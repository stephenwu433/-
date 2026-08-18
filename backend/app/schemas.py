"""Pydantic request/response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class MeResponse(BaseModel):
    id: uuid.UUID
    clerk_user_id: str
    email: str | None = None
    display_name: str | None = None


class TeamCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class TeamResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    role: str
    created_at: datetime


class TeamListResponse(BaseModel):
    teams: list[TeamResponse]
