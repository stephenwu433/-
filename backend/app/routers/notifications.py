"""In-app notification list / mark-read endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.membership import require_team_membership
from app.models import Notification, Project, User
from app.schemas import (
    NotificationListResponse,
    NotificationResponse,
    NotificationUnreadCountResponse,
)

router = APIRouter(tags=["notifications"])
project_router = APIRouter(
    prefix="/teams/{team_id}/projects/{project_id}/notifications",
    tags=["notifications"],
)


def _to_response(row: Notification) -> NotificationResponse:
    return NotificationResponse(
        id=row.id,
        user_id=row.user_id,
        team_id=row.team_id,
        project_id=row.project_id,
        type=row.type,
        category=row.category,
        title=row.title,
        body=row.body,
        link_path=row.link_path,
        read_at=row.read_at,
        created_at=row.created_at,
        unread=row.read_at is None,
    )


def _list_for_user(
    db: Session,
    *,
    user_id: uuid.UUID,
    project_id: uuid.UUID | None = None,
    unread_only: bool = False,
    limit: int = 50,
) -> NotificationListResponse:
    query = db.query(Notification).filter(Notification.user_id == user_id)
    if project_id is not None:
        query = query.filter(Notification.project_id == project_id)
    if unread_only:
        query = query.filter(Notification.read_at.is_(None))

    unread_q = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.read_at.is_(None),
    )
    if project_id is not None:
        unread_q = unread_q.filter(Notification.project_id == project_id)
    unread_count = unread_q.count()

    rows = (
        query.order_by(Notification.created_at.desc())
        .limit(max(1, min(limit, 100)))
        .all()
    )
    return NotificationListResponse(
        unread_count=unread_count,
        notifications=[_to_response(row) for row in rows],
    )


@router.get("/notifications", response_model=NotificationListResponse)
def list_notifications(
    unread_only: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationListResponse:
    return _list_for_user(
        db,
        user_id=current_user.id,
        unread_only=unread_only,
        limit=limit,
    )


@router.get("/notifications/unread-count", response_model=NotificationUnreadCountResponse)
def unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationUnreadCountResponse:
    count = (
        db.query(Notification)
        .filter(
            Notification.user_id == current_user.id,
            Notification.read_at.is_(None),
        )
        .count()
    )
    return NotificationUnreadCountResponse(unread_count=count)


@router.post("/notifications/mark-all-read", response_model=NotificationUnreadCountResponse)
def mark_all_read(
    project_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationUnreadCountResponse:
    now = datetime.now(timezone.utc)
    query = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.read_at.is_(None),
    )
    if project_id is not None:
        query = query.filter(Notification.project_id == project_id)
    query.update({Notification.read_at: now}, synchronize_session=False)
    db.commit()
    return NotificationUnreadCountResponse(unread_count=0)


@router.post(
    "/notifications/{notification_id}/read",
    response_model=NotificationResponse,
)
def mark_one_read(
    notification_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationResponse:
    row = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
        .one_or_none()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    if row.read_at is None:
        row.read_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(row)
    return _to_response(row)


@project_router.get("", response_model=NotificationListResponse)
def list_project_notifications(
    team_id: uuid.UUID,
    project_id: uuid.UUID,
    unread_only: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationListResponse:
    require_team_membership(db, team_id=team_id, user=current_user)
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.team_id == team_id)
        .one_or_none()
    )
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return _list_for_user(
        db,
        user_id=current_user.id,
        project_id=project_id,
        unread_only=unread_only,
        limit=limit,
    )


@project_router.post("/mark-all-read", response_model=NotificationUnreadCountResponse)
def mark_project_all_read(
    team_id: uuid.UUID,
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationUnreadCountResponse:
    require_team_membership(db, team_id=team_id, user=current_user)
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.team_id == team_id)
        .one_or_none()
    )
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    now = datetime.now(timezone.utc)
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.project_id == project_id,
        Notification.read_at.is_(None),
    ).update({Notification.read_at: now}, synchronize_session=False)
    db.commit()
    return NotificationUnreadCountResponse(unread_count=0)
