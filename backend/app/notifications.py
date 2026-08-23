"""Helpers to create in-app notifications for team members."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models import Notification, TeamMember


def notify_team_members(
    db: Session,
    *,
    team_id: uuid.UUID,
    project_id: uuid.UUID | None,
    type: str,
    title: str,
    body: str | None = None,
    category: str = "一般",
    link_path: str | None = None,
    exclude_user_id: uuid.UUID | None = None,
) -> int:
    """Fan-out a notification to all members of a team. Returns created count."""
    member_ids = [
        row[0]
        for row in db.query(TeamMember.user_id).filter(TeamMember.team_id == team_id).all()
    ]
    created = 0
    for user_id in member_ids:
        if exclude_user_id is not None and user_id == exclude_user_id:
            continue
        db.add(
            Notification(
                user_id=user_id,
                team_id=team_id,
                project_id=project_id,
                type=type,
                category=category,
                title=title,
                body=body,
                link_path=link_path,
            )
        )
        created += 1
    return created
