"""Tasks under a project."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.membership import require_team_membership
from app.models import Notification, Project, Task, TeamMember, User
from app.project_members import require_project_assignee
from app.schemas import (
    TASK_STATUSES,
    TaskCreateRequest,
    TaskListResponse,
    TaskResponse,
    TaskUpdateRequest,
)

router = APIRouter(
    prefix="/teams/{team_id}/projects/{project_id}/tasks",
    tags=["tasks"],
)


def _to_response(task: Task) -> TaskResponse:
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


def _require_project(
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
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def _get_task(
    db: Session,
    *,
    team_id: uuid.UUID,
    project_id: uuid.UUID,
    task_id: uuid.UUID,
) -> Task:
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
    return task


def _validate_assignee(
    db: Session,
    *,
    team_id: uuid.UUID,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    require_project_assignee(
        db, team_id=team_id, project_id=project_id, user_id=user_id
    )


@router.get("", response_model=TaskListResponse)
def list_tasks(
    team_id: uuid.UUID,
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskListResponse:
    require_team_membership(db, team_id=team_id, user=current_user)
    _require_project(db, team_id=team_id, project_id=project_id)
    rows = (
        db.query(Task)
        .filter(Task.team_id == team_id, Task.project_id == project_id)
        .order_by(Task.sort_order.asc(), Task.created_at.asc())
        .all()
    )
    return TaskListResponse(tasks=[_to_response(row) for row in rows])


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    team_id: uuid.UUID,
    project_id: uuid.UUID,
    body: TaskCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskResponse:
    require_team_membership(db, team_id=team_id, user=current_user)
    _require_project(db, team_id=team_id, project_id=project_id)

    title = body.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="Task title cannot be empty")

    description = body.description.strip() if body.description else None
    if description == "":
        description = None

    if body.assignee_user_id is not None:
        _validate_assignee(
            db,
            team_id=team_id,
            project_id=project_id,
            user_id=body.assignee_user_id,
        )

    max_order = (
        db.query(Task.sort_order)
        .filter(Task.project_id == project_id)
        .order_by(Task.sort_order.desc())
        .limit(1)
        .scalar()
    )
    next_order = (max_order or 0) + 1

    task = Task(
        team_id=team_id,
        project_id=project_id,
        title=title,
        description=description,
        status="todo",
        assignee_user_id=body.assignee_user_id,
        due_date=body.due_date,
        sort_order=next_order,
        created_by_user_id=current_user.id,
    )
    db.add(task)
    db.flush()
    if (
        body.assignee_user_id is not None
        and body.assignee_user_id != current_user.id
    ):
        db.add(
            Notification(
                user_id=body.assignee_user_id,
                team_id=team_id,
                project_id=project_id,
                type="task_assigned",
                category="任务",
                title="你有新的任务",
                body=f"「{title}」已指派给你。",
                link_path=f"/teams/{team_id}/projects/{project_id}/daily",
            )
        )
    db.commit()
    db.refresh(task)
    return _to_response(task)


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(
    team_id: uuid.UUID,
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    body: TaskUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskResponse:
    require_team_membership(db, team_id=team_id, user=current_user)
    task = _get_task(
        db, team_id=team_id, project_id=project_id, task_id=task_id
    )

    if body.title is not None:
        title = body.title.strip()
        if not title:
            raise HTTPException(status_code=400, detail="Task title cannot be empty")
        task.title = title

    if body.description is not None:
        description = body.description.strip()
        task.description = description or None

    if body.status is not None:
        new_status = body.status.strip().lower()
        if new_status not in TASK_STATUSES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Use one of: {', '.join(TASK_STATUSES)}",
            )
        task.status = new_status

    if body.clear_assignee:
        task.assignee_user_id = None
    elif body.assignee_user_id is not None:
        _validate_assignee(
            db,
            team_id=team_id,
            project_id=project_id,
            user_id=body.assignee_user_id,
        )
        previous = task.assignee_user_id
        task.assignee_user_id = body.assignee_user_id
        if (
            body.assignee_user_id != previous
            and body.assignee_user_id != current_user.id
        ):
            db.add(
                Notification(
                    user_id=body.assignee_user_id,
                    team_id=team_id,
                    project_id=project_id,
                    type="task_assigned",
                    category="任务",
                    title="你有新的任务",
                    body=f"「{task.title}」已指派给你。",
                    link_path=f"/teams/{team_id}/projects/{project_id}/daily",
                )
            )

    if body.clear_due_date:
        task.due_date = None
    elif body.due_date is not None:
        task.due_date = body.due_date

    db.commit()
    db.refresh(task)
    return _to_response(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    team_id: uuid.UUID,
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    require_team_membership(db, team_id=team_id, user=current_user)
    task = _get_task(
        db, team_id=team_id, project_id=project_id, task_id=task_id
    )
    db.delete(task)
    db.commit()
