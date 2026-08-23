/**
 * Call PlanFlow backend team APIs.
 *
 * Beginner flow:
 * 1) Clerk login → getToken()
 * 2) Send Authorization: Bearer <token>
 * 3) Create / list teams
 */

import { apiFetch } from "./api-client";

export type Team = {
  id: string;
  name: string;
  slug: string;
  role: string;
  created_at: string;
};

export type TeamListResponse = {
  teams: Team[];
};

export function listMyTeams(token: string): Promise<TeamListResponse> {
  return apiFetch<TeamListResponse>("/teams", token);
}

export function createTeam(token: string, name: string): Promise<Team> {
  return apiFetch<Team>("/teams", token, {
    method: "POST",
    body: JSON.stringify({ name }),
  });
}
