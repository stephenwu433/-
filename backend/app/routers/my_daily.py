"""Personal daily tasks across all teams/projects for the current user."""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models import PhaseWorkItem, Project, ProjectPhase, Task, TaskTimeEntry, Team, TeamMember, User
from app.schemas import MyDailyTaskItem, MyDailyTasksResponse

router = APIRouter(tags=["my-daily"])


@router.get("/my-daily-tasks", response_model=MyDailyTasksResponse)
def list_my_daily_tasks(
    view_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MyDailyTasksResponse:
    """Tasks assigned to me that are due today, or that I logged hours on today."""
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

    query = db.query(Task).filter(
        Task.team_id.in_(team_ids),
        Task.assignee_user_id == current_user.id,
    )
    if my_entry_task_ids:
        query = query.filter(or_(Task.due_date == day, Task.id.in_(my_entry_task_ids)))
    else:
        query = query.filter(Task.due_date == day)

    tasks = query.order_by(Task.sort_order.asc(), Task.created_at.asc()).all()
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
    todo_count = doing_count = done_count = 0
    for task in tasks:
        project = projects.get(task.project_id)
        team = teams.get(task.team_id)
        entry = mine.get(task.id)
        hours = float(entry.hours) if entry else 0.0
        my_hours_total += hours
        status = (task.status or "todo").lower()
        if status == "doing":
            doing_count += 1
        elif status == "done":
            done_count += 1
        else:
            todo_count += 1
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
                my_hours=hours,
                my_note=entry.note if entry else None,
                my_entry_id=entry.id if entry else None,
            )
        )

    return MyDailyTasksResponse(
        view_date=day,
        task_count=len(items),
        todo_count=todo_count,
        doing_count=doing_count,
        done_count=done_count,
        my_logged_hours=round(my_hours_total, 1),
        tasks=items,
    )
