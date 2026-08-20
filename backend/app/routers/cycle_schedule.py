"""Per-project cycle schedule: phases + work items."""

from __future__ import annotations

import uuid
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.membership import require_team_membership
from app.models import PhaseWorkItem, Project, ProjectPhase, TeamMember, User
from app.schemas import (
    DEFAULT_PHASE_NAMES,
    PHASE_WORK_ITEM_STATUSES,
    GenerateCycleScheduleRequest,
    PhaseWorkItemResponse,
    PhaseWorkItemUpdateRequest,
    ProjectCycleScheduleResponse,
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
    for item in items:
        items_by_phase.setdefault(item.phase_id, []).append(item)
        total_hours += float(item.estimated_hours or 0)

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
        phases=phase_payloads,
    )


def _split_range(start: date, end: date, count: int) -> list[tuple[date, date]]:
    """Split inclusive date range into `count` contiguous segments."""
    total_days = (end - start).days + 1
    if total_days < count:
        # Too short: each phase gets at least the start day, clamp ends
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
    # rough: 40% of member daily capacity across calendar days
    return round(max(days, 1) * daily_hours * 0.4, 1)


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
    """Create default phases + one work item each from project date range."""
    require_team_membership(db, team_id=team_id, user=current_user)
    project = _require_project(db, team_id=team_id, project_id=project_id)

    opts = body or GenerateCycleScheduleRequest()
    if not project.planned_start or not project.planned_end:
        raise HTTPException(
            status_code=400,
            detail="Set project planned_start and planned_end before generating schedule",
        )
    _validate_dates(project.planned_start, project.planned_end)

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
        db.query(PhaseWorkItem).filter(PhaseWorkItem.project_id == project.id).delete()
        db.query(ProjectPhase).filter(ProjectPhase.project_id == project.id).delete()
        db.flush()

    count = opts.phase_count
    names = list(DEFAULT_PHASE_NAMES[:count])
    while len(names) < count:
        names.append(f"阶段 {len(names) + 1}")

    segments = _split_range(project.planned_start, project.planned_end, count)
    daily = float(project.member_daily_hours or 6.0)
    default_assignee = project.owner_user_id or current_user.id

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
        hours = _estimate_hours(seg_start, seg_end, daily)
        item = PhaseWorkItem(
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
        db.add(item)

    project.plan_confirmed = False
    db.commit()
    db.refresh(project)
    return _build_schedule_response(db, project)


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
    _require_project(db, team_id=team_id, project_id=project_id)
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

    db.commit()
    db.refresh(phase)
    items = (
        db.query(PhaseWorkItem)
        .filter(PhaseWorkItem.phase_id == phase.id)
        .order_by(PhaseWorkItem.sort_order.asc())
        .all()
    )
    return _phase_to_response(phase, items)


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
    _require_project(db, team_id=team_id, project_id=project_id)
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

    project = _require_project(db, team_id=team_id, project_id=project_id)
    project.plan_confirmed = False

    db.commit()
    db.refresh(item)
    return _work_item_to_response(item)


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
    db.commit()
    db.refresh(project)
    return _build_schedule_response(db, project)
