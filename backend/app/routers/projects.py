"""Project create / list / status endpoints (MVP).

Beginner map:
  POST  /teams/{team_id}/projects              → create
  GET   /teams/{team_id}/projects              → list
  PATCH /teams/{team_id}/projects/{project_id} → update status
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.membership import require_team_membership
from app.models import Project, User
from app.schemas import (
    PROJECT_STATUSES,
    ProjectCreateRequest,
    ProjectListResponse,
    ProjectResponse,
    ProjectStatusUpdateRequest,
)

router = APIRouter(prefix="/teams/{team_id}/projects", tags=["projects"])


def _to_response(project: Project) -> ProjectResponse:
    return ProjectResponse(
        id=project.id,
        team_id=project.team_id,
        name=project.name,
        description=project.description,
        status=project.status,
        created_at=project.created_at,
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

    project = Project(
        team_id=team_id,
        name=name,
        description=description,
        status="active",
        created_by_user_id=current_user.id,
    )
    db.add(project)
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


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project_status(
    team_id: uuid.UUID,
    project_id: uuid.UUID,
    body: ProjectStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectResponse:
    """Change status: active | paused | done."""
    require_team_membership(db, team_id=team_id, user=current_user)
    project = _get_team_project(db, team_id=team_id, project_id=project_id)

    new_status = body.status.strip().lower()
    if new_status not in PROJECT_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Use one of: {', '.join(PROJECT_STATUSES)}",
        )

    project.status = new_status
    db.commit()
    db.refresh(project)
    return _to_response(project)
