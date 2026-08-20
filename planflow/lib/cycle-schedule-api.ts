/**
 * Per-project cycle schedule (phases + work items) API helpers.
 */

import { apiFetch } from "./api-client";

export type WorkItemStatus = "todo" | "doing" | "done";

export type PhaseWorkItem = {
  id: string;
  team_id: string;
  project_id: string;
  phase_id: string;
  title: string;
  assignee_user_id: string | null;
  planned_start: string | null;
  planned_end: string | null;
  estimated_hours: number;
  status: WorkItemStatus | string;
  sort_order: number;
  created_at: string;
};

export type ProjectPhase = {
  id: string;
  team_id: string;
  project_id: string;
  name: string;
  sort_order: number;
  planned_start: string | null;
  planned_end: string | null;
  work_items: PhaseWorkItem[];
  created_at: string;
};

export type CycleSchedule = {
  project_id: string;
  team_id: string;
  project_name: string;
  planned_start: string | null;
  planned_end: string | null;
  member_daily_hours: number;
  owner_user_id: string | null;
  plan_confirmed: boolean;
  total_estimated_hours: number;
  phase_count: number;
  work_item_count: number;
  phases: ProjectPhase[];
};

export type UpdateWorkItemInput = {
  title?: string;
  assignee_user_id?: string | null;
  clear_assignee?: boolean;
  planned_start?: string | null;
  planned_end?: string | null;
  clear_dates?: boolean;
  estimated_hours?: number;
  status?: WorkItemStatus;
};

function base(teamId: string, projectId: string) {
  return `/teams/${teamId}/projects/${projectId}/cycle-schedule`;
}

export function getCycleSchedule(token: string, teamId: string, projectId: string) {
  return apiFetch<CycleSchedule>(base(teamId, projectId), token);
}

export function generateCycleSchedule(
  token: string,
  teamId: string,
  projectId: string,
  replaceExisting = true,
) {
  return apiFetch<CycleSchedule>(`${base(teamId, projectId)}/generate`, token, {
    method: "POST",
    body: JSON.stringify({ replace_existing: replaceExisting, phase_count: 5 }),
  });
}

export function updateWorkItem(
  token: string,
  teamId: string,
  projectId: string,
  itemId: string,
  input: UpdateWorkItemInput,
) {
  return apiFetch<PhaseWorkItem>(
    `${base(teamId, projectId)}/work-items/${itemId}`,
    token,
    {
      method: "PATCH",
      body: JSON.stringify(input),
    },
  );
}

export function confirmCycleSchedule(
  token: string,
  teamId: string,
  projectId: string,
) {
  return apiFetch<CycleSchedule>(`${base(teamId, projectId)}/confirm`, token, {
    method: "POST",
  });
}
