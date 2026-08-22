"""Project membership helpers (project-scoped roster + job titles)."""

from __future__ import annotations

import uuid

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import ProjectMember, TeamMember
from app.schemas import JOB_TITLES, JOB_TITLE_LABELS_ZH


def normalize_job_title(raw: str | None) -> str | None:
    if raw is None:
        return None
    value = raw.strip().lower()
    if not value:
        return None
    if value not in JOB_TITLES:
        raise HTTPException(
            status_code=400,
            detail=f"job_title must be one of: {', '.join(JOB_TITLES)}",
        )
    return value


def job_title_label(job: str | None) -> str | None:
    if not job:
        return None
    return JOB_TITLE_LABELS_ZH.get(job, job)


def ensure_project_member(
    db: Session,
    *,
    team_id: uuid.UUID,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    job_title: str | None = None,
) -> ProjectMember:
    """Ensure user is on the project roster (must already be a team member)."""
    team_member = (
        db.query(TeamMember)
        .filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
        .one_or_none()
    )
    if team_member is None:
        raise HTTPException(
            status_code=400,
            detail="user must be a member of this team before joining the project",
        )

    existing = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
        .one_or_none()
    )
    if existing is not None:
        if job_title is not None:
            existing.job_title = job_title
        return existing

    row = ProjectMember(
        team_id=team_id,
        project_id=project_id,
        user_id=user_id,
        job_title=job_title if job_title is not None else team_member.job_title,
    )
    db.add(row)
    return row


def require_project_assignee(
    db: Session,
    *,
    team_id: uuid.UUID,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    """Assignee must be on the project roster (and therefore the team)."""
    member = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
            ProjectMember.team_id == team_id,
        )
        .one_or_none()
    )
    if member is None:
        # Soft fallback: if roster empty, allow any team member (legacy projects mid-migration).
        roster_count = (
            db.query(ProjectMember.id)
            .filter(ProjectMember.project_id == project_id)
            .count()
        )
        if roster_count == 0:
            team_ok = (
                db.query(TeamMember.id)
                .filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
                .first()
            )
            if team_ok is not None:
                return
        raise HTTPException(
            status_code=400,
            detail="assignee_user_id must be a member of this project",
        )


def list_project_job_titles(db: Session, *, project_id: uuid.UUID) -> list[str]:
    rows = (
        db.query(ProjectMember.job_title)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.job_title.is_not(None),
        )
        .order_by(ProjectMember.created_at.asc())
        .all()
    )
    seen: list[str] = []
    for (job,) in rows:
        j = (job or "").strip().lower()
        if j and j not in seen:
            seen.append(j)
    return seen
