"""Cross-project member workload for the current user's teams."""

from __future__ import annotations

import calendar
import uuid
from collections import defaultdict
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models import Project, Task, TaskTimeEntry, Team, TeamMember, User
from app.schemas import WorkloadMemberCard, WorkloadProjectSlice, WorkloadResponse

router = APIRouter(tags=["workload"])


def _month_bounds(day: date) -> tuple[date, date, int]:
    last = calendar.monthrange(day.year, day.month)[1]
    start = date(day.year, day.month, 1)
    end = date(day.year, day.month, last)
    weekdays = sum(
        1
        for d in range(1, last + 1)
        if date(day.year, day.month, d).weekday() < 5
    )
    return start, end, weekdays


@router.get("/workload", response_model=WorkloadResponse)
def get_workload(
    view_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkloadResponse:
    """Aggregate due tasks + logged hours by member across my teams (month scope)."""
    day = view_date or date.today()
    month_start, month_end, weekday_count = _month_bounds(day)

    team_ids = [
        row[0]
        for row in db.query(TeamMember.team_id)
        .filter(TeamMember.user_id == current_user.id)
        .all()
    ]
    if not team_ids:
        return WorkloadResponse(
            view_date=day,
            month_start=month_start,
            month_end=month_end,
            weekday_count=weekday_count,
            member_count=0,
            overloaded_count=0,
            members=[],
        )

    # Members visible in my teams
    memberships = (
        db.query(TeamMember, User, Team)
        .join(User, User.id == TeamMember.user_id)
        .join(Team, Team.id == TeamMember.team_id)
        .filter(TeamMember.team_id.in_(team_ids))
        .all()
    )
    # user_id -> display
    display: dict[uuid.UUID, str] = {}
    for _m, user, _team in memberships:
        display[user.id] = user.display_name or user.email or user.clerk_user_id

    projects = {
        p.id: p
        for p in db.query(Project).filter(Project.team_id.in_(team_ids)).all()
    }
    teams = {
        t.id: t
        for t in db.query(Team).filter(Team.id.in_(team_ids)).all()
    }

    # Due tasks in month (assigned, not done)
    due_tasks = (
        db.query(Task)
        .filter(
            Task.team_id.in_(team_ids),
            Task.due_date.is_not(None),
            Task.due_date >= month_start,
            Task.due_date <= month_end,
            Task.assignee_user_id.is_not(None),
            Task.status != "done",
        )
        .all()
    )

    # Time entries in month
    entries = (
        db.query(TaskTimeEntry)
        .filter(
            TaskTimeEntry.team_id.in_(team_ids),
            TaskTimeEntry.work_date >= month_start,
            TaskTimeEntry.work_date <= month_end,
        )
        .all()
    )

    # Accumulate per user / project
    # key: (user_id, project_id) -> {due, hours}
    slice_due: dict[tuple[uuid.UUID, uuid.UUID], int] = defaultdict(int)
    slice_hours: dict[tuple[uuid.UUID, uuid.UUID], float] = defaultdict(float)
    user_ids: set[uuid.UUID] = set()

    for task in due_tasks:
        uid = task.assignee_user_id
        if uid is None:
            continue
        user_ids.add(uid)
        slice_due[(uid, task.project_id)] += 1

    for entry in entries:
        user_ids.add(entry.user_id)
        slice_hours[(entry.user_id, entry.project_id)] += float(entry.hours or 0)

    cards: list[WorkloadMemberCard] = []
    for uid in sorted(user_ids, key=lambda x: display.get(x, str(x))):
        project_ids = {
            pid
            for (u, pid), n in slice_due.items()
            if u == uid and n > 0
        } | {
            pid
            for (u, pid), h in slice_hours.items()
            if u == uid and h > 0
        }
        if not project_ids:
            continue

        slices: list[WorkloadProjectSlice] = []
        due_total = 0
        hours_total = 0.0
        daily_caps: list[float] = []
        for pid in sorted(project_ids, key=lambda p: projects[p].name if p in projects else str(p)):
            project = projects.get(pid)
            if project is None:
                continue
            team = teams.get(project.team_id)
            due_n = int(slice_due.get((uid, pid), 0))
            hours_n = float(slice_hours.get((uid, pid), 0.0))
            daily = float(project.member_daily_hours or 6.0)
            daily_caps.append(daily)
            due_total += due_n
            hours_total += hours_n
            slices.append(
                WorkloadProjectSlice(
                    project_id=project.id,
                    team_id=project.team_id,
                    project_name=project.name,
                    team_name=team.name if team else "",
                    due_task_count=due_n,
                    logged_hours=round(hours_n, 1),
                    member_daily_hours=daily,
                )
            )

        avg_daily = sum(daily_caps) / len(daily_caps) if daily_caps else 6.0
        capacity = round(avg_daily * max(weekday_count, 1), 1)
        if capacity > 0 and hours_total > 0:
            load_ratio = round(hours_total / capacity, 2)
        elif weekday_count > 0:
            # fallback: open due-tasks vs ~1 per weekday baseline
            load_ratio = round(due_total / max(weekday_count, 1), 2)
        else:
            load_ratio = 0.0

        # open due-tasks per weekday as a concurrency signal
        projects_per_day = round(due_total / max(weekday_count, 1), 2)
        overloaded = load_ratio >= 1.0 or due_total >= 10 or projects_per_day >= 1.5

        cards.append(
            WorkloadMemberCard(
                user_id=uid,
                display_name=display.get(uid, str(uid)[:8]),
                project_count=len(project_ids),
                due_task_count=due_total,
                logged_hours=round(hours_total, 1),
                capacity_hours=capacity,
                load_ratio=load_ratio,
                projects_per_day=projects_per_day,
                overloaded=overloaded,
                projects=slices,
            )
        )

    cards.sort(key=lambda c: (-c.load_ratio, -c.due_task_count, c.display_name))
    overloaded_count = sum(1 for c in cards if c.overloaded)

    return WorkloadResponse(
        view_date=day,
        month_start=month_start,
        month_end=month_end,
        weekday_count=weekday_count,
        member_count=len(cards),
        overloaded_count=overloaded_count,
        members=cards,
    )
