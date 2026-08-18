"""Project create / list endpoints (MVP).

Beginner map:
  POST /teams/{team_id}/projects  → create a project inside a team you belong to
  GET  /teams/{team_id}/projects  → list that team's projects
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.membership import require_team_membership
from app.models import Project, User
from app.schemas import ProjectCreateRequest, ProjectListResponse, ProjectResponse

router = APIRouter(prefix="/teams/{team_id}/projects", tags=["projects"])


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

    return ProjectResponse(
        id=project.id,
        team_id=project.team_id,
        name=project.name,
        description=project.description,
        status=project.status,
        created_at=project.created_at,
    )


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
    projects = [
        ProjectResponse(
            id=row.id,
            team_id=row.team_id,
            name=row.name,
            description=row.description,
            status=row.status,
            created_at=row.created_at,
        )
        for row in rows
    ]
    return ProjectListResponse(projects=projects)
