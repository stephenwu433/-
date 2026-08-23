"""Project-scoped members (reference MVP: 此项目的成员)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.membership import require_team_membership
from app.models import Project, ProjectMember, User
from app.project_members import (
    ensure_project_member,
    job_title_label,
    normalize_job_title,
)
from app.schemas import (
    ProjectMemberCreateRequest,
    ProjectMemberListResponse,
    ProjectMemberResponse,
    ProjectMemberUpdateRequest,
)

router = APIRouter(
    prefix="/teams/{team_id}/projects/{project_id}/members",
    tags=["project-members"],
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


def _to_response(member: ProjectMember, user: User) -> ProjectMemberResponse:
    return ProjectMemberResponse(
        user_id=user.id,
        clerk_user_id=user.clerk_user_id,
        email=user.email,
        display_name=user.display_name,
        job_title=member.job_title,
        job_title_label=job_title_label(member.job_title),
        joined_at=member.created_at,
    )


@router.get("", response_model=ProjectMemberListResponse)
def list_project_members(
    team_id: uuid.UUID,
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectMemberListResponse:
    require_team_membership(db, team_id=team_id, user=current_user)
    _require_project(db, team_id=team_id, project_id=project_id)

    rows = (
        db.query(ProjectMember, User)
        .join(User, User.id == ProjectMember.user_id)
        .filter(ProjectMember.project_id == project_id)
        .order_by(User.display_name.asc().nulls_last(), User.email.asc().nulls_last())
        .all()
    )
    return ProjectMemberListResponse(
        members=[_to_response(m, u) for m, u in rows]
    )


@router.post("", response_model=ProjectMemberResponse, status_code=status.HTTP_201_CREATED)
def add_project_member(
    team_id: uuid.UUID,
    project_id: uuid.UUID,
    body: ProjectMemberCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectMemberResponse:
    require_team_membership(db, team_id=team_id, user=current_user)
    _require_project(db, team_id=team_id, project_id=project_id)

    job = normalize_job_title(body.job_title)
    member = ensure_project_member(
        db,
        team_id=team_id,
        project_id=project_id,
        user_id=body.user_id,
        job_title=job,
    )
    db.commit()
    db.refresh(member)
    user = db.query(User).filter(User.id == body.user_id).one()
    return _to_response(member, user)


@router.patch("/{user_id}", response_model=ProjectMemberResponse)
def update_project_member(
    team_id: uuid.UUID,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    body: ProjectMemberUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectMemberResponse:
    require_team_membership(db, team_id=team_id, user=current_user)
    _require_project(db, team_id=team_id, project_id=project_id)

    member = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
        .one_or_none()
    )
    if member is None:
        raise HTTPException(status_code=404, detail="Project member not found")

    if body.clear_job_title:
        member.job_title = None
    elif body.job_title is not None:
        member.job_title = normalize_job_title(body.job_title)

    db.commit()
    db.refresh(member)
    user = db.query(User).filter(User.id == user_id).one()
    return _to_response(member, user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_project_member(
    team_id: uuid.UUID,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    require_team_membership(db, team_id=team_id, user=current_user)
    project = _require_project(db, team_id=team_id, project_id=project_id)

    member = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
        .one_or_none()
    )
    if member is None:
        raise HTTPException(status_code=404, detail="Project member not found")

    if project.owner_user_id == user_id:
        raise HTTPException(
            status_code=400,
            detail="Cannot remove the project owner from project members",
        )

    db.delete(member)
    db.commit()
