"""Daily tasks view + time entry (hours) logging."""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.membership import require_team_membership
from app.models import Project, ProjectDailyReport, Task, TaskTimeEntry, User
from app.schemas import (
    DailyDayFeedbackRequest,
    DailyTaskCard,
    DailyTasksResponse,
    TaskResponse,
    TimeEntryResponse,
    TimeEntryUpsertRequest,
)

router = APIRouter(
    prefix="/teams/{team_id}/projects/{project_id}",
    tags=["daily-tasks"],
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


def _task_to_response(task: Task) -> TaskResponse:
    return TaskResponse(
        id=task.id,
        team_id=task.team_id,
        project_id=task.project_id,
        title=task.title,
        description=task.description,
        status=task.status,
        assignee_user_id=task.assignee_user_id,
        due_date=task.due_date,
        sort_order=task.sort_order,
        created_at=task.created_at,
    )


def _entry_to_response(entry: TaskTimeEntry) -> TimeEntryResponse:
    return TimeEntryResponse(
        id=entry.id,
        team_id=entry.team_id,
        project_id=entry.project_id,
        task_id=entry.task_id,
        user_id=entry.user_id,
        work_date=entry.work_date,
        hours=float(entry.hours or 0),
        note=entry.note,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    )


@router.get("/daily-tasks", response_model=DailyTasksResponse)
def list_daily_tasks(
    team_id: uuid.UUID,
    project_id: uuid.UUID,
    view_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DailyTasksResponse:
    """Tasks due on view_date, plus any with time logged that day."""
    require_team_membership(db, team_id=team_id, user=current_user)
    project = _require_project(db, team_id=team_id, project_id=project_id)
    day = view_date or date.today()

    entry_task_ids = [
        row[0]
        for row in db.query(TaskTimeEntry.task_id)
        .filter(
            TaskTimeEntry.project_id == project_id,
            TaskTimeEntry.work_date == day,
        )
        .distinct()
        .all()
    ]

    tasks_query = db.query(Task).filter(
        Task.team_id == team_id,
        Task.project_id == project_id,
    )
    if entry_task_ids:
        tasks_query = tasks_query.filter(
            or_(Task.due_date == day, Task.id.in_(entry_task_ids))
        )
    else:
        tasks_query = tasks_query.filter(Task.due_date == day)

    tasks = tasks_query.order_by(Task.sort_order.asc(), Task.created_at.asc()).all()

    assignee_ids = {t.assignee_user_id for t in tasks if t.assignee_user_id}
    names: dict[uuid.UUID, str] = {}
    if assignee_ids:
        for user in db.query(User).filter(User.id.in_(assignee_ids)).all():
            names[user.id] = user.display_name or user.email or user.clerk_user_id

    entries = (
        db.query(TaskTimeEntry)
        .filter(
            TaskTimeEntry.project_id == project_id,
            TaskTimeEntry.work_date == day,
        )
        .all()
    )
    totals: dict[uuid.UUID, float] = {}
    mine: dict[uuid.UUID, TaskTimeEntry] = {}
    for entry in entries:
        totals[entry.task_id] = totals.get(entry.task_id, 0.0) + float(entry.hours or 0)
        if entry.user_id == current_user.id:
            mine[entry.task_id] = entry

    cards: list[DailyTaskCard] = []
    my_total = 0.0
    day_total = 0.0
    for task in tasks:
        my_entry = mine.get(task.id)
        my_hours = float(my_entry.hours) if my_entry else 0.0
        total_hours = float(totals.get(task.id, 0.0))
        my_total += my_hours
        day_total += total_hours
        cards.append(
            DailyTaskCard(
                task=_task_to_response(task),
                assignee_display_name=(
                    names.get(task.assignee_user_id) if task.assignee_user_id else None
                ),
                my_hours=my_hours,
                my_note=my_entry.note if my_entry else None,
                my_entry_id=my_entry.id if my_entry else None,
                total_hours=total_hours,
            )
        )

    report = (
        db.query(ProjectDailyReport)
        .filter(
            ProjectDailyReport.project_id == project_id,
            ProjectDailyReport.report_date == day,
        )
        .one_or_none()
    )

    return DailyTasksResponse(
        view_date=day,
        project_id=project.id,
        team_id=project.team_id,
        project_name=project.name,
        task_count=len(cards),
        total_logged_hours=round(day_total, 1),
        my_logged_hours=round(my_total, 1),
        completion_percent=int(report.completion_percent) if report else 0,
        day_note=report.day_note if report else None,
        tasks=cards,
    )


@router.put("/daily-tasks/feedback", response_model=DailyTasksResponse)
def save_daily_feedback(
    team_id: uuid.UUID,
    project_id: uuid.UUID,
    body: DailyDayFeedbackRequest,
    view_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DailyTasksResponse:
    """Save day completion % / note (reference: 任务总完成度滑条)."""
    require_team_membership(db, team_id=team_id, user=current_user)
    project = _require_project(db, team_id=team_id, project_id=project_id)
    day = view_date or date.today()

    note = body.day_note.strip() if body.day_note else None
    if note == "":
        note = None

    report = (
        db.query(ProjectDailyReport)
        .filter(
            ProjectDailyReport.project_id == project_id,
            ProjectDailyReport.report_date == day,
        )
        .one_or_none()
    )
    if report is None:
        report = ProjectDailyReport(
            team_id=team_id,
            project_id=project_id,
            report_date=day,
            completion_percent=body.completion_percent,
            day_note=note,
            created_by_user_id=current_user.id,
        )
        db.add(report)
    else:
        report.completion_percent = body.completion_percent
        report.day_note = note

    if body.apply_review_status and body.completion_percent >= 100:
        day_tasks = (
            db.query(Task)
            .filter(
                Task.project_id == project_id,
                Task.due_date == day,
                Task.status.in_(("todo", "doing", "returned")),
            )
            .all()
        )
        for task in day_tasks:
            task.status = "review"

    db.commit()
    return list_daily_tasks(
        team_id=team_id,
        project_id=project_id,
        view_date=day,
        db=db,
        current_user=current_user,
    )


@router.put(
    "/tasks/{task_id}/time-entries/{work_date}",
    response_model=TimeEntryResponse,
)
def upsert_time_entry(
    team_id: uuid.UUID,
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    work_date: date,
    body: TimeEntryUpsertRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TimeEntryResponse:
    """Create or update the current user's hours for a task on a date."""
    require_team_membership(db, team_id=team_id, user=current_user)
    _require_project(db, team_id=team_id, project_id=project_id)

    task = (
        db.query(Task)
        .filter(
            Task.id == task_id,
            Task.team_id == team_id,
            Task.project_id == project_id,
        )
        .one_or_none()
    )
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    note = body.note.strip() if body.note else None
    if note == "":
        note = None

    entry = (
        db.query(TaskTimeEntry)
        .filter(
            TaskTimeEntry.task_id == task_id,
            TaskTimeEntry.user_id == current_user.id,
            TaskTimeEntry.work_date == work_date,
        )
        .one_or_none()
    )
    if entry is None:
        entry = TaskTimeEntry(
            team_id=team_id,
            project_id=project_id,
            task_id=task_id,
            user_id=current_user.id,
            work_date=work_date,
            hours=body.hours,
            note=note,
        )
        db.add(entry)
    else:
        entry.hours = body.hours
        entry.note = note

    db.commit()
    db.refresh(entry)
    return _entry_to_response(entry)


@router.get("/time-entries", response_model=list[TimeEntryResponse])
def list_time_entries(
    team_id: uuid.UUID,
    project_id: uuid.UUID,
    view_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TimeEntryResponse]:
    require_team_membership(db, team_id=team_id, user=current_user)
    _require_project(db, team_id=team_id, project_id=project_id)
    day = view_date or date.today()
    rows = (
        db.query(TaskTimeEntry)
        .filter(
            TaskTimeEntry.project_id == project_id,
            TaskTimeEntry.work_date == day,
        )
        .order_by(TaskTimeEntry.created_at.asc())
        .all()
    )
    return [_entry_to_response(row) for row in rows]
