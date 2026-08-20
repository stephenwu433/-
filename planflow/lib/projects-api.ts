/**
 * Call PlanFlow backend project APIs for a team / portfolio.
 */

import { apiFetch } from "./api-client";

export type ProjectStatus = "active" | "paused" | "done";

export type Project = {
  id: string;
  team_id: string;
  name: string;
  description: string | null;
  objective: string | null;
  status: ProjectStatus | string;
  planned_start: string | null;
  planned_end: string | null;
  owner_user_id: string | null;
  member_daily_hours: number;
  plan_confirmed: boolean;
  created_at: string;
};

export type ProjectListResponse = {
  projects: Project[];
};

export type CreateProjectInput = {
  name: string;
  description?: string;
  objective?: string;
  planned_start?: string;
  planned_end?: string;
  owner_user_id?: string;
  member_daily_hours?: number;
};

export type UpdateProjectInput = {
  name?: string;
  description?: string | null;
  objective?: string | null;
  status?: ProjectStatus;
  planned_start?: string | null;
  planned_end?: string | null;
  clear_schedule?: boolean;
  owner_user_id?: string | null;
  clear_owner?: boolean;
  member_daily_hours?: number;
  plan_confirmed?: boolean;
};

export type PortfolioStats = {
  active_projects: number;
  total_tasks: number;
  day_tasks: number;
  day_task_hours_estimate: number;
  high_load_members: number;
};

export type PortfolioProject = {
  id: string;
  team_id: string;
  team_name: string;
  name: string;
  description: string | null;
  objective: string | null;
  status: ProjectStatus | string;
  planned_start: string | null;
  planned_end: string | null;
  owner_user_id: string | null;
  owner_display_name: string | null;
  member_daily_hours: number;
  plan_confirmed: boolean;
  member_count: number;
  task_count: number;
  done_task_count: number;
  progress_percent: number;
  day_task_count: number;
  created_at: string;
};

export type PortfolioResponse = {
  view_date: string;
  stats: PortfolioStats;
  projects: PortfolioProject[];
};

export function listTeamProjects(
  token: string,
  teamId: string,
): Promise<ProjectListResponse> {
  return apiFetch<ProjectListResponse>(`/teams/${teamId}/projects`, token);
}

export function createProject(
  token: string,
  teamId: string,
  input: CreateProjectInput | string,
  description?: string,
  plannedStart?: string,
  plannedEnd?: string,
): Promise<Project> {
  // Back-compat: createProject(token, teamId, name, description?, start?, end?)
  const body: CreateProjectInput =
    typeof input === "string"
      ? {
          name: input,
          description,
          planned_start: plannedStart,
          planned_end: plannedEnd,
        }
      : input;

  return apiFetch<Project>(`/teams/${teamId}/projects`, token, {
    method: "POST",
    body: JSON.stringify({
      name: body.name,
      description: body.description?.trim() ? body.description.trim() : null,
      objective: body.objective?.trim() ? body.objective.trim() : null,
      planned_start: body.planned_start || null,
      planned_end: body.planned_end || null,
      owner_user_id: body.owner_user_id || null,
      member_daily_hours: body.member_daily_hours ?? 6,
    }),
  });
}

export function updateProject(
  token: string,
  teamId: string,
  projectId: string,
  input: UpdateProjectInput,
): Promise<Project> {
  return apiFetch<Project>(`/teams/${teamId}/projects/${projectId}`, token, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export function updateProjectStatus(
  token: string,
  teamId: string,
  projectId: string,
  status: ProjectStatus,
): Promise<Project> {
  return updateProject(token, teamId, projectId, { status });
}

export function updateProjectSchedule(
  token: string,
  teamId: string,
  projectId: string,
  plannedStart: string | null,
  plannedEnd: string | null,
): Promise<Project> {
  if (!plannedStart && !plannedEnd) {
    return updateProject(token, teamId, projectId, { clear_schedule: true });
  }
  return updateProject(token, teamId, projectId, {
    planned_start: plannedStart,
    planned_end: plannedEnd,
  });
}

export function getPortfolio(
  token: string,
  viewDate?: string,
): Promise<PortfolioResponse> {
  const qs = viewDate ? `?view_date=${encodeURIComponent(viewDate)}` : "";
  return apiFetch<PortfolioResponse>(`/portfolio${qs}`, token);
}
