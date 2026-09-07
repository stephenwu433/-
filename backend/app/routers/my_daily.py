"""Personal daily tasks across all teams/projects for the current user."""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models import PhaseWorkItem, Project, ProjectPhase, Task, TaskTimeEntry, Team, TeamMember, User
from app.schemas import MyDailyTaskItem, MyDailyTasksResponse

router = APIRouter(tags=["my-daily"])

OPEN_STATUSES = ("todo", "doing", "review", "returned")
IN_FLIGHT_STATUSES = ("doing", "review", "returned")


def _bucket_for(task: Task, day: date, logged_task_ids: set[uuid.UUID]) -> str:
    status = (task.status or "todo").lower()
    due = task.due_date
    if due is not None and due < day and status != "done":
        return "overdue"
    if due == day or task.id in logged_task_ids:
        return "today"
    return "later"


@router.get("/my-daily-tasks", response_model=MyDailyTasksResponse)
def list_my_daily_tasks(
    view_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MyDailyTasksResponse:
    """Assigned work for this day: due today, overdue, in-flight, or hours logged today."""
    day = view_date or date.today()

    team_ids = [
        row[0]
        for row in db.query(TeamMember.team_id)
        .filter(TeamMember.user_id == current_user.id)
        .all()
    ]
    if not team_ids:
        return MyDailyTasksResponse(view_date=day)

    my_entry_task_ids = [
        row[0]
        for row in db.query(TaskTimeEntry.task_id)
        .filter(
            TaskTimeEntry.user_id == current_user.id,
            TaskTimeEntry.work_date == day,
            TaskTimeEntry.team_id.in_(team_ids),
        )
        .distinct()
        .all()
    ]
    logged_ids = set(my_entry_task_ids)

    conditions = [
        Task.due_date == day,
        and_(
            Task.due_date.is_not(None),
            Task.due_date < day,
            Task.status.in_(OPEN_STATUSES),
        ),
        and_(
            Task.status.in_(IN_FLIGHT_STATUSES),
            or_(Task.due_date.is_(None), Task.due_date > day),
        ),
    ]
    if my_entry_task_ids:
        conditions.append(Task.id.in_(my_entry_task_ids))

    tasks = (
        db.query(Task)
        .filter(
            Task.team_id.in_(team_ids),
            Task.assignee_user_id == current_user.id,
            or_(*conditions),
        )
        .order_by(Task.due_date.asc().nulls_last(), Task.sort_order.asc(), Task.created_at.asc())
        .all()
    )
    if not tasks:
        return MyDailyTasksResponse(view_date=day)

    project_ids = {t.project_id for t in tasks}
    team_id_set = {t.team_id for t in tasks}
    task_ids = [t.id for t in tasks]

    projects = {
        p.id: p
        for p in db.query(Project).filter(Project.id.in_(project_ids)).all()
    }
    teams = {
        t.id: t for t in db.query(Team).filter(Team.id.in_(team_id_set)).all()
    }

    phase_by_task: dict[uuid.UUID, str] = {}
    rows = (
        db.query(PhaseWorkItem.task_id, ProjectPhase.name)
        .join(ProjectPhase, ProjectPhase.id == PhaseWorkItem.phase_id)
        .filter(PhaseWorkItem.task_id.in_(task_ids))
        .all()
    )
    for task_id, phase_name in rows:
        if task_id is not None and task_id not in phase_by_task:
            phase_by_task[task_id] = phase_name

    entries = (
        db.query(TaskTimeEntry)
        .filter(
            TaskTimeEntry.user_id == current_user.id,
            TaskTimeEntry.work_date == day,
            TaskTimeEntry.task_id.in_(task_ids),
        )
        .all()
    )
    mine = {e.task_id: e for e in entries}

    items: list[MyDailyTaskItem] = []
    my_hours_total = 0.0
    planned_hours = 0.0
    todo_count = doing_count = review_count = done_count = returned_count = 0
    overdue_count = today_count = later_count = 0
    capacity = 6.0
    hours_set = {
        float(project.member_daily_hours or 6.0) for project in projects.values()
    }
    if len(hours_set) == 1:
        capacity = hours_set.pop()

    for task in tasks:
        project = projects.get(task.project_id)
        team = teams.get(task.team_id)
        entry = mine.get(task.id)
        hours = float(entry.hours) if entry else 0.0
        my_hours_total += hours
        estimated = float(task.estimated_hours or 0.0)
        status = (task.status or "todo").lower()
        bucket = _bucket_for(task, day, logged_ids)
        if bucket in ("today", "overdue"):
            planned_hours += estimated
        if status == "doing":
            doing_count += 1
        elif status == "review":
            review_count += 1
        elif status == "done":
            done_count += 1
        elif status == "returned":
            returned_count += 1
        else:
            todo_count += 1
        if bucket == "overdue":
            overdue_count += 1
        elif bucket == "later":
            later_count += 1
        else:
            today_count += 1
        items.append(
            MyDailyTaskItem(
                task_id=task.id,
                title=task.title,
                status=task.status,
                due_date=task.due_date,
                team_id=task.team_id,
                team_name=team.name if team else "",
                project_id=task.project_id,
                project_name=project.name if project else "",
                phase_name=phase_by_task.get(task.id),
                estimated_hours=estimated,
                my_hours=hours,
                my_note=entry.note if entry else None,
                my_entry_id=entry.id if entry else None,
                my_completion_percent=int(entry.completion_percent or 0) if entry else 0,
                bucket=bucket,
            )
        )

    return MyDailyTasksResponse(
        view_date=day,
        task_count=len(items),
        todo_count=todo_count,
        doing_count=doing_count,
        review_count=review_count,
        done_count=done_count,
        returned_count=returned_count,
        overdue_count=overdue_count,
        today_count=today_count,
        later_count=later_count,
        my_logged_hours=round(my_hours_total, 1),
        planned_hours=round(planned_hours, 1),
        capacity_hours=round(capacity, 1),
        tasks=items,
    )
