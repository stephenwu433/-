/**
 * Call PlanFlow backend team APIs.
 *
 * Beginner flow:
 * 1) Clerk login → getToken()
 * 2) Send Authorization: Bearer <token>
 * 3) Create / list teams
 */

import { getApiBaseUrl } from "./api";

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

async function apiFetch<T>(
  path: string,
  token: string,
  init?: RequestInit,
): Promise<T> {
  const res = await fetch(`${getApiBaseUrl()}${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = (await res.json()) as { detail?: unknown };
      if (typeof body.detail === "string") {
        detail = body.detail;
      } else if (body.detail != null) {
        detail = JSON.stringify(body.detail);
      }
    } catch {
      // keep statusText
    }
    throw new Error(`API ${res.status}: ${detail}`);
  }

  return (await res.json()) as T;
}

export function listMyTeams(token: string): Promise<TeamListResponse> {
  return apiFetch<TeamListResponse>("/teams", token);
}

export function createTeam(
  token: string,
  name: string,
): Promise<Team> {
  return apiFetch<Team>("/teams", token, {
    method: "POST",
    body: JSON.stringify({ name }),
  });
}
