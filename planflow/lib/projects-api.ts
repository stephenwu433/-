/**
 * Call PlanFlow backend project APIs for a team.
 *
 * Beginner flow:
 * 1) Open /teams/{teamId}
 * 2) getToken() → Authorization Bearer
 * 3) GET/POST /teams/{teamId}/projects
 */

import { apiFetch } from "./api-client";

export type ProjectStatus = "active" | "paused" | "done";

export type Project = {
  id: string;
  team_id: string;
  name: string;
  description: string | null;
  status: ProjectStatus | string;
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
): Promise<Project> {
  return apiFetch<Project>(`/teams/${teamId}/projects`, token, {
    method: "POST",
    body: JSON.stringify({
      name,
      description: description?.trim() ? description.trim() : null,
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
