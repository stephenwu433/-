"""Project create / list / update endpoints (status + schedule + setup fields)."""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.membership import require_team_membership
from app.models import Project, Task, Team, TeamMember, User
from app.project_members import ensure_project_member
from app.schemas import (
    PROJECT_STATUSES,
    PortfolioProjectCard,
    PortfolioResponse,
    PortfolioStats,
    ProjectCreateRequest,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdateRequest,
    ScheduleResponse,
)

router = APIRouter(prefix="/teams/{team_id}/projects", tags=["projects"])
portfolio_router = APIRouter(tags=["portfolio"])


def _to_response(project: Project) -> ProjectResponse:
    return ProjectResponse(
        id=project.id,
        team_id=project.team_id,
        name=project.name,
        description=project.description,
        objective=project.objective,
        status=project.status,
        planned_start=project.planned_start,
        planned_end=project.planned_end,
        owner_user_id=project.owner_user_id,
        member_daily_hours=float(project.member_daily_hours or 6.0),
        plan_confirmed=bool(project.plan_confirmed),
        created_at=project.created_at,
    )


def _validate_schedule(start, end) -> None:
    if start and end and end < start:
        raise HTTPException(
            status_code=400,
            detail="planned_end cannot be earlier than planned_start",
        )


def _ensure_team_member_user(
    db: Session, *, team_id: uuid.UUID, user_id: uuid.UUID
) -> None:
    exists = (
        db.query(TeamMember.id)
        .filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
        .first()
    )
    if exists is None:
        raise HTTPException(
            status_code=400,
            detail="owner_user_id must be a member of this team",
        )


def _get_team_project(
    db: Session,
    *,
    team_id: uuid.UUID,
    project_id: uuid.UUID,
) -> Project:
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.team_id == team_id)
        .one_or_none()
    )
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    return project


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    team_id: uuid.UUID,
    body: ProjectCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectResponse:
    require_team_membership(db, team_id=team_id, user=current_user)

    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Project name cannot be empty")

    description = body.description.strip() if body.description else None
    if description == "":
        description = None
    objective = body.objective.strip() if body.objective else None
    if objective == "":
        objective = None

    _validate_schedule(body.planned_start, body.planned_end)

    owner_id = body.owner_user_id or current_user.id
    _ensure_team_member_user(db, team_id=team_id, user_id=owner_id)

    project = Project(
        team_id=team_id,
        name=name,
        description=description,
        objective=objective,
        status="active",
        planned_start=body.planned_start,
        planned_end=body.planned_end,
        owner_user_id=owner_id,
        member_daily_hours=body.member_daily_hours,
        plan_confirmed=False,
        created_by_user_id=current_user.id,
    )
    db.add(project)
    db.flush()
    # Seed project roster: creator + owner (reference: 此项目的成员)
    ensure_project_member(
        db,
        team_id=team_id,
        project_id=project.id,
        user_id=current_user.id,
    )
    if owner_id != current_user.id:
        ensure_project_member(
            db,
            team_id=team_id,
            project_id=project.id,
            user_id=owner_id,
        )
    db.commit()
    db.refresh(project)
    return _to_response(project)


@router.get("", response_model=ProjectListResponse)
def list_team_projects(
    team_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectListResponse:
    require_team_membership(db, team_id=team_id, user=current_user)

    rows = (
        db.query(Project)
        .filter(Project.team_id == team_id)
        .order_by(Project.created_at.desc())
        .all()
    )
    return ProjectListResponse(projects=[_to_response(row) for row in rows])


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    team_id: uuid.UUID,
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectResponse:
    require_team_membership(db, team_id=team_id, user=current_user)
    project = _get_team_project(db, team_id=team_id, project_id=project_id)
    return _to_response(project)


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    team_id: uuid.UUID,
    project_id: uuid.UUID,
    body: ProjectUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectResponse:
    """Update status, schedule, and setup fields."""
    require_team_membership(db, team_id=team_id, user=current_user)
    project = _get_team_project(db, team_id=team_id, project_id=project_id)

    if body.name is not None:
        name = body.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="Project name cannot be empty")
        project.name = name

    if body.description is not None:
        description = body.description.strip()
        project.description = description or None

    if body.objective is not None:
        objective = body.objective.strip()
        project.objective = objective or None

    if body.status is not None:
        new_status = body.status.strip().lower()
        if new_status not in PROJECT_STATUSES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Use one of: {', '.join(PROJECT_STATUSES)}",
            )
        project.status = new_status

    if body.clear_schedule:
        project.planned_start = None
        project.planned_end = None
    else:
        if body.planned_start is not None:
            project.planned_start = body.planned_start
        if body.planned_end is not None:
            project.planned_end = body.planned_end
        _validate_schedule(project.planned_start, project.planned_end)

    if body.clear_owner:
        project.owner_user_id = None
    elif body.owner_user_id is not None:
        _ensure_team_member_user(db, team_id=team_id, user_id=body.owner_user_id)
        project.owner_user_id = body.owner_user_id

    if body.member_daily_hours is not None:
        project.member_daily_hours = body.member_daily_hours

    if body.plan_confirmed is not None:
        project.plan_confirmed = body.plan_confirmed

    db.commit()
    db.refresh(project)
    return _to_response(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    team_id: uuid.UUID,
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a project and cascaded schedule/tasks/reports."""
    require_team_membership(db, team_id=team_id, user=current_user)
    project = _get_team_project(db, team_id=team_id, project_id=project_id)
    db.delete(project)
    db.commit()


schedule_router = APIRouter(prefix="/teams/{team_id}", tags=["schedule"])


@schedule_router.get("/schedule", response_model=ScheduleResponse)
def list_team_schedule(
    team_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ScheduleResponse:
    """Projects that have schedule dates (for calendar)."""
    require_team_membership(db, team_id=team_id, user=current_user)
    rows = (
        db.query(Project)
        .filter(
            Project.team_id == team_id,
            Project.planned_start.is_not(None),
        )
        .order_by(Project.planned_start.asc(), Project.name.asc())
        .all()
    )
    return ScheduleResponse(projects=[_to_response(row) for row in rows])


@portfolio_router.get("/portfolio", response_model=PortfolioResponse)
def get_portfolio(
    view_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PortfolioResponse:
    """Cross-team project overview for the current user."""
    day = view_date or date.today()

    team_ids = [
        row[0]
        for row in db.query(TeamMember.team_id)
        .filter(TeamMember.user_id == current_user.id)
        .all()
    ]
    if not team_ids:
        return PortfolioResponse(
            view_date=day,
            stats=PortfolioStats(
                active_projects=0,
                total_tasks=0,
                day_tasks=0,
                day_task_hours_estimate=0.0,
                high_load_members=0,
            ),
            projects=[],
        )

    projects = (
        db.query(Project, Team)
        .join(Team, Team.id == Project.team_id)
        .filter(Project.team_id.in_(team_ids))
        .order_by(Project.created_at.desc())
        .all()
    )

    # member counts per team
    member_counts = dict(
        db.query(TeamMember.team_id, func.count(TeamMember.id))
        .filter(TeamMember.team_id.in_(team_ids))
        .group_by(TeamMember.team_id)
        .all()
    )

    # task aggregates per project
    task_rows = (
        db.query(
            Task.project_id,
            func.count(Task.id),
            func.sum(case((Task.status == "done", 1), else_=0)),
            func.sum(case((Task.due_date == day, 1), else_=0)),
        )
        .filter(Task.team_id.in_(team_ids))
        .group_by(Task.project_id)
        .all()
    )
    task_map = {
        pid: {
            "total": int(total or 0),
            "done": int(done or 0),
            "day": int(day_count or 0),
        }
        for pid, total, done, day_count in task_rows
    }

    # high load: assignees with >= 3 tasks due on view_date
    assignee_day_counts = (
        db.query(Task.assignee_user_id, func.count(Task.id))
        .filter(
            Task.team_id.in_(team_ids),
            Task.due_date == day,
            Task.assignee_user_id.is_not(None),
            Task.status != "done",
        )
        .group_by(Task.assignee_user_id)
        .all()
    )
    high_load = sum(1 for _uid, cnt in assignee_day_counts if int(cnt) >= 3)

    owner_ids = {p.owner_user_id for p, _t in projects if p.owner_user_id}
    owners = {}
    if owner_ids:
        for user in db.query(User).filter(User.id.in_(owner_ids)).all():
            owners[user.id] = user.display_name or user.email or user.clerk_user_id

    cards: list[PortfolioProjectCard] = []
    active = 0
    total_tasks = 0
    day_tasks = 0
    for project, team in projects:
        stats = task_map.get(project.id, {"total": 0, "done": 0, "day": 0})
        total = stats["total"]
        done = stats["done"]
        day_count = stats["day"]
        progress = int(round((done / total) * 100)) if total else 0
        if project.status == "active":
            active += 1
        total_tasks += total
        day_tasks += day_count
        cards.append(
            PortfolioProjectCard(
                id=project.id,
                team_id=project.team_id,
                team_name=team.name,
                name=project.name,
                description=project.description,
                objective=project.objective,
                status=project.status,
                planned_start=project.planned_start,
                planned_end=project.planned_end,
                owner_user_id=project.owner_user_id,
                owner_display_name=owners.get(project.owner_user_id) if project.owner_user_id else None,
                member_daily_hours=float(project.member_daily_hours or 6.0),
                plan_confirmed=bool(project.plan_confirmed),
                member_count=int(member_counts.get(project.team_id, 0)),
                task_count=total,
                done_task_count=done,
                progress_percent=progress,
                day_task_count=day_count,
                created_at=project.created_at,
            )
        )

    # rough hour estimate: day_tasks * 1.2h style demo number, or use daily hours / tasks
    day_hours = round(day_tasks * 1.2, 1) if day_tasks else 0.0

    return PortfolioResponse(
        view_date=day,
        stats=PortfolioStats(
            active_projects=active,
            total_tasks=total_tasks,
            day_tasks=day_tasks,
            day_task_hours_estimate=day_hours,
            high_load_members=high_load,
        ),
        projects=cards,
    )
