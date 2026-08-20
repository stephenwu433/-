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


class ProjectCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)


class ProjectResponse(BaseModel):
    id: uuid.UUID
    team_id: uuid.UUID
    name: str
    description: str | None = None
    status: str
    created_at: datetime


class ProjectListResponse(BaseModel):
    projects: list[ProjectResponse]


PROJECT_STATUSES = ("active", "paused", "done")


class ProjectStatusUpdateRequest(BaseModel):
    status: str = Field(min_length=1, max_length=20)
