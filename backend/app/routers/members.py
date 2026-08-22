"""Team members + invite links."""

from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.membership import require_team_manager, require_team_membership
from app.models import Team, TeamInvite, TeamMember, User
from app.schemas import (
    InviteCreateRequest,
    InviteListResponse,
    InvitePreviewResponse,
    InviteResponse,
    JOB_TITLES,
    TeamMemberListResponse,
    TeamMemberResponse,
    TeamMemberUpdateRequest,
)

members_router = APIRouter(prefix="/teams/{team_id}", tags=["members"])
invites_router = APIRouter(tags=["invites"])


def _invite_response(invite: TeamInvite, team_name: str) -> InviteResponse:
    return InviteResponse(
        id=invite.id,
        team_id=invite.team_id,
        team_name=team_name,
        token=invite.token,
        invite_path=f"/invites/{invite.token}",
        email=invite.email,
        role=invite.role,
        status=invite.status,
        expires_at=invite.expires_at,
        created_at=invite.created_at,
    )


@members_router.get("/members", response_model=TeamMemberListResponse)
def list_members(
    team_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TeamMemberListResponse:
    require_team_membership(db, team_id=team_id, user=current_user)
    rows = (
        db.query(TeamMember, User)
        .join(User, User.id == TeamMember.user_id)
        .filter(TeamMember.team_id == team_id)
        .order_by(TeamMember.created_at.asc())
        .all()
    )
    members = [
        TeamMemberResponse(
            user_id=user.id,
            clerk_user_id=user.clerk_user_id,
            email=user.email,
            display_name=user.display_name,
            role=member.role,
            job_title=member.job_title,
            joined_at=member.created_at,
        )
        for member, user in rows
    ]
    return TeamMemberListResponse(members=members)


@members_router.patch("/members/{user_id}", response_model=TeamMemberResponse)
def update_member(
    team_id: uuid.UUID,
    user_id: uuid.UUID,
    body: TeamMemberUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TeamMemberResponse:
    """Update a member's job position (岗位). Managers or the member themselves."""
    _team, membership = require_team_membership(db, team_id=team_id, user=current_user)
    is_manager = membership.role in {"owner", "admin"}
    if not is_manager and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Only managers can edit other members")

    row = (
        db.query(TeamMember, User)
        .join(User, User.id == TeamMember.user_id)
        .filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
        .one_or_none()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Member not found")
    member, user = row

    if body.clear_job_title:
        member.job_title = None
    elif body.job_title is not None:
        job = body.job_title.strip().lower()
        if job == "":
            member.job_title = None
        elif job not in JOB_TITLES:
            raise HTTPException(
                status_code=400,
                detail=f"job_title must be one of: {', '.join(JOB_TITLES)}",
            )
        else:
            member.job_title = job

    db.commit()
    return TeamMemberResponse(
        user_id=user.id,
        clerk_user_id=user.clerk_user_id,
        email=user.email,
        display_name=user.display_name,
        role=member.role,
        job_title=member.job_title,
        joined_at=member.created_at,
    )


@members_router.post(
    "/invites",
    response_model=InviteResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_invite(
    team_id: uuid.UUID,
    body: InviteCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InviteResponse:
    team, _membership = require_team_manager(db, team_id=team_id, user=current_user)

    role = (body.role or "member").strip().lower()
    if role not in {"admin", "member"}:
        raise HTTPException(status_code=400, detail="role must be admin or member")

    email = body.email.strip().lower() if body.email else None
    if email == "":
        email = None

    invite = TeamInvite(
        team_id=team.id,
        token=secrets.token_urlsafe(24),
        email=email,
        role=role,
        status="pending",
        invited_by_user_id=current_user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=body.expires_in_days),
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return _invite_response(invite, team.name)


@members_router.get("/invites", response_model=InviteListResponse)
def list_invites(
    team_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InviteListResponse:
    team, _membership = require_team_manager(db, team_id=team_id, user=current_user)
    rows = (
        db.query(TeamInvite)
        .filter(TeamInvite.team_id == team_id)
        .order_by(TeamInvite.created_at.desc())
        .all()
    )
    return InviteListResponse(
        invites=[_invite_response(row, team.name) for row in rows]
    )


def _get_invite_or_404(db: Session, token: str) -> tuple[TeamInvite, Team]:
    invite = (
        db.query(TeamInvite).filter(TeamInvite.token == token).one_or_none()
    )
    if invite is None:
        raise HTTPException(status_code=404, detail="Invite not found")
    team = db.query(Team).filter(Team.id == invite.team_id).one_or_none()
    if team is None:
        raise HTTPException(status_code=404, detail="Invite not found")
    return invite, team


@invites_router.get("/invites/{token}", response_model=InvitePreviewResponse)
def preview_invite(
    token: str,
    db: Session = Depends(get_db),
) -> InvitePreviewResponse:
    """Anyone with the link can preview (no login required)."""
    invite, team = _get_invite_or_404(db, token)
    now = datetime.now(timezone.utc)
    expired = invite.expires_at <= now or invite.status != "pending"
    return InvitePreviewResponse(
        team_id=team.id,
        team_name=team.name,
        role=invite.role,
        status=invite.status,
        email=invite.email,
        expires_at=invite.expires_at,
        expired=expired,
    )


@invites_router.post("/invites/{token}/accept", response_model=TeamMemberResponse)
def accept_invite(
    token: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TeamMemberResponse:
    invite, team = _get_invite_or_404(db, token)
    now = datetime.now(timezone.utc)

    if invite.status != "pending":
        raise HTTPException(status_code=400, detail="Invite is no longer pending")
    if invite.expires_at <= now:
        invite.status = "revoked"
        db.commit()
        raise HTTPException(status_code=400, detail="Invite has expired")

    existing = (
        db.query(TeamMember)
        .filter(
            TeamMember.team_id == team.id,
            TeamMember.user_id == current_user.id,
        )
        .one_or_none()
    )
    if existing is not None:
        invite.status = "accepted"
        invite.accepted_by_user_id = current_user.id
        invite.accepted_at = now
        db.commit()
        return TeamMemberResponse(
            user_id=current_user.id,
            clerk_user_id=current_user.clerk_user_id,
            email=current_user.email,
            display_name=current_user.display_name,
            role=existing.role,
            job_title=existing.job_title,
            joined_at=existing.created_at,
        )

    membership = TeamMember(
        team_id=team.id,
        user_id=current_user.id,
        role=invite.role,
    )
    invite.status = "accepted"
    invite.accepted_by_user_id = current_user.id
    invite.accepted_at = now
    db.add(membership)
    db.commit()
    db.refresh(membership)

    return TeamMemberResponse(
        user_id=current_user.id,
        clerk_user_id=current_user.clerk_user_id,
        email=current_user.email,
        display_name=current_user.display_name,
        role=membership.role,
        job_title=membership.job_title,
        joined_at=membership.created_at,
    )
