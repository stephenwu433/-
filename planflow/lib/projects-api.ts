/**
 * Call PlanFlow backend project APIs for a team.
 *
 * Beginner flow:
 * 1) Open /teams/{teamId}
 * 2) getToken() → Authorization Bearer
 * 3) GET/POST /teams/{teamId}/projects
 */

import { apiFetch } from "./api-client";

export type Project = {
  id: string;
  team_id: string;
  name: string;
  description: string | null;
  status: string;
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
