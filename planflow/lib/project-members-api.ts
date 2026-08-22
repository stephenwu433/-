/**
 * Project-scoped members API (此项目的成员).
 */

import { apiFetch } from "./api-client";
import type { JobTitle } from "./members-api";

export type ProjectMember = {
  user_id: string;
  clerk_user_id: string;
  email: string | null;
  display_name: string | null;
  job_title: JobTitle | string | null;
  job_title_label: string | null;
  joined_at: string;
};

function base(teamId: string, projectId: string) {
  return `/teams/${teamId}/projects/${projectId}/members`;
}

export function listProjectMembers(
  token: string,
  teamId: string,
  projectId: string,
) {
  return apiFetch<{ members: ProjectMember[] }>(
    base(teamId, projectId),
    token,
  );
}

export function addProjectMember(
  token: string,
  teamId: string,
  projectId: string,
  body: { user_id: string; job_title?: string | null },
) {
  return apiFetch<ProjectMember>(base(teamId, projectId), token, {
    method: "POST",
    body: JSON.stringify({
      user_id: body.user_id,
      job_title: body.job_title || null,
    }),
  });
}

export function updateProjectMember(
  token: string,
  teamId: string,
  projectId: string,
  userId: string,
  body: { job_title?: string | null; clear_job_title?: boolean },
) {
  return apiFetch<ProjectMember>(
    `${base(teamId, projectId)}/${userId}`,
    token,
    {
      method: "PATCH",
      body: JSON.stringify(
        body.clear_job_title
          ? { clear_job_title: true }
          : { job_title: body.job_title || null },
      ),
    },
  );
}

export async function removeProjectMember(
  token: string,
  teamId: string,
  projectId: string,
  userId: string,
) {
  const { getApiBaseUrl } = await import("./api");
  const res = await fetch(
    `${getApiBaseUrl()}${base(teamId, projectId)}/${userId}`,
    {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    },
  );
  if (!res.ok && res.status !== 204) {
    throw new Error(`API ${res.status}: remove project member failed`);
  }
}
