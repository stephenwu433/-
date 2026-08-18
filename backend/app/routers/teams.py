"""Team create / list endpoints (MVP)."""

from __future__ import annotations

import re
import secrets
import unicodedata

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models import Team, TeamMember, User
from app.schemas import TeamCreateRequest, TeamListResponse, TeamResponse

router = APIRouter(prefix="/teams", tags=["teams"])


def slugify(name: str) -> str:
    """Turn a team name into a URL-safe slug (ASCII-ish)."""
    normalized = unicodedata.normalize("NFKD", name)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_only).strip("-").lower()
    if not slug:
        slug = "team"
    return slug[:48]


def unique_slug(db: Session, name: str) -> str:
    base = slugify(name)
    candidate = base
    # Retry a few times with a short suffix on collision.
    for _ in range(8):
        exists = db.query(Team.id).filter(Team.slug == candidate).first()
        if exists is None:
            return candidate
        candidate = f"{base}-{secrets.token_hex(2)}"
    return f"{base}-{secrets.token_hex(4)}"


@router.post("", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
def create_team(
    body: TeamCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TeamResponse:
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Team name cannot be empty")

    team = Team(
        name=name,
        slug=unique_slug(db, name),
        created_by_user_id=current_user.id,
    )
    db.add(team)
    db.flush()

    membership = TeamMember(
        team_id=team.id,
        user_id=current_user.id,
        role="owner",
    )
    db.add(membership)
    db.commit()
    db.refresh(team)

    return TeamResponse(
        id=team.id,
        name=team.name,
        slug=team.slug,
        role="owner",
        created_at=team.created_at,
    )


@router.get("", response_model=TeamListResponse)
def list_my_teams(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TeamListResponse:
    rows = (
        db.query(Team, TeamMember.role)
        .join(TeamMember, TeamMember.team_id == Team.id)
        .filter(TeamMember.user_id == current_user.id)
        .order_by(Team.created_at.desc())
        .all()
    )
    teams = [
        TeamResponse(
            id=team.id,
            name=team.name,
            slug=team.slug,
            role=role,
            created_at=team.created_at,
        )
        for team, role in rows
    ]
    return TeamListResponse(teams=teams)
