"""Team daily board: who is doing what today, grouped by member."""

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
from app.models import PhaseWorkItem, Project, ProjectPhase, Task, TaskTimeEntry, TeamMember, User
from app.schemas import (
    TeamDailyBoardResponse,
    TeamDailyMemberColumn,
    TeamDailyTaskItem,
)

router = APIRouter(tags=["team-daily"])

JOB_TITLE_LABELS_ZH = {
    "project_manager": "项目经理",
    "pm": "产品经理",
    "designer": "设计师",
    "ops": "运营",
    "other": "其他",
}


def _status_bucket(status: str | None) -> str:
    s = (status or "todo").lower()
    if s in ("doing", "done"):
        return s
    return "todo"


@router.get("/teams/{team_id}/team-daily", response_model=TeamDailyBoardResponse)
def get_team_daily_board(
    team_id: uuid.UUID,
    view_date: date | None = Query(default=None),
    project_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TeamDailyBoardResponse:
    """Tasks due today (or with hours logged today) for a team, grouped by assignee."""
    team, _membership = require_team_membership(db, team_id=team_id, user=current_user)
    day = view_date or date.today()

    if project_id is not None:
        project = (
            db.query(Project)
            .filter(Project.id == project_id, Project.team_id == team_id)
            .one_or_none()
        )
        if project is None:
            raise HTTPException(status_code=404, detail="Project not found in this team")

    memberships = (
        db.query(TeamMember, User)
        .join(User, User.id == TeamMember.user_id)
        .filter(TeamMember.team_id == team_id)
        .order_by(User.display_name.asc().nulls_last(), User.email.asc().nulls_last())
        .all()
    )

    entry_q = db.query(TaskTimeEntry.task_id).filter(
        TaskTimeEntry.team_id == team_id,
        TaskTimeEntry.work_date == day,
    )
    if project_id is not None:
        entry_q = entry_q.filter(TaskTimeEntry.project_id == project_id)
    entry_task_ids = [row[0] for row in entry_q.distinct().all()]

    task_q = db.query(Task).filter(Task.team_id == team_id)
    if project_id is not None:
        task_q = task_q.filter(Task.project_id == project_id)
    if entry_task_ids:
        task_q = task_q.filter(or_(Task.due_date == day, Task.id.in_(entry_task_ids)))
    else:
        task_q = task_q.filter(Task.due_date == day)

    tasks = task_q.order_by(Task.sort_order.asc(), Task.created_at.asc()).all()
    task_ids = [t.id for t in tasks]

    projects = {
        p.id: p
        for p in db.query(Project).filter(Project.team_id == team_id).all()
    }

    phase_by_task: dict[uuid.UUID, str] = {}
    if task_ids:
        rows = (
            db.query(PhaseWorkItem.task_id, ProjectPhase.name)
            .join(ProjectPhase, ProjectPhase.id == PhaseWorkItem.phase_id)
            .filter(PhaseWorkItem.task_id.in_(task_ids))
            .all()
        )
        for tid, phase_name in rows:
            if tid is not None and tid not in phase_by_task:
                phase_by_task[tid] = phase_name

    hours_by_task_user: dict[tuple[uuid.UUID, uuid.UUID], tuple[float, str | None]] = {}
    if task_ids:
        entries = (
            db.query(TaskTimeEntry)
            .filter(
                TaskTimeEntry.team_id == team_id,
                TaskTimeEntry.work_date == day,
                TaskTimeEntry.task_id.in_(task_ids),
            )
            .all()
        )
        for e in entries:
            hours_by_task_user[(e.task_id, e.user_id)] = (float(e.hours), e.note)

    by_assignee: dict[uuid.UUID | None, list[Task]] = defaultdict(list)
    for task in tasks:
        by_assignee[task.assignee_user_id].append(task)

    members_out: list[TeamDailyMemberColumn] = []
    total_tasks = todo_count = doing_count = done_count = 0
    logged_hours = 0.0

    for membership, user in memberships:
        member_tasks = by_assignee.pop(user.id, [])
        items: list[TeamDailyTaskItem] = []
        m_todo = m_doing = m_done = 0
        m_hours = 0.0
        for task in member_tasks:
            project = projects.get(task.project_id)
            hours, note = hours_by_task_user.get((task.id, user.id), (0.0, None))
            m_hours += hours
            bucket = _status_bucket(task.status)
            if bucket == "doing":
                m_doing += 1
            elif bucket == "done":
                m_done += 1
            else:
                m_todo += 1
            items.append(
                TeamDailyTaskItem(
                    task_id=task.id,
                    title=task.title,
                    status=task.status,
                    due_date=task.due_date,
                    project_id=task.project_id,
                    project_name=project.name if project else "",
                    phase_name=phase_by_task.get(task.id),
                    assignee_hours=hours,
                    assignee_note=note,
                )
            )

        job = membership.job_title
        job_label = JOB_TITLE_LABELS_ZH.get(job, job) if job else None
        members_out.append(
            TeamDailyMemberColumn(
                user_id=user.id,
                display_name=user.display_name or user.email or user.clerk_user_id,
                job_title=job,
                job_title_label=job_label,
                task_count=len(items),
                todo_count=m_todo,
                doing_count=m_doing,
                done_count=m_done,
                logged_hours=round(m_hours, 1),
                tasks=items,
            )
        )
        total_tasks += len(items)
        todo_count += m_todo
        doing_count += m_doing
        done_count += m_done
        logged_hours += m_hours

    unassigned_tasks = by_assignee.pop(None, [])
    # Any leftover assignee ids not in memberships (shouldn't happen often)
    for leftover_uid, leftover_tasks in by_assignee.items():
        unassigned_tasks.extend(leftover_tasks)

    unassigned_items: list[TeamDailyTaskItem] = []
    u_todo = u_doing = u_done = 0
    for task in unassigned_tasks:
        project = projects.get(task.project_id)
        bucket = _status_bucket(task.status)
        if bucket == "doing":
            u_doing += 1
        elif bucket == "done":
            u_done += 1
        else:
            u_todo += 1
        unassigned_items.append(
            TeamDailyTaskItem(
                task_id=task.id,
                title=task.title,
                status=task.status,
                due_date=task.due_date,
                project_id=task.project_id,
                project_name=project.name if project else "",
                phase_name=phase_by_task.get(task.id),
                assignee_hours=0.0,
                assignee_note=None,
            )
        )

    total_tasks += len(unassigned_items)
    todo_count += u_todo
    doing_count += u_doing
    done_count += u_done

    return TeamDailyBoardResponse(
        view_date=day,
        team_id=team.id,
        team_name=team.name,
        project_id=project_id,
        member_count=len(members_out),
        task_count=total_tasks,
        todo_count=todo_count,
        doing_count=doing_count,
        done_count=done_count,
        logged_hours=round(logged_hours, 1),
        members=members_out,
        unassigned_tasks=unassigned_items,
    )
