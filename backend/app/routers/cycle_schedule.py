"""Per-project cycle schedule: phases + work items linked to real tasks."""

from __future__ import annotations

import uuid
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.membership import require_team_membership
from app.models import Notification, PhaseWorkItem, Project, ProjectPhase, Task, TeamMember, User
from app.notifications import notify_team_members
from app.schemas import (
    DEFAULT_PHASE_NAMES,
    PHASE_WORK_ITEM_STATUSES,
    REQUIREMENT_CYCLE_PHASE_NAMES,
    DailyPlanAssignment,
    DailyPlanDay,
    DailyPlanResponse,
    ExpandDailyScheduleRequest,
    GenerateCycleScheduleRequest,
    ImportTasksRequest,
    PhaseWorkItemCreateRequest,
    PhaseWorkItemResponse,
    PhaseWorkItemUpdateRequest,
    ProjectCycleScheduleResponse,
    ProjectPhaseCreateRequest,
    ProjectPhaseResponse,
    ProjectPhaseUpdateRequest,
)

router = APIRouter(
    prefix="/teams/{team_id}/projects/{project_id}/cycle-schedule",
    tags=["cycle-schedule"],
)


def _require_project(
    db: Session, *, team_id: uuid.UUID, project_id: uuid.UUID
) -> Project:
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.team_id == team_id)
        .one_or_none()
    )
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def _validate_dates(start: date | None, end: date | None) -> None:
    if start and end and end < start:
        raise HTTPException(
            status_code=400,
            detail="planned_end cannot be earlier than planned_start",
        )


def _validate_assignee(
    db: Session,
    *,
    team_id: uuid.UUID,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    from app.project_members import require_project_assignee

    require_project_assignee(
        db, team_id=team_id, project_id=project_id, user_id=user_id
    )


def _get_phase(
    db: Session, *, team_id: uuid.UUID, project_id: uuid.UUID, phase_id: uuid.UUID
) -> ProjectPhase:
    phase = (
        db.query(ProjectPhase)
        .filter(
            ProjectPhase.id == phase_id,
            ProjectPhase.project_id == project_id,
            ProjectPhase.team_id == team_id,
        )
        .one_or_none()
    )
    if phase is None:
        raise HTTPException(status_code=404, detail="Phase not found")
    return phase


def _get_work_item(
    db: Session, *, team_id: uuid.UUID, project_id: uuid.UUID, item_id: uuid.UUID
) -> PhaseWorkItem:
    item = (
        db.query(PhaseWorkItem)
        .filter(
            PhaseWorkItem.id == item_id,
            PhaseWorkItem.project_id == project_id,
            PhaseWorkItem.team_id == team_id,
        )
        .one_or_none()
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Work item not found")
    return item


def _work_item_to_response(item: PhaseWorkItem) -> PhaseWorkItemResponse:
    return PhaseWorkItemResponse(
        id=item.id,
        team_id=item.team_id,
        project_id=item.project_id,
        phase_id=item.phase_id,
        title=item.title,
        assignee_user_id=item.assignee_user_id,
        planned_start=item.planned_start,
        planned_end=item.planned_end,
        estimated_hours=float(item.estimated_hours or 0),
        status=item.status,
        sort_order=item.sort_order,
        task_id=item.task_id,
        created_at=item.created_at,
    )


def _phase_to_response(
    phase: ProjectPhase, items: list[PhaseWorkItem]
) -> ProjectPhaseResponse:
    return ProjectPhaseResponse(
        id=phase.id,
        team_id=phase.team_id,
        project_id=phase.project_id,
        name=phase.name,
        sort_order=phase.sort_order,
        planned_start=phase.planned_start,
        planned_end=phase.planned_end,
        work_items=[_work_item_to_response(i) for i in items],
        created_at=phase.created_at,
    )


def _build_schedule_response(
    db: Session, project: Project
) -> ProjectCycleScheduleResponse:
    phases = (
        db.query(ProjectPhase)
        .filter(ProjectPhase.project_id == project.id)
        .order_by(ProjectPhase.sort_order.asc(), ProjectPhase.created_at.asc())
        .all()
    )
    items = (
        db.query(PhaseWorkItem)
        .filter(PhaseWorkItem.project_id == project.id)
        .order_by(PhaseWorkItem.sort_order.asc(), PhaseWorkItem.created_at.asc())
        .all()
    )
    items_by_phase: dict[uuid.UUID, list[PhaseWorkItem]] = {}
    total_hours = 0.0
    linked = 0
    for item in items:
        items_by_phase.setdefault(item.phase_id, []).append(item)
        total_hours += float(item.estimated_hours or 0)
        if item.task_id is not None:
            linked += 1

    phase_payloads = [
        _phase_to_response(phase, items_by_phase.get(phase.id, [])) for phase in phases
    ]
    return ProjectCycleScheduleResponse(
        project_id=project.id,
        team_id=project.team_id,
        project_name=project.name,
        planned_start=project.planned_start,
        planned_end=project.planned_end,
        member_daily_hours=float(project.member_daily_hours or 6.0),
        owner_user_id=project.owner_user_id,
        plan_confirmed=bool(project.plan_confirmed),
        total_estimated_hours=round(total_hours, 1),
        phase_count=len(phase_payloads),
        work_item_count=len(items),
        linked_task_count=linked,
        phases=phase_payloads,
    )


def _split_range(start: date, end: date, count: int) -> list[tuple[date, date]]:
    """Split inclusive date range into `count` contiguous segments."""
    total_days = (end - start).days + 1
    if total_days < count:
        segments = []
        for i in range(count):
            day = start + timedelta(days=min(i, total_days - 1))
            segments.append((day, day))
        return segments

    base = total_days // count
    rem = total_days % count
    segments: list[tuple[date, date]] = []
    cursor = start
    for i in range(count):
        length = base + (1 if i < rem else 0)
        seg_end = cursor + timedelta(days=length - 1)
        segments.append((cursor, seg_end))
        cursor = seg_end + timedelta(days=1)
    return segments


def _estimate_hours(
    start: date | None, end: date | None, daily_hours: float
) -> float:
    if not start or not end:
        return round(daily_hours * 0.4, 1)
    days = (end - start).days + 1
    return round(max(days, 1) * daily_hours * 0.4, 1)


def _parse_requirements(text: str | None) -> list[str]:
    """Split free-text requirements into concrete items (one per line / bullet)."""
    if not text:
        return []
    items: list[str] = []
    for raw in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw.strip()
        if not line:
            continue
        # Strip common bullet / numbering prefixes: -, *, •, 1., 1)、（1）
        cleaned = line
        for prefix in ("- ", "* ", "• ", "· ", "－ ", "— "):
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix) :].strip()
                break
        while cleaned and cleaned[0].isdigit():
            cleaned = cleaned[1:].lstrip(" .、)）:：-")
        if cleaned.startswith(("（", "(")) and len(cleaned) > 2:
            # "(1) xxx" / "（1）xxx"
            for closer in ("）", ")"):
                idx = cleaned.find(closer)
                if 0 < idx <= 4:
                    cleaned = cleaned[idx + 1 :].strip()
                    break
        cleaned = cleaned.strip(" ；;。.")
        if cleaned and cleaned not in items:
            items.append(cleaned[:200])
    return items[:40]


def _resolve_phase_names(
    opts: GenerateCycleScheduleRequest,
    *,
    seed_mode: str,
    available_jobs: list[str] | None = None,
) -> list[str]:
    if opts.phase_names:
        names = [n.strip() for n in opts.phase_names if n and n.strip()]
        if names:
            return names
    if seed_mode == "from_requirements":
        pipeline = _pipeline_steps_for_jobs(available_jobs or [])
        # Unique phase names in pipeline order
        names: list[str] = []
        for phase_name, _prefix, _job in pipeline:
            if phase_name not in names:
                names.append(phase_name)
        return names or ["目标与需求", "推进落地", "交付复盘"]
    count = opts.phase_count
    names = list(DEFAULT_PHASE_NAMES[:count])
    while len(names) < count:
        names.append(f"阶段 {len(names) + 1}")
    return names


def _hours_for_phase_item(
    phase: ProjectPhase, daily: float, *, weight: float = 0.35
) -> float:
    return round(
        max(_estimate_hours(phase.planned_start, phase.planned_end, daily) * weight, 0.5),
        1,
    )


def _add_work_item(
    db: Session,
    *,
    team_id: uuid.UUID,
    project: Project,
    phase: ProjectPhase,
    title: str,
    assignee_user_id: uuid.UUID | None,
    sort_order: int,
    estimated_hours: float,
    create_task: bool,
    created_by_user_id: uuid.UUID,
) -> PhaseWorkItem:
    task_id = None
    if create_task:
        max_order = (
            db.query(Task.sort_order)
            .filter(Task.project_id == project.id)
            .order_by(Task.sort_order.desc())
            .first()
        )
        task = Task(
            team_id=team_id,
            project_id=project.id,
            title=title,
            status="todo",
            assignee_user_id=assignee_user_id,
            due_date=phase.planned_end,
            sort_order=(max_order[0] + 1) if max_order else 0,
            created_by_user_id=created_by_user_id,
        )
        db.add(task)
        db.flush()
        task_id = task.id

    item = PhaseWorkItem(
        team_id=team_id,
        project_id=project.id,
        phase_id=phase.id,
        task_id=task_id,
        title=title,
        assignee_user_id=assignee_user_id,
        planned_start=phase.planned_start,
        planned_end=phase.planned_end,
        estimated_hours=estimated_hours,
        status="todo",
        sort_order=sort_order,
    )
    db.add(item)
    return item


JOB_TITLE_LABELS_ZH = {
    "project_manager": "项目经理",
    "pm": "产品经理",
    "designer": "设计师",
    "frontend": "前端工程师",
    "backend": "后端工程师",
    "fullstack": "全栈工程师",
    "qa": "测试工程师",
    "ops": "运营",
    "other": "其他",
}


def _team_job_titles(db: Session, *, team_id: uuid.UUID) -> list[str]:
    """Ordered unique job titles currently set on the team (may be empty)."""
    rows = (
        db.query(TeamMember.job_title)
        .filter(TeamMember.team_id == team_id, TeamMember.job_title.is_not(None))
        .order_by(TeamMember.created_at.asc())
        .all()
    )
    seen: list[str] = []
    for (job,) in rows:
        j = (job or "").strip().lower()
        if j and j not in seen:
            seen.append(j)
    return seen


def _project_job_titles(
    db: Session, *, team_id: uuid.UUID, project_id: uuid.UUID
) -> list[str]:
    """Prefer project-member jobs; fall back to team jobs."""
    from app.project_members import list_project_job_titles

    jobs = list_project_job_titles(db, project_id=project_id)
    return jobs or _team_job_titles(db, team_id=team_id)


def _pipeline_steps_for_jobs(jobs: list[str]) -> list[tuple[str, str, str | None]]:
    """Build (phase_name, title_prefix, target_job) from jobs that actually exist.

    Not every team has design/frontend/backend — only include steps the roster can cover.
    """
    job_set = set(jobs)
    steps: list[tuple[str, str, str | None]] = []

    def pick(*candidates: str) -> str | None:
        for c in candidates:
            if c in job_set:
                return c
        return jobs[0] if jobs else None

    # 1) Goals / requirements — prefer pm / project_manager
    steps.append(
        (
            "目标与需求",
            "澄清目标",
            pick(
                "pm",
                "project_manager",
                "fullstack",
                "frontend",
                "backend",
                "ops",
                "qa",
                "designer",
            ),
        )
    )

    # 2) Design — only if designer exists
    if "designer" in job_set:
        steps.append(("方案设计", "设计方案", "designer"))

    # 3) Build — only for engineering roles that exist
    eng = [j for j in ("fullstack", "frontend", "backend") if j in job_set]
    if len(eng) == 1:
        label = JOB_TITLE_LABELS_ZH.get(eng[0], eng[0])
        steps.append(("开发实现", f"{label}实现", eng[0]))
    elif len(eng) > 1:
        for j in eng:
            label = JOB_TITLE_LABELS_ZH.get(j, j)
            steps.append(("开发实现", f"{label}实现", j))
    elif job_set:
        owner_job = pick("ops", "pm", "qa", "designer")
        label = JOB_TITLE_LABELS_ZH.get(owner_job or "", "执行")
        steps.append(("推进落地", f"{label}推进", owner_job))
    else:
        # No job titles configured — keep a generic execution step for goals
        steps.append(("推进落地", "推进落地", None))

    # 4) QA — only if qa exists
    if "qa" in job_set:
        steps.append(("验收测试", "验收确认", "qa"))

    # 5) Delivery
    deliver = pick("ops", "pm", "fullstack", "backend", "frontend", "qa", "designer")
    steps.append(("交付复盘", "交付收尾", deliver))
    return steps


def _seed_from_requirements(
    db: Session,
    *,
    team_id: uuid.UUID,
    project: Project,
    phases: list[ProjectPhase],
    requirements: list[str],
    daily: float,
    default_assignee: uuid.UUID,
    create_tasks: bool,
    created_by_user_id: uuid.UUID,
    available_jobs: list[str] | None = None,
) -> int:
    """Build plan from requirements using only steps that match real team jobs."""
    jobs = available_jobs if available_jobs is not None else _team_job_titles(db, team_id=team_id)
    pipeline = _pipeline_steps_for_jobs(jobs)

    # Map phase_name -> ProjectPhase (phases already created to match pipeline names)
    by_name = {p.name: p for p in phases}
    created = 0

    # Kickoff always on first phase
    first_phase = phases[0]
    planner = pipeline[0][2] if pipeline else None
    kickoff = [
        ("确认项目目标与成功标准", planner),
        ("对齐干系人与沟通节奏", planner),
    ]
    if project.objective:
        kickoff.insert(0, (f"对齐总体目标：{project.objective.strip()[:80]}", planner))
    for index, (title, _job) in enumerate(kickoff):
        _add_work_item(
            db,
            team_id=team_id,
            project=project,
            phase=first_phase,
            title=title[:200],
            assignee_user_id=default_assignee,
            sort_order=1000 + index,
            estimated_hours=_hours_for_phase_item(first_phase, daily, weight=0.2),
            create_task=create_tasks,
            created_by_user_id=created_by_user_id,
        )
        created += 1

    for req_index, req in enumerate(requirements):
        for phase_name, prefix, _target_job in pipeline:
            phase = by_name.get(phase_name) or first_phase
            weight = 0.45 if "实现" in prefix or "推进" in prefix else 0.28
            _add_work_item(
                db,
                team_id=team_id,
                project=project,
                phase=phase,
                title=f"{prefix}：{req}"[:200],
                assignee_user_id=default_assignee,
                sort_order=req_index,
                estimated_hours=_hours_for_phase_item(phase, daily, weight=weight),
                create_task=create_tasks,
                created_by_user_id=created_by_user_id,
            )
            created += 1

    last_phase = phases[-1]
    delivery_titles = [
        f"交付核对：{'、'.join(requirements[:3])}" + ("…" if len(requirements) > 3 else ""),
        "周期复盘与遗留项归档",
    ]
    for index, title in enumerate(delivery_titles):
        _add_work_item(
            db,
            team_id=team_id,
            project=project,
            phase=last_phase,
            title=title[:200],
            assignee_user_id=default_assignee,
            sort_order=2000 + index,
            estimated_hours=_hours_for_phase_item(last_phase, daily, weight=0.25),
            create_task=create_tasks,
            created_by_user_id=created_by_user_id,
        )
        created += 1

    db.flush()
    return created


def _clear_schedule(db: Session, project_id: uuid.UUID) -> None:
    db.query(PhaseWorkItem).filter(PhaseWorkItem.project_id == project_id).delete()
    db.query(ProjectPhase).filter(ProjectPhase.project_id == project_id).delete()
    db.flush()


def _sync_linked_task(db: Session, item: PhaseWorkItem) -> None:
    if item.task_id is None:
        return
    task = db.query(Task).filter(Task.id == item.task_id).one_or_none()
    if task is None:
        item.task_id = None
        return
    task.title = item.title
    task.status = item.status if item.status in PHASE_WORK_ITEM_STATUSES else task.status
    task.assignee_user_id = item.assignee_user_id
    if item.planned_end is not None:
        task.due_date = item.planned_end


@router.get("", response_model=ProjectCycleScheduleResponse)
def get_cycle_schedule(
    team_id: uuid.UUID,
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectCycleScheduleResponse:
    require_team_membership(db, team_id=team_id, user=current_user)
    project = _require_project(db, team_id=team_id, project_id=project_id)
    return _build_schedule_response(db, project)


@router.post(
    "/generate",
    response_model=ProjectCycleScheduleResponse,
    status_code=status.HTTP_201_CREATED,
)
def generate_cycle_schedule(
    team_id: uuid.UUID,
    project_id: uuid.UUID,
    body: GenerateCycleScheduleRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectCycleScheduleResponse:
    """Create a full-cycle schedule from requirements (or legacy seed modes)."""
    require_team_membership(db, team_id=team_id, user=current_user)
    project = _require_project(db, team_id=team_id, project_id=project_id)

    opts = body or GenerateCycleScheduleRequest()
    if not project.planned_start or not project.planned_end:
        raise HTTPException(
            status_code=400,
            detail="Set project planned_start and planned_end before generating schedule",
        )
    _validate_dates(project.planned_start, project.planned_end)

    seed_mode = (opts.seed_mode or "from_requirements").strip().lower()
    if seed_mode not in {
        "from_requirements",
        "from_tasks",
        "phases_only",
        "placeholders",
    }:
        raise HTTPException(
            status_code=400,
            detail=(
                "seed_mode must be from_requirements, from_tasks, "
                "phases_only, or placeholders"
            ),
        )

    requirements: list[str] = []
    available_jobs: list[str] = []
    if seed_mode == "from_requirements":
        requirements = _parse_requirements(opts.requirements_text)
        if not requirements:
            requirements = _parse_requirements(project.objective)
        if not requirements:
            raise HTTPException(
                status_code=400,
                detail=(
                    "请先填写需求（每行一条），或在项目设置里写好目标说明，"
                    "再生成全周期排期。"
                ),
            )
        if opts.save_requirements_to_project and opts.requirements_text:
            cleaned = opts.requirements_text.strip()
            if cleaned:
                project.objective = cleaned[:4000]
        available_jobs = _project_job_titles(
            db, team_id=team_id, project_id=project.id
        )

    existing = (
        db.query(ProjectPhase.id)
        .filter(ProjectPhase.project_id == project.id)
        .first()
    )
    if existing and not opts.replace_existing:
        raise HTTPException(
            status_code=400,
            detail="Schedule already exists. Pass replace_existing=true to regenerate.",
        )

    if existing and opts.replace_existing:
        _clear_schedule(db, project.id)

    names = _resolve_phase_names(
        opts, seed_mode=seed_mode, available_jobs=available_jobs
    )
    count = len(names)
    segments = _split_range(project.planned_start, project.planned_end, count)
    daily = float(project.member_daily_hours or 6.0)
    default_assignee = project.owner_user_id or current_user.id

    phases: list[ProjectPhase] = []
    for idx, ((seg_start, seg_end), name) in enumerate(zip(segments, names)):
        phase = ProjectPhase(
            team_id=team_id,
            project_id=project.id,
            name=name,
            sort_order=idx,
            planned_start=seg_start,
            planned_end=seg_end,
        )
        db.add(phase)
        db.flush()
        phases.append(phase)

        if seed_mode == "placeholders":
            hours = _estimate_hours(seg_start, seg_end, daily)
            db.add(
                PhaseWorkItem(
                    team_id=team_id,
                    project_id=project.id,
                    phase_id=phase.id,
                    title=f"{name} · 关键工作",
                    assignee_user_id=default_assignee,
                    planned_start=seg_start,
                    planned_end=seg_end,
                    estimated_hours=hours,
                    status="todo",
                    sort_order=0,
                )
            )

    work_item_hint = ""
    if seed_mode == "from_requirements":
        created_count = _seed_from_requirements(
            db,
            team_id=team_id,
            project=project,
            phases=phases,
            requirements=requirements,
            daily=daily,
            default_assignee=default_assignee,
            create_tasks=bool(opts.create_tasks),
            created_by_user_id=current_user.id,
            available_jobs=available_jobs,
        )
        job_hint = "、".join(available_jobs) if available_jobs else "未设岗位(按成员均分)"
        work_item_hint = (
            f"，{created_count} 个工作项（{len(requirements)} 条需求 · 岗位：{job_hint}）"
        )
    elif seed_mode == "from_tasks":
        tasks = (
            db.query(Task)
            .filter(Task.project_id == project.id)
            .order_by(Task.sort_order.asc(), Task.created_at.asc())
            .all()
        )
        for index, task in enumerate(tasks):
            phase = phases[index % len(phases)]
            db.add(
                PhaseWorkItem(
                    team_id=team_id,
                    project_id=project.id,
                    phase_id=phase.id,
                    task_id=task.id,
                    title=task.title,
                    assignee_user_id=task.assignee_user_id or default_assignee,
                    planned_start=phase.planned_start,
                    planned_end=task.due_date or phase.planned_end,
                    estimated_hours=0.0,
                    status=task.status if task.status in PHASE_WORK_ITEM_STATUSES else "todo",
                    sort_order=index,
                )
            )

    project.plan_confirmed = False
    notify_team_members(
        db,
        team_id=team_id,
        project_id=project.id,
        type="cycle_schedule_generated",
        category="周期",
        title="全局周期排期已生成",
        body=f"「{project.name}」已生成 {count} 个阶段（模式：{seed_mode}）{work_item_hint}。",
        link_path=f"/teams/{team_id}/projects/{project.id}/schedule",
        exclude_user_id=current_user.id,
    )
    db.commit()
    db.refresh(project)
    return _build_schedule_response(db, project)


@router.post("/phases", response_model=ProjectPhaseResponse, status_code=status.HTTP_201_CREATED)
def create_phase(
    team_id: uuid.UUID,
    project_id: uuid.UUID,
    body: ProjectPhaseCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectPhaseResponse:
    require_team_membership(db, team_id=team_id, user=current_user)
    project = _require_project(db, team_id=team_id, project_id=project_id)
    _validate_dates(body.planned_start, body.planned_end)

    max_order = (
        db.query(ProjectPhase.sort_order)
        .filter(ProjectPhase.project_id == project.id)
        .order_by(ProjectPhase.sort_order.desc())
        .first()
    )
    sort_order = body.sort_order if body.sort_order is not None else (
        (max_order[0] + 1) if max_order else 0
    )

    phase = ProjectPhase(
        team_id=team_id,
        project_id=project.id,
        name=body.name.strip(),
        sort_order=sort_order,
        planned_start=body.planned_start,
        planned_end=body.planned_end,
    )
    db.add(phase)
    project.plan_confirmed = False
    db.commit()
    db.refresh(phase)
    return _phase_to_response(phase, [])


@router.patch("/phases/{phase_id}", response_model=ProjectPhaseResponse)
def update_phase(
    team_id: uuid.UUID,
    project_id: uuid.UUID,
    phase_id: uuid.UUID,
    body: ProjectPhaseUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectPhaseResponse:
    require_team_membership(db, team_id=team_id, user=current_user)
    project = _require_project(db, team_id=team_id, project_id=project_id)
    phase = _get_phase(db, team_id=team_id, project_id=project_id, phase_id=phase_id)

    if body.name is not None:
        name = body.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="Phase name cannot be empty")
        phase.name = name

    if body.clear_dates:
        phase.planned_start = None
        phase.planned_end = None
    else:
        if body.planned_start is not None:
            phase.planned_start = body.planned_start
        if body.planned_end is not None:
            phase.planned_end = body.planned_end
        _validate_dates(phase.planned_start, phase.planned_end)

    project.plan_confirmed = False
    db.commit()
    db.refresh(phase)
    items = (
        db.query(PhaseWorkItem)
        .filter(PhaseWorkItem.phase_id == phase.id)
        .order_by(PhaseWorkItem.sort_order.asc())
        .all()
    )
    return _phase_to_response(phase, items)


@router.delete("/phases/{phase_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_phase(
    team_id: uuid.UUID,
    project_id: uuid.UUID,
    phase_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    require_team_membership(db, team_id=team_id, user=current_user)
    project = _require_project(db, team_id=team_id, project_id=project_id)
    phase = _get_phase(db, team_id=team_id, project_id=project_id, phase_id=phase_id)
    db.query(PhaseWorkItem).filter(PhaseWorkItem.phase_id == phase.id).delete()
    db.delete(phase)
    project.plan_confirmed = False
    db.commit()


@router.post(
    "/phases/{phase_id}/work-items",
    response_model=PhaseWorkItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_work_item(
    team_id: uuid.UUID,
    project_id: uuid.UUID,
    phase_id: uuid.UUID,
    body: PhaseWorkItemCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PhaseWorkItemResponse:
    require_team_membership(db, team_id=team_id, user=current_user)
    project = _require_project(db, team_id=team_id, project_id=project_id)
    phase = _get_phase(db, team_id=team_id, project_id=project_id, phase_id=phase_id)
    _validate_dates(body.planned_start, body.planned_end)

    status_value = body.status.strip().lower()
    if status_value not in PHASE_WORK_ITEM_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Use one of: {', '.join(PHASE_WORK_ITEM_STATUSES)}",
        )

    assignee = body.assignee_user_id
    if assignee is not None:
        _validate_assignee(
            db, team_id=team_id, project_id=project_id, user_id=assignee
        )

    task_id = body.task_id
    if task_id is not None:
        task = (
            db.query(Task)
            .filter(
                Task.id == task_id,
                Task.project_id == project.id,
                Task.team_id == team_id,
            )
            .one_or_none()
        )
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")

    max_order = (
        db.query(PhaseWorkItem.sort_order)
        .filter(PhaseWorkItem.phase_id == phase.id)
        .order_by(PhaseWorkItem.sort_order.desc())
        .first()
    )
    sort_order = (max_order[0] + 1) if max_order else 0

    item = PhaseWorkItem(
        team_id=team_id,
        project_id=project.id,
        phase_id=phase.id,
        task_id=task_id,
        title=body.title.strip(),
        assignee_user_id=assignee,
        planned_start=body.planned_start or phase.planned_start,
        planned_end=body.planned_end or phase.planned_end,
        estimated_hours=body.estimated_hours,
        status=status_value,
        sort_order=sort_order,
    )
    db.add(item)
    project.plan_confirmed = False
    db.commit()
    db.refresh(item)
    return _work_item_to_response(item)


@router.patch("/work-items/{item_id}", response_model=PhaseWorkItemResponse)
def update_work_item(
    team_id: uuid.UUID,
    project_id: uuid.UUID,
    item_id: uuid.UUID,
    body: PhaseWorkItemUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PhaseWorkItemResponse:
    require_team_membership(db, team_id=team_id, user=current_user)
    project = _require_project(db, team_id=team_id, project_id=project_id)
    item = _get_work_item(db, team_id=team_id, project_id=project_id, item_id=item_id)

    if body.title is not None:
        title = body.title.strip()
        if not title:
            raise HTTPException(status_code=400, detail="Title cannot be empty")
        item.title = title

    if body.clear_assignee:
        item.assignee_user_id = None
    elif body.assignee_user_id is not None:
        _validate_assignee(
            db,
            team_id=team_id,
            project_id=project_id,
            user_id=body.assignee_user_id,
        )
        item.assignee_user_id = body.assignee_user_id

    if body.clear_dates:
        item.planned_start = None
        item.planned_end = None
    else:
        if body.planned_start is not None:
            item.planned_start = body.planned_start
        if body.planned_end is not None:
            item.planned_end = body.planned_end
        _validate_dates(item.planned_start, item.planned_end)

    if body.estimated_hours is not None:
        item.estimated_hours = body.estimated_hours

    if body.status is not None:
        status_value = body.status.strip().lower()
        if status_value not in PHASE_WORK_ITEM_STATUSES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Use one of: {', '.join(PHASE_WORK_ITEM_STATUSES)}",
            )
        item.status = status_value

    _sync_linked_task(db, item)
    project.plan_confirmed = False
    db.commit()
    db.refresh(item)
    return _work_item_to_response(item)


@router.delete("/work-items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_work_item(
    team_id: uuid.UUID,
    project_id: uuid.UUID,
    item_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    require_team_membership(db, team_id=team_id, user=current_user)
    project = _require_project(db, team_id=team_id, project_id=project_id)
    item = _get_work_item(db, team_id=team_id, project_id=project_id, item_id=item_id)
    db.delete(item)
    project.plan_confirmed = False
    db.commit()


@router.post(
    "/work-items/{item_id}/sync-task",
    response_model=PhaseWorkItemResponse,
)
def sync_work_item_to_task(
    team_id: uuid.UUID,
    project_id: uuid.UUID,
    item_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PhaseWorkItemResponse:
    """Create a real Task from this work item, or refresh the linked task."""
    require_team_membership(db, team_id=team_id, user=current_user)
    project = _require_project(db, team_id=team_id, project_id=project_id)
    item = _get_work_item(db, team_id=team_id, project_id=project_id, item_id=item_id)

    if item.task_id is not None:
        _sync_linked_task(db, item)
        db.commit()
        db.refresh(item)
        return _work_item_to_response(item)

    max_order = (
        db.query(Task.sort_order)
        .filter(Task.project_id == project.id)
        .order_by(Task.sort_order.desc())
        .first()
    )
    task = Task(
        team_id=team_id,
        project_id=project.id,
        title=item.title,
        status=item.status if item.status in PHASE_WORK_ITEM_STATUSES else "todo",
        assignee_user_id=item.assignee_user_id,
        due_date=item.planned_end,
        sort_order=(max_order[0] + 1) if max_order else 0,
        created_by_user_id=current_user.id,
    )
    db.add(task)
    db.flush()
    item.task_id = task.id
    project.plan_confirmed = False

    if item.assignee_user_id and item.assignee_user_id != current_user.id:
        db.add(
            Notification(
                user_id=item.assignee_user_id,
                team_id=team_id,
                project_id=project.id,
                type="task_assigned",
                category="任务",
                title=f"新任务：{task.title}",
                body=f"从排期同步创建了任务「{task.title}」并指派给你。",
                link_path=f"/teams/{team_id}/projects/{project.id}/daily",
            )
        )

    db.commit()
    db.refresh(item)
    return _work_item_to_response(item)


@router.post("/import-tasks", response_model=ProjectCycleScheduleResponse)
def import_tasks_into_schedule(
    team_id: uuid.UUID,
    project_id: uuid.UUID,
    body: ImportTasksRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectCycleScheduleResponse:
    require_team_membership(db, team_id=team_id, user=current_user)
    project = _require_project(db, team_id=team_id, project_id=project_id)
    phase = _get_phase(
        db, team_id=team_id, project_id=project_id, phase_id=body.phase_id
    )

    already_linked = {
        row[0]
        for row in db.query(PhaseWorkItem.task_id)
        .filter(
            PhaseWorkItem.project_id == project.id,
            PhaseWorkItem.task_id.isnot(None),
        )
        .all()
        if row[0] is not None
    }

    query = db.query(Task).filter(Task.project_id == project.id, Task.team_id == team_id)
    if body.task_ids:
        query = query.filter(Task.id.in_(body.task_ids))
    tasks = query.order_by(Task.sort_order.asc(), Task.created_at.asc()).all()
    if body.task_ids and len(tasks) != len(set(body.task_ids)):
        raise HTTPException(status_code=404, detail="Some tasks not found")

    max_order = (
        db.query(PhaseWorkItem.sort_order)
        .filter(PhaseWorkItem.phase_id == phase.id)
        .order_by(PhaseWorkItem.sort_order.desc())
        .first()
    )
    next_order = (max_order[0] + 1) if max_order else 0
    imported = 0
    for task in tasks:
        if body.only_unlinked and task.id in already_linked:
            continue
        if task.id in already_linked and not body.only_unlinked:
            # already on schedule elsewhere — skip to avoid duplicate links
            continue
        db.add(
            PhaseWorkItem(
                team_id=team_id,
                project_id=project.id,
                phase_id=phase.id,
                task_id=task.id,
                title=task.title,
                assignee_user_id=task.assignee_user_id,
                planned_start=phase.planned_start,
                planned_end=task.due_date or phase.planned_end,
                estimated_hours=0.0,
                status=task.status if task.status in PHASE_WORK_ITEM_STATUSES else "todo",
                sort_order=next_order,
            )
        )
        next_order += 1
        imported += 1

    if imported:
        project.plan_confirmed = False
    db.commit()
    db.refresh(project)
    return _build_schedule_response(db, project)


@router.post("/expand-daily", response_model=DailyPlanResponse)
def expand_cycle_schedule_to_daily(
    team_id: uuid.UUID,
    project_id: uuid.UUID,
    body: ExpandDailyScheduleRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DailyPlanResponse:
    """Pack each phase's work items onto concrete days within that phase window.

    Updates Task.due_date so 「每日任务」 shows the day-by-day plan.
    """
    require_team_membership(db, team_id=team_id, user=current_user)
    project = _require_project(db, team_id=team_id, project_id=project_id)
    opts = body or ExpandDailyScheduleRequest()

    phases = (
        db.query(ProjectPhase)
        .filter(ProjectPhase.project_id == project.id)
        .order_by(ProjectPhase.sort_order.asc(), ProjectPhase.created_at.asc())
        .all()
    )
    if not phases:
        raise HTTPException(
            status_code=400,
            detail="请先生成全周期排期，再展开为每日工作安排。",
        )

    daily_cap = float(project.member_daily_hours or 6.0)
    default_assignee = project.owner_user_id or current_user.id
    created_tasks = 0
    updated_tasks = 0
    assigned = 0

    job_pools = _load_job_pools(db, team_id=team_id) if opts.assign_by_job else {}
    all_member_ids = [
        row[0]
        for row in db.query(TeamMember.user_id)
        .filter(TeamMember.team_id == team_id)
        .order_by(TeamMember.created_at.asc())
        .all()
    ]
    # job_title lookup by user
    job_by_user = {
        m.user_id: (m.job_title or None)
        for m in db.query(TeamMember).filter(TeamMember.team_id == team_id).all()
    }
    person_day_load: dict[tuple[uuid.UUID, date], float] = {}

    # day -> list of assignment dicts for response
    day_map: dict[date, list[dict]] = {}

    for phase in phases:
        items = (
            db.query(PhaseWorkItem)
            .filter(PhaseWorkItem.phase_id == phase.id)
            .order_by(PhaseWorkItem.sort_order.asc(), PhaseWorkItem.created_at.asc())
            .all()
        )
        if not items:
            continue

        window_start = phase.planned_start or project.planned_start
        window_end = phase.planned_end or project.planned_end
        if window_start is None or window_end is None:
            raise HTTPException(
                status_code=400,
                detail=f"阶段「{phase.name}」缺少日期，无法展开每日排期。",
            )
        if window_end < window_start:
            window_start, window_end = window_end, window_start

        days = _iter_days(window_start, window_end, weekdays_only=opts.weekdays_only)
        if not days:
            days = _iter_days(window_start, window_end, weekdays_only=False)
        if not days:
            continue

        # Remaining capacity per day (shared across phases if dates overlap)
        for d in days:
            day_map.setdefault(d, [])

        loads: dict[date, float] = {
            d: sum(float(a["planned_hours"]) for a in day_map[d]) for d in days
        }

        for item in items:
            hours = float(item.estimated_hours or 0)
            if hours <= 0:
                hours = round(max(daily_cap * 0.35, 0.5), 1)

            preferred_job = _infer_job_from_title(item.title)

            item_days = days
            if item.planned_start and item.planned_end:
                narrowed = [
                    d for d in days if item.planned_start <= d <= item.planned_end
                ]
                if narrowed:
                    item_days = narrowed
            ordered = sorted(item_days)

            # Pack into day chunks respecting daily capacity when possible.
            remaining = hours
            chunks: list[tuple[date, float]] = []
            safety = 0
            while remaining > 1e-6 and safety < 40:
                safety += 1
                day = min(ordered, key=lambda d: (loads.get(d, 0.0), d.toordinal()))
                room = daily_cap - loads.get(day, 0.0)
                if room >= 0.25:
                    take = min(remaining, room)
                else:
                    take = remaining
                take = round(take, 1)
                if take <= 0:
                    take = remaining
                chunks.append((day, take))
                loads[day] = loads.get(day, 0.0) + take
                remaining = round(remaining - take, 1)

            primary_day = chunks[0][0]
            last_day = chunks[-1][0]
            if opts.pin_work_item_dates:
                item.planned_start = primary_day
                item.planned_end = last_day

            matched_job: str | None = None
            if opts.assign_by_job:
                assignee, matched_job = _pick_assignee_for_job(
                    preferred_job=preferred_job,
                    pools=job_pools,
                    person_day_load=person_day_load,
                    day=primary_day,
                    default_assignee=default_assignee,
                    all_member_ids=all_member_ids,
                )
                item.assignee_user_id = assignee
            else:
                assignee = item.assignee_user_id or default_assignee

            for chunk_index, (day, chunk_hours) in enumerate(chunks):
                title = (
                    item.title
                    if len(chunks) == 1
                    else f"{item.title}（{day.isoformat()}）"
                )
                # Re-pick by person capacity on this specific day when assigning by job
                chunk_assignee = assignee
                chunk_matched = matched_job
                if opts.assign_by_job:
                    chunk_assignee, chunk_matched = _pick_assignee_for_job(
                        preferred_job=preferred_job,
                        pools=job_pools,
                        person_day_load=person_day_load,
                        day=day,
                        default_assignee=default_assignee,
                        all_member_ids=all_member_ids,
                    )
                    if chunk_index == 0:
                        item.assignee_user_id = chunk_assignee
                person_day_load[(chunk_assignee, day)] = (
                    person_day_load.get((chunk_assignee, day), 0.0) + chunk_hours
                )

                task_id = None
                if chunk_index == 0 and item.task_id is not None:
                    task = db.query(Task).filter(Task.id == item.task_id).one_or_none()
                    if task is not None:
                        task.due_date = day
                        task.title = item.title
                        task.assignee_user_id = chunk_assignee
                        task_id = task.id
                        updated_tasks += 1
                    else:
                        item.task_id = None

                if task_id is None and opts.create_tasks:
                    max_order = (
                        db.query(Task.sort_order)
                        .filter(Task.project_id == project.id)
                        .order_by(Task.sort_order.desc())
                        .first()
                    )
                    task = Task(
                        team_id=team_id,
                        project_id=project.id,
                        title=title[:200],
                        status=item.status
                        if item.status in PHASE_WORK_ITEM_STATUSES
                        else "todo",
                        assignee_user_id=chunk_assignee,
                        due_date=day,
                        sort_order=(max_order[0] + 1) if max_order else 0,
                        created_by_user_id=current_user.id,
                    )
                    db.add(task)
                    db.flush()
                    task_id = task.id
                    created_tasks += 1
                    if chunk_index == 0:
                        item.task_id = task_id

                day_map.setdefault(day, []).append(
                    {
                        "work_item_id": item.id,
                        "task_id": task_id,
                        "phase_id": phase.id,
                        "phase_name": phase.name,
                        "title": title[:200],
                        "assignee_user_id": chunk_assignee,
                        "assignee_job_title": job_by_user.get(chunk_assignee),
                        "planned_hours": chunk_hours,
                        "status": item.status,
                        "matched_job": chunk_matched or preferred_job,
                    }
                )
            assigned += 1

    if opts.mark_confirmed:
        project.plan_confirmed = True
    else:
        # Expanding daily detail usually means plan is still adjustable
        project.plan_confirmed = False

    notify_team_members(
        db,
        team_id=team_id,
        project_id=project.id,
        type="cycle_schedule_expanded_daily",
        category="周期",
        title="已展开每日工作排期",
        body=(
            f"「{project.name}」已按阶段日期"
            f"{'与岗位' if opts.assign_by_job else ''}"
            f"展开每日任务（{assigned} 项 → {created_tasks} 新建 / {updated_tasks} 更新）。"
        ),
        link_path=f"/teams/{team_id}/projects/{project.id}/daily",
        exclude_user_id=current_user.id,
    )
    db.commit()
    db.refresh(project)

    days_payload = _build_daily_plan_days(day_map)
    return DailyPlanResponse(
        project_id=project.id,
        team_id=project.team_id,
        project_name=project.name,
        planned_start=project.planned_start,
        planned_end=project.planned_end,
        member_daily_hours=daily_cap,
        weekdays_only=opts.weekdays_only,
        assigned_work_item_count=assigned,
        created_task_count=created_tasks,
        updated_task_count=updated_tasks,
        day_count=len(days_payload),
        days=days_payload,
        schedule=_build_schedule_response(db, project),
    )


@router.get("/daily-plan", response_model=DailyPlanResponse)
def get_daily_plan(
    team_id: uuid.UUID,
    project_id: uuid.UUID,
    weekdays_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DailyPlanResponse:
    """Read-only day-by-day view from work items / linked tasks (after expand)."""
    require_team_membership(db, team_id=team_id, user=current_user)
    project = _require_project(db, team_id=team_id, project_id=project_id)

    items = (
        db.query(PhaseWorkItem, ProjectPhase)
        .join(ProjectPhase, ProjectPhase.id == PhaseWorkItem.phase_id)
        .filter(PhaseWorkItem.project_id == project.id)
        .order_by(
            ProjectPhase.sort_order.asc(),
            PhaseWorkItem.sort_order.asc(),
            PhaseWorkItem.created_at.asc(),
        )
        .all()
    )

    day_map: dict[date, list[dict]] = {}
    job_by_user = {
        m.user_id: (m.job_title or None)
        for m in db.query(TeamMember).filter(TeamMember.team_id == team_id).all()
    }
    for item, phase in items:
        # Prefer linked task due_date; else work item start day
        day = None
        if item.task_id:
            task = db.query(Task).filter(Task.id == item.task_id).one_or_none()
            if task and task.due_date:
                day = task.due_date
        if day is None:
            day = item.planned_start or phase.planned_start or project.planned_start
        if day is None:
            continue
        if weekdays_only and day.weekday() >= 5:
            # still show if already assigned to weekend
            pass
        day_map.setdefault(day, []).append(
            {
                "work_item_id": item.id,
                "task_id": item.task_id,
                "phase_id": phase.id,
                "phase_name": phase.name,
                "title": item.title,
                "assignee_user_id": item.assignee_user_id,
                "assignee_job_title": job_by_user.get(item.assignee_user_id)
                if item.assignee_user_id
                else None,
                "planned_hours": float(item.estimated_hours or 0),
                "status": item.status,
                "matched_job": _infer_job_from_title(item.title),
            }
        )

    days_payload = _build_daily_plan_days(day_map)
    return DailyPlanResponse(
        project_id=project.id,
        team_id=project.team_id,
        project_name=project.name,
        planned_start=project.planned_start,
        planned_end=project.planned_end,
        member_daily_hours=float(project.member_daily_hours or 6.0),
        weekdays_only=weekdays_only,
        assigned_work_item_count=sum(len(v) for v in day_map.values()),
        created_task_count=0,
        updated_task_count=0,
        day_count=len(days_payload),
        days=days_payload,
        schedule=None,
    )


def _iter_days(start: date, end: date, *, weekdays_only: bool) -> list[date]:
    days: list[date] = []
    cursor = start
    while cursor <= end:
        if not weekdays_only or cursor.weekday() < 5:
            days.append(cursor)
        cursor += timedelta(days=1)
    return days


def _infer_job_from_title(title: str) -> str:
    """Map work-item title to a preferred job_title bucket."""
    # Explicit prefixes produced by role-aware seeding
    if title.startswith("设计方案") or "设计方案：" in title:
        return "designer"
    if title.startswith("前端实现") or "前端实现：" in title:
        return "frontend"
    if title.startswith("后端实现") or "后端实现：" in title:
        return "backend"
    if title.startswith("全栈实现") or "全栈实现：" in title:
        return "fullstack"
    if title.startswith("验收确认") or "验收确认：" in title:
        return "qa"
    if title.startswith("交付收尾") or "交付收尾：" in title or "交付核对" in title:
        return "ops"
    if title.startswith("澄清目标") or "澄清目标：" in title:
        return "pm"
    if "运维推进" in title or title.startswith("运维"):
        return "ops"
    if "产品推进" in title:
        return "pm"
    if any(k in title for k in ("高保真", "交互", "视觉", "UI", "UX")):
        return "designer"
    if any(k in title for k in ("测试", "联调", "QA", "质量", "验收")):
        return "qa"
    if any(k in title for k in ("上线", "发布", "运维", "部署")):
        return "ops"
    if "前端" in title or "页面" in title:
        return "frontend"
    if "后端" in title or "接口" in title or "API" in title:
        return "backend"
    if "全栈" in title or "开发实现" in title or "实现：" in title:
        return "fullstack"
    if any(k in title for k in ("目标", "需求", "干系人", "复盘", "产品")):
        return "pm"
    return "pm"


def _job_fallback_chain(job: str, *, available: set[str]) -> list[str]:
    """Prefer the requested job, then nearby roles that actually exist on the team."""
    chains = {
        "pm": ["pm", "ops", "fullstack", "frontend", "backend", "qa", "designer"],
        "designer": ["designer", "frontend", "pm", "fullstack"],
        "frontend": ["frontend", "fullstack", "backend", "designer", "pm"],
        "backend": ["backend", "fullstack", "frontend", "ops", "pm"],
        "fullstack": ["fullstack", "frontend", "backend", "pm"],
        "qa": ["qa", "backend", "fullstack", "pm"],
        "ops": ["ops", "backend", "fullstack", "pm"],
    }
    ordered = chains.get(job, ["pm", "fullstack", "frontend", "backend", "qa", "ops", "designer"])
    if available:
        filtered = [j for j in ordered if j in available]
        if filtered:
            return filtered
        # No overlap — just use whatever jobs the team has
        return list(available)
    return ordered


def _load_job_pools(
    db: Session, *, team_id: uuid.UUID
) -> dict[str, list[uuid.UUID]]:
    rows = (
        db.query(TeamMember)
        .filter(TeamMember.team_id == team_id)
        .order_by(TeamMember.created_at.asc())
        .all()
    )
    pools: dict[str, list[uuid.UUID]] = {}
    for member in rows:
        job = (member.job_title or "").strip().lower()
        if not job:
            continue
        pools.setdefault(job, []).append(member.user_id)
    return pools


def _pick_assignee_for_job(
    *,
    preferred_job: str,
    pools: dict[str, list[uuid.UUID]],
    person_day_load: dict[tuple[uuid.UUID, date], float],
    day: date,
    default_assignee: uuid.UUID,
    all_member_ids: list[uuid.UUID],
) -> tuple[uuid.UUID, str | None]:
    available = set(pools.keys())
    for job in _job_fallback_chain(preferred_job, available=available):
        candidates = pools.get(job) or []
        if not candidates:
            continue
        chosen = min(
            candidates,
            key=lambda uid: (person_day_load.get((uid, day), 0.0), str(uid)),
        )
        return chosen, job
    # No job titles set — balance across all members
    if all_member_ids:
        chosen = min(
            all_member_ids,
            key=lambda uid: (person_day_load.get((uid, day), 0.0), str(uid)),
        )
        return chosen, None
    return default_assignee, None


def _build_daily_plan_days(day_map: dict[date, list[dict]]) -> list[DailyPlanDay]:
    result: list[DailyPlanDay] = []
    for day in sorted(day_map.keys()):
        assignments = day_map[day]
        phase_id = assignments[0]["phase_id"] if assignments else None
        phase_name = assignments[0]["phase_name"] if assignments else None
        total = round(sum(float(a["planned_hours"]) for a in assignments), 1)
        result.append(
            DailyPlanDay(
                date=day,
                phase_id=phase_id,
                phase_name=phase_name,
                total_planned_hours=total,
                assignments=[
                    DailyPlanAssignment(
                        work_item_id=a["work_item_id"],
                        task_id=a["task_id"],
                        phase_id=a["phase_id"],
                        phase_name=a["phase_name"],
                        title=a["title"],
                        assignee_user_id=a["assignee_user_id"],
                        assignee_job_title=a.get("assignee_job_title"),
                        planned_hours=float(a["planned_hours"]),
                        status=a["status"],
                        matched_job=a.get("matched_job"),
                    )
                    for a in assignments
                ],
            )
        )
    return result


@router.post("/confirm", response_model=ProjectCycleScheduleResponse)
def confirm_cycle_schedule(
    team_id: uuid.UUID,
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectCycleScheduleResponse:
    require_team_membership(db, team_id=team_id, user=current_user)
    project = _require_project(db, team_id=team_id, project_id=project_id)
    phase_count = (
        db.query(ProjectPhase.id).filter(ProjectPhase.project_id == project.id).count()
    )
    if phase_count == 0:
        raise HTTPException(
            status_code=400,
            detail="Generate a cycle schedule before confirming the plan",
        )
    project.plan_confirmed = True
    notify_team_members(
        db,
        team_id=team_id,
        project_id=project.id,
        type="cycle_schedule_confirmed",
        category="周期",
        title="全局周期计划已确认",
        body=f"「{project.name}」的全周期计划已确认，可按阶段安排当日工作。",
        link_path=f"/teams/{team_id}/projects/{project.id}/schedule",
        exclude_user_id=current_user.id,
    )
    db.commit()
    db.refresh(project)
    return _build_schedule_response(db, project)
