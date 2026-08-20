"""Pydantic request/response schemas."""

from __future__ import annotations

import uuid
from datetime import date, datetime

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


class TeamMemberResponse(BaseModel):
    user_id: uuid.UUID
    clerk_user_id: str
    email: str | None = None
    display_name: str | None = None
    role: str
    joined_at: datetime


class TeamMemberListResponse(BaseModel):
    members: list[TeamMemberResponse]


class InviteCreateRequest(BaseModel):
    email: str | None = Field(default=None, max_length=200)
    role: str = Field(default="member", max_length=20)
    expires_in_days: int = Field(default=7, ge=1, le=30)


class InviteResponse(BaseModel):
    id: uuid.UUID
    team_id: uuid.UUID
    team_name: str
    token: str
    invite_path: str
    email: str | None = None
    role: str
    status: str
    expires_at: datetime
    created_at: datetime


class InviteListResponse(BaseModel):
    invites: list[InviteResponse]


class InvitePreviewResponse(BaseModel):
    team_id: uuid.UUID
    team_name: str
    role: str
    status: str
    email: str | None = None
    expires_at: datetime
    expired: bool


class ProjectCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    planned_start: date | None = None
    planned_end: date | None = None


class ProjectResponse(BaseModel):
    id: uuid.UUID
    team_id: uuid.UUID
    name: str
    description: str | None = None
    status: str
    planned_start: date | None = None
    planned_end: date | None = None
    created_at: datetime


class ProjectListResponse(BaseModel):
    projects: list[ProjectResponse]


PROJECT_STATUSES = ("active", "paused", "done")


class ProjectUpdateRequest(BaseModel):
    status: str | None = Field(default=None, max_length=20)
    planned_start: date | None = None
    planned_end: date | None = None
    clear_schedule: bool = False


class ScheduleResponse(BaseModel):
    projects: list[ProjectResponse]


TASK_STATUSES = ("todo", "doing", "done")


class TaskCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    assignee_user_id: uuid.UUID | None = None
    due_date: date | None = None


class TaskUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    status: str | None = Field(default=None, max_length=20)
    assignee_user_id: uuid.UUID | None = None
    clear_assignee: bool = False
    due_date: date | None = None
    clear_due_date: bool = False


class TaskResponse(BaseModel):
    id: uuid.UUID
    team_id: uuid.UUID
    project_id: uuid.UUID
    title: str
    description: str | None = None
    status: str
    assignee_user_id: uuid.UUID | None = None
    due_date: date | None = None
    sort_order: int
    created_at: datetime


class TaskListResponse(BaseModel):
    tasks: list[TaskResponse]
