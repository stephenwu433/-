"""Per-project daily report: auto-aggregated + optional narrative."""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.membership import require_team_membership
from app.models import Project, ProjectDailyReport, Task, TaskTimeEntry, User
from app.schemas import (
    DailyReportResponse,
    DailyReportSaveRequest,
    DailyReportWorkItem,
)

router = APIRouter(
    prefix="/teams/{team_id}/projects/{project_id}/daily-report",
    tags=["daily-report"],
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


def _auto_summary(
    *,
    day: date,
    day_task_count: int,
    day_hours: float,
    progress: int,
    done: int,
    total: int,
) -> str:
    label = f"{day.month}月{day.day}日"
    if day_task_count == 0 and day_hours <= 0:
        return f"{label}没有此项目任务或工时记录，可切换日期查看，或先在每日任务里添加。"
    parts = [
        f"{label}共有 {day_task_count} 项相关任务",
        f"当日已填工时 {day_hours}h",
        f"项目整体进度 {progress}%（{done}/{total}）",
    ]
    return "，".join(parts) + "。"


def _build_report(
    db: Session, *, project: Project, day: date
) -> DailyReportResponse:
    all_tasks = (
        db.query(Task)
        .filter(Task.project_id == project.id)
        .order_by(Task.sort_order.asc(), Task.created_at.asc())
        .all()
    )
    total = len(all_tasks)
    done = sum(1 for t in all_tasks if t.status == "done")
    progress = int(round((done / total) * 100)) if total else 0

    entries = (
        db.query(TaskTimeEntry)
        .filter(
            TaskTimeEntry.project_id == project.id,
            TaskTimeEntry.work_date == day,
        )
        .all()
    )
    entry_task_ids = {e.task_id for e in entries}
    hours_by_task: dict[uuid.UUID, float] = defaultdict(float)
    notes_by_task: dict[uuid.UUID, list[str]] = defaultdict(list)
    for entry in entries:
        hours_by_task[entry.task_id] += float(entry.hours or 0)
        if entry.note:
            notes_by_task[entry.task_id].append(entry.note)

    day_tasks_query = db.query(Task).filter(Task.project_id == project.id)
    if entry_task_ids:
        day_tasks_query = day_tasks_query.filter(
            or_(Task.due_date == day, Task.id.in_(entry_task_ids))
        )
    else:
        day_tasks_query = day_tasks_query.filter(Task.due_date == day)
    day_tasks = day_tasks_query.order_by(
        Task.sort_order.asc(), Task.created_at.asc()
    ).all()

    assignee_ids = {t.assignee_user_id for t in day_tasks if t.assignee_user_id}
    names: dict[uuid.UUID, str] = {}
    if assignee_ids:
        for user in db.query(User).filter(User.id.in_(assignee_ids)).all():
            names[user.id] = user.display_name or user.email or user.clerk_user_id

    work_items = [
        DailyReportWorkItem(
            task_id=task.id,
            title=task.title,
            status=task.status,
            assignee_user_id=task.assignee_user_id,
            assignee_display_name=(
                names.get(task.assignee_user_id) if task.assignee_user_id else None
            ),
            due_date=task.due_date,
            logged_hours=round(float(hours_by_task.get(task.id, 0.0)), 1),
            notes=notes_by_task.get(task.id, []),
        )
        for task in day_tasks
    ]
    day_hours = round(sum(hours_by_task.values()), 1)
    auto = _auto_summary(
        day=day,
        day_task_count=len(work_items),
        day_hours=day_hours,
        progress=progress,
        done=done,
        total=total,
    )

    saved = (
        db.query(ProjectDailyReport)
        .filter(
            ProjectDailyReport.project_id == project.id,
            ProjectDailyReport.report_date == day,
        )
        .one_or_none()
    )

    return DailyReportResponse(
        view_date=day,
        project_id=project.id,
        team_id=project.team_id,
        project_name=project.name,
        project_status=project.status,
        progress_percent=progress,
        total_tasks=total,
        done_tasks=done,
        day_task_count=len(work_items),
        day_logged_hours=day_hours,
        auto_summary=auto,
        summary_text=saved.summary_text if saved else None,
        next_actions=saved.next_actions if saved else None,
        saved=saved is not None,
        work_items=work_items,
    )


@router.get("", response_model=DailyReportResponse)
def get_daily_report(
    team_id: uuid.UUID,
    project_id: uuid.UUID,
    view_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DailyReportResponse:
    require_team_membership(db, team_id=team_id, user=current_user)
    project = _require_project(db, team_id=team_id, project_id=project_id)
    day = view_date or date.today()
    return _build_report(db, project=project, day=day)


@router.put("", response_model=DailyReportResponse)
def save_daily_report(
    team_id: uuid.UUID,
    project_id: uuid.UUID,
    body: DailyReportSaveRequest,
    view_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DailyReportResponse:
    require_team_membership(db, team_id=team_id, user=current_user)
    project = _require_project(db, team_id=team_id, project_id=project_id)
    day = view_date or date.today()

    summary = body.summary_text.strip() if body.summary_text else None
    if summary == "":
        summary = None
    actions = body.next_actions.strip() if body.next_actions else None
    if actions == "":
        actions = None

    row = (
        db.query(ProjectDailyReport)
        .filter(
            ProjectDailyReport.project_id == project.id,
            ProjectDailyReport.report_date == day,
        )
        .one_or_none()
    )
    if row is None:
        row = ProjectDailyReport(
            team_id=team_id,
            project_id=project.id,
            report_date=day,
            summary_text=summary,
            next_actions=actions,
            created_by_user_id=current_user.id,
        )
        db.add(row)
    else:
        row.summary_text = summary
        row.next_actions = actions

    db.commit()
    return _build_report(db, project=project, day=day)
