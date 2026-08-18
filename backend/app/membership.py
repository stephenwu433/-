"""Helpers: check the current user belongs to a team."""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Team, TeamMember, User


def require_team_membership(
    db: Session,
    *,
    team_id: uuid.UUID,
    user: User,
) -> Team:
    """Return the team if the user is a member; otherwise 404/403."""
    team = db.query(Team).filter(Team.id == team_id).one_or_none()
    if team is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )

    membership = (
        db.query(TeamMember)
        .filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user.id,
        )
        .one_or_none()
    )
    if membership is None:
        # Hide existence of teams the user cannot access.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )
    return team
