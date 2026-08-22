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


def _validate_assignee(db: Session, *, team_id: uuid.UUID, user_id: uuid.UUID) -> None:
    exists = (
        db.query(TeamMember.id)
        .filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
        .first()
    )
    if exists is None:
        raise HTTPException(
            status_code=400,
            detail="assignee_user_id must be a member of this team",
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


def _resolve_phase_names(opts: GenerateCycleScheduleRequest) -> list[str]:
    if opts.phase_names:
        names = [n.strip() for n in opts.phase_names if n and n.strip()]
        if names:
            return names
    count = opts.phase_count
    names = list(DEFAULT_PHASE_NAMES[:count])
    while len(names) < count:
        names.append(f"阶段 {len(names) + 1}")
    return names


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
    """Create phases. Seed work items from real tasks (default), empty, or placeholders."""
    require_team_membership(db, team_id=team_id, user=current_user)
    project = _require_project(db, team_id=team_id, project_id=project_id)

    opts = body or GenerateCycleScheduleRequest()
    if not project.planned_start or not project.planned_end:
        raise HTTPException(
            status_code=400,
            detail="Set project planned_start and planned_end before generating schedule",
        )
    _validate_dates(project.planned_start, project.planned_end)

    seed_mode = (opts.seed_mode or "from_tasks").strip().lower()
    if seed_mode not in {"from_tasks", "phases_only", "placeholders"}:
        raise HTTPException(
            status_code=400,
            detail="seed_mode must be from_tasks, phases_only, or placeholders",
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

    names = _resolve_phase_names(opts)
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

    if seed_mode == "from_tasks":
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
        body=f"「{project.name}」已生成 {count} 个阶段（模式：{seed_mode}）。",
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
        _validate_assignee(db, team_id=team_id, user_id=assignee)

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
        _validate_assignee(db, team_id=team_id, user_id=body.assignee_user_id)
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
