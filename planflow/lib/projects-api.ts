/**
 * Call PlanFlow backend project APIs for a team.
 */

import { apiFetch } from "./api-client";

export type ProjectStatus = "active" | "paused" | "done";

export type Project = {
  id: string;
  team_id: string;
  name: string;
  description: string | null;
  status: ProjectStatus | string;
  planned_start: string | null;
  planned_end: string | null;
  created_at: string;
};

export type ProjectListResponse = {
  projects: Project[];
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
  name: string,
  description?: string,
  plannedStart?: string,
  plannedEnd?: string,
): Promise<Project> {
  return apiFetch<Project>(`/teams/${teamId}/projects`, token, {
    method: "POST",
    body: JSON.stringify({
      name,
      description: description?.trim() ? description.trim() : null,
      planned_start: plannedStart || null,
      planned_end: plannedEnd || null,
    }),
  });
}

export function updateProjectStatus(
  token: string,
  teamId: string,
  projectId: string,
  status: ProjectStatus,
): Promise<Project> {
  return apiFetch<Project>(`/teams/${teamId}/projects/${projectId}`, token, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}

export function updateProjectSchedule(
  token: string,
  teamId: string,
  projectId: string,
  plannedStart: string | null,
  plannedEnd: string | null,
): Promise<Project> {
  if (!plannedStart && !plannedEnd) {
    return apiFetch<Project>(`/teams/${teamId}/projects/${projectId}`, token, {
      method: "PATCH",
      body: JSON.stringify({ clear_schedule: true }),
    });
  }
  return apiFetch<Project>(`/teams/${teamId}/projects/${projectId}`, token, {
    method: "PATCH",
    body: JSON.stringify({
      planned_start: plannedStart,
      planned_end: plannedEnd,
    }),
  });
}
