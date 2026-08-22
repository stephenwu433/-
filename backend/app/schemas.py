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
    job_title: str | None = None
    joined_at: datetime


class TeamMemberListResponse(BaseModel):
    members: list[TeamMemberResponse]


JOB_TITLES = (
    "pm",
    "designer",
    "frontend",
    "backend",
    "fullstack",
    "qa",
    "ops",
)


class TeamMemberUpdateRequest(BaseModel):
    job_title: str | None = Field(default=None, max_length=40)
    clear_job_title: bool = False


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


class TimeEntryUpsertRequest(BaseModel):
    hours: float = Field(ge=0, le=24)
    note: str | None = Field(default=None, max_length=2000)


class TimeEntryResponse(BaseModel):
    id: uuid.UUID
    team_id: uuid.UUID
    project_id: uuid.UUID
    task_id: uuid.UUID
    user_id: uuid.UUID
    work_date: date
    hours: float
    note: str | None = None
    created_at: datetime
    updated_at: datetime


class DailyTaskCard(BaseModel):
    task: TaskResponse
    assignee_display_name: str | None = None
    my_hours: float = 0.0
    my_note: str | None = None
    my_entry_id: uuid.UUID | None = None
    total_hours: float = 0.0


class DailyTasksResponse(BaseModel):
    view_date: date
    project_id: uuid.UUID
    team_id: uuid.UUID
    project_name: str
    task_count: int
    total_logged_hours: float
    my_logged_hours: float
    tasks: list[DailyTaskCard]


class WorkloadProjectSlice(BaseModel):
    project_id: uuid.UUID
    team_id: uuid.UUID
    project_name: str
    team_name: str
    due_task_count: int = 0
    logged_hours: float = 0.0
    member_daily_hours: float = 6.0


class WorkloadMemberCard(BaseModel):
    user_id: uuid.UUID
    display_name: str
    project_count: int
    due_task_count: int
    logged_hours: float
    capacity_hours: float
    load_ratio: float
    projects_per_day: float
    overloaded: bool
    projects: list[WorkloadProjectSlice] = Field(default_factory=list)


class WorkloadResponse(BaseModel):
    view_date: date
    month_start: date
    month_end: date
    weekday_count: int
    member_count: int
    overloaded_count: int
    members: list[WorkloadMemberCard]


PHASE_WORK_ITEM_STATUSES = ("todo", "doing", "done")

DEFAULT_PHASE_NAMES = (
    "项目启动与目标确认",
    "方案与示范高保真",
    "核心技术与后端",
    "优化全过程体验",
    "驻场上线与维护",
)

# Full-cycle phases used when generating a plan from written requirements.
REQUIREMENT_CYCLE_PHASE_NAMES = (
    "需求澄清与目标确认",
    "方案设计",
    "开发实现",
    "联调验收",
    "交付复盘",
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
    task_id: uuid.UUID | None = None
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


class PhaseWorkItemCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    assignee_user_id: uuid.UUID | None = None
    planned_start: date | None = None
    planned_end: date | None = None
    estimated_hours: float = Field(default=0.0, ge=0, le=1000)
    status: str = Field(default="todo", max_length=20)
    task_id: uuid.UUID | None = None


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


class ProjectPhaseCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    planned_start: date | None = None
    planned_end: date | None = None
    sort_order: int | None = Field(default=None, ge=0, le=1000)


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
    linked_task_count: int = 0
    phases: list[ProjectPhaseResponse] = Field(default_factory=list)


class GenerateCycleScheduleRequest(BaseModel):
    replace_existing: bool = True
    phase_count: int = Field(default=5, ge=1, le=12)
    # from_requirements: build full-cycle plan from requirement text (recommended)
    # from_tasks / phases_only / placeholders: legacy modes
    seed_mode: str = Field(default="from_requirements", max_length=40)
    phase_names: list[str] | None = None
    # Free-text requirements (one item per line). Falls back to project.objective.
    requirements_text: str | None = Field(default=None, max_length=8000)
    # Persist requirements_text onto project.objective when generating.
    save_requirements_to_project: bool = True
    # Also create real Task rows linked to each generated work item.
    create_tasks: bool = True


class ImportTasksRequest(BaseModel):
    phase_id: uuid.UUID
    task_ids: list[uuid.UUID] | None = None
    only_unlinked: bool = True


class ExpandDailyScheduleRequest(BaseModel):
    """Pack phase work items onto concrete calendar days (for 每日任务)."""

    weekdays_only: bool = True
    # If true, also create/update linked Task.due_date for each packed day.
    create_tasks: bool = True
    # Shrink each work item's planned_start/end to the assigned day.
    pin_work_item_dates: bool = True
    mark_confirmed: bool = False
    # Assign each item to a person by team member job_title (岗位).
    assign_by_job: bool = True


class DailyPlanAssignment(BaseModel):
    work_item_id: uuid.UUID
    task_id: uuid.UUID | None = None
    phase_id: uuid.UUID
    phase_name: str
    title: str
    assignee_user_id: uuid.UUID | None = None
    assignee_job_title: str | None = None
    planned_hours: float = 0.0
    status: str = "todo"
    matched_job: str | None = None


class DailyPlanDay(BaseModel):
    date: date
    phase_id: uuid.UUID | None = None
    phase_name: str | None = None
    total_planned_hours: float = 0.0
    assignments: list[DailyPlanAssignment] = Field(default_factory=list)


class DailyPlanResponse(BaseModel):
    project_id: uuid.UUID
    team_id: uuid.UUID
    project_name: str
    planned_start: date | None = None
    planned_end: date | None = None
    member_daily_hours: float = 6.0
    weekdays_only: bool = True
    assigned_work_item_count: int = 0
    created_task_count: int = 0
    updated_task_count: int = 0
    day_count: int = 0
    days: list[DailyPlanDay] = Field(default_factory=list)
    # Full schedule snapshot after expand (optional convenience for UI refresh)
    schedule: ProjectCycleScheduleResponse | None = None


class DailyReportWorkItem(BaseModel):
    task_id: uuid.UUID
    title: str
    status: str
    assignee_user_id: uuid.UUID | None = None
    assignee_display_name: str | None = None
    due_date: date | None = None
    logged_hours: float = 0.0
    notes: list[str] = Field(default_factory=list)


class DailyReportSaveRequest(BaseModel):
    summary_text: str | None = Field(default=None, max_length=4000)
    next_actions: str | None = Field(default=None, max_length=4000)


class DailyReportResponse(BaseModel):
    view_date: date
    project_id: uuid.UUID
    team_id: uuid.UUID
    project_name: str
    project_status: str
    progress_percent: int
    total_tasks: int
    done_tasks: int
    day_task_count: int
    day_logged_hours: float
    auto_summary: str
    summary_text: str | None = None
    next_actions: str | None = None
    saved: bool = False
    work_items: list[DailyReportWorkItem] = Field(default_factory=list)


class NotificationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    team_id: uuid.UUID | None = None
    project_id: uuid.UUID | None = None
    type: str
    category: str
    title: str
    body: str | None = None
    link_path: str | None = None
    read_at: datetime | None = None
    created_at: datetime
    unread: bool = True


class NotificationListResponse(BaseModel):
    unread_count: int
    notifications: list[NotificationResponse]


class NotificationUnreadCountResponse(BaseModel):
    unread_count: int



