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
    objective: str | None = Field(default=None, max_length=4000)
    planned_start: date | None = None
    planned_end: date | None = None
    owner_user_id: uuid.UUID | None = None
    member_daily_hours: float = Field(default=6.0, ge=0, le=24)


class ProjectResponse(BaseModel):
    id: uuid.UUID
    team_id: uuid.UUID
    name: str
    description: str | None = None
    objective: str | None = None
    status: str
    planned_start: date | None = None
    planned_end: date | None = None
    owner_user_id: uuid.UUID | None = None
    member_daily_hours: float = 6.0
    plan_confirmed: bool = False
    created_at: datetime


class ProjectListResponse(BaseModel):
    projects: list[ProjectResponse]


PROJECT_STATUSES = ("active", "paused", "done")


class ProjectUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    objective: str | None = Field(default=None, max_length=4000)
    status: str | None = Field(default=None, max_length=20)
    planned_start: date | None = None
    planned_end: date | None = None
    clear_schedule: bool = False
    owner_user_id: uuid.UUID | None = None
    clear_owner: bool = False
    member_daily_hours: float | None = Field(default=None, ge=0, le=24)
    plan_confirmed: bool | None = None


class ScheduleResponse(BaseModel):
    projects: list[ProjectResponse]


class PortfolioProjectCard(BaseModel):
    id: uuid.UUID
    team_id: uuid.UUID
    team_name: str
    name: str
    description: str | None = None
    objective: str | None = None
    status: str
    planned_start: date | None = None
    planned_end: date | None = None
    owner_user_id: uuid.UUID | None = None
    owner_display_name: str | None = None
    member_daily_hours: float = 6.0
    plan_confirmed: bool = False
    member_count: int = 0
    task_count: int = 0
    done_task_count: int = 0
    progress_percent: int = 0
    day_task_count: int = 0
    created_at: datetime


class PortfolioStats(BaseModel):
    active_projects: int
    total_tasks: int
    day_tasks: int
    day_task_hours_estimate: float
    high_load_members: int


class PortfolioResponse(BaseModel):
    view_date: date
    stats: PortfolioStats
    projects: list[PortfolioProjectCard]


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


PHASE_WORK_ITEM_STATUSES = ("todo", "doing", "done")

DEFAULT_PHASE_NAMES = (
    "项目启动与目标确认",
    "方案与示范高保真",
    "核心技术与后端",
    "优化全过程体验",
    "驻场上线与维护",
)


class PhaseWorkItemResponse(BaseModel):
    id: uuid.UUID
    team_id: uuid.UUID
    project_id: uuid.UUID
    phase_id: uuid.UUID
    title: str
    assignee_user_id: uuid.UUID | None = None
    planned_start: date | None = None
    planned_end: date | None = None
    estimated_hours: float = 0.0
    status: str
    sort_order: int
    created_at: datetime


class PhaseWorkItemUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    assignee_user_id: uuid.UUID | None = None
    clear_assignee: bool = False
    planned_start: date | None = None
    planned_end: date | None = None
    clear_dates: bool = False
    estimated_hours: float | None = Field(default=None, ge=0, le=1000)
    status: str | None = Field(default=None, max_length=20)


class ProjectPhaseResponse(BaseModel):
    id: uuid.UUID
    team_id: uuid.UUID
    project_id: uuid.UUID
    name: str
    sort_order: int
    planned_start: date | None = None
    planned_end: date | None = None
    work_items: list[PhaseWorkItemResponse] = Field(default_factory=list)
    created_at: datetime


class ProjectPhaseUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    planned_start: date | None = None
    planned_end: date | None = None
    clear_dates: bool = False


class ProjectCycleScheduleResponse(BaseModel):
    project_id: uuid.UUID
    team_id: uuid.UUID
    project_name: str
    planned_start: date | None = None
    planned_end: date | None = None
    member_daily_hours: float = 6.0
    owner_user_id: uuid.UUID | None = None
    plan_confirmed: bool = False
    total_estimated_hours: float = 0.0
    phase_count: int = 0
    work_item_count: int = 0
    phases: list[ProjectPhaseResponse] = Field(default_factory=list)


class GenerateCycleScheduleRequest(BaseModel):
    replace_existing: bool = True
    phase_count: int = Field(default=5, ge=2, le=8)

