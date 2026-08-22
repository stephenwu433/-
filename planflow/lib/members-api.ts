/**
 * Members, invites, and schedule API helpers.
 */

import { apiFetch } from "./api-client";
import type { Project } from "./projects-api";

export type JobTitle =
  | "project_manager"
  | "pm"
  | "designer"
  | "ops"
  | "other";

export const JOB_TITLE_LABELS: Record<JobTitle, string> = {
  project_manager: "项目经理",
  pm: "产品经理",
  designer: "设计师",
  ops: "运营",
  other: "其他",
};

export type TeamMember = {
  user_id: string;
  clerk_user_id: string;
  email: string | null;
  display_name: string | null;
  role: string;
  job_title: JobTitle | string | null;
  joined_at: string;
};

export type Invite = {
  id: string;
  team_id: string;
  team_name: string;
  token: string;
  invite_path: string;
  email: string | null;
  role: string;
  status: string;
  expires_at: string;
  created_at: string;
};

export type InvitePreview = {
  team_id: string;
  team_name: string;
  role: string;
  status: string;
  email: string | null;
  expires_at: string;
  expired: boolean;
};

export function listMembers(token: string, teamId: string) {
  return apiFetch<{ members: TeamMember[] }>(`/teams/${teamId}/members`, token);
}

export function updateMemberJobTitle(
  token: string,
  teamId: string,
  userId: string,
  jobTitle: string | null,
) {
  return apiFetch<TeamMember>(`/teams/${teamId}/members/${userId}`, token, {
    method: "PATCH",
    body: JSON.stringify(
      jobTitle
        ? { job_title: jobTitle }
        : { clear_job_title: true },
    ),
  });
}

export function createInvite(
  token: string,
  teamId: string,
  body: { email?: string; role?: string } = {},
) {
  return apiFetch<Invite>(`/teams/${teamId}/invites`, token, {
    method: "POST",
    body: JSON.stringify({
      email: body.email || null,
      role: body.role || "member",
      expires_in_days: 7,
    }),
  });
}

export function listInvites(token: string, teamId: string) {
  return apiFetch<{ invites: Invite[] }>(`/teams/${teamId}/invites`, token);
}

export async function previewInvite(tokenPath: string): Promise<InvitePreview> {
  const { getApiBaseUrl } = await import("./api");
  const res = await fetch(`${getApiBaseUrl()}/invites/${tokenPath}`);
  if (!res.ok) {
    throw new Error(`API ${res.status}: invite preview failed`);
  }
  return (await res.json()) as InvitePreview;
}

export function acceptInvite(token: string, inviteToken: string) {
  return apiFetch<TeamMember>(`/invites/${inviteToken}/accept`, token, {
    method: "POST",
  });
}

export function listSchedule(token: string, teamId: string) {
  return apiFetch<{ projects: Project[] }>(`/teams/${teamId}/schedule`, token);
}
