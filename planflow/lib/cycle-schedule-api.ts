/**
 * Per-project cycle schedule (phases + work items) API helpers.
 */

import { apiFetch } from "./api-client";

export type WorkItemStatus = "todo" | "doing" | "done";

export type SeedMode =
  | "from_requirements"
  | "from_tasks"
  | "phases_only"
  | "placeholders";

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
  task_id: string | null;
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
  linked_task_count: number;
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

export type CreateWorkItemInput = {
  title: string;
  assignee_user_id?: string | null;
  planned_start?: string | null;
  planned_end?: string | null;
  estimated_hours?: number;
  status?: WorkItemStatus;
  task_id?: string | null;
};

export type GenerateScheduleInput = {
  replace_existing?: boolean;
  phase_count?: number;
  seed_mode?: SeedMode;
  phase_names?: string[];
  requirements_text?: string | null;
  save_requirements_to_project?: boolean;
  create_tasks?: boolean;
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
  input: GenerateScheduleInput = {},
) {
  return apiFetch<CycleSchedule>(`${base(teamId, projectId)}/generate`, token, {
    method: "POST",
    body: JSON.stringify({
      replace_existing: input.replace_existing ?? true,
      phase_count: input.phase_count ?? 5,
      seed_mode: input.seed_mode ?? "from_requirements",
      phase_names: input.phase_names,
      requirements_text: input.requirements_text ?? null,
      save_requirements_to_project: input.save_requirements_to_project ?? true,
      create_tasks: input.create_tasks ?? true,
    }),
  });
}

export function createPhase(
  token: string,
  teamId: string,
  projectId: string,
  body: {
    name: string;
    planned_start?: string | null;
    planned_end?: string | null;
  },
) {
  return apiFetch<ProjectPhase>(`${base(teamId, projectId)}/phases`, token, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function updatePhase(
  token: string,
  teamId: string,
  projectId: string,
  phaseId: string,
  body: {
    name?: string;
    planned_start?: string | null;
    planned_end?: string | null;
    clear_dates?: boolean;
  },
) {
  return apiFetch<ProjectPhase>(
    `${base(teamId, projectId)}/phases/${phaseId}`,
    token,
    {
      method: "PATCH",
      body: JSON.stringify(body),
    },
  );
}

export async function deletePhase(
  token: string,
  teamId: string,
  projectId: string,
  phaseId: string,
) {
  const { getApiBaseUrl } = await import("./api");
  const res = await fetch(
    `${getApiBaseUrl()}${base(teamId, projectId)}/phases/${phaseId}`,
    {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    },
  );
  if (!res.ok && res.status !== 204) {
    throw new Error(`API ${res.status}: delete phase failed`);
  }
}

export function createWorkItem(
  token: string,
  teamId: string,
  projectId: string,
  phaseId: string,
  input: CreateWorkItemInput,
) {
  return apiFetch<PhaseWorkItem>(
    `${base(teamId, projectId)}/phases/${phaseId}/work-items`,
    token,
    {
      method: "POST",
      body: JSON.stringify(input),
    },
  );
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

export async function deleteWorkItem(
  token: string,
  teamId: string,
  projectId: string,
  itemId: string,
) {
  const { getApiBaseUrl } = await import("./api");
  const res = await fetch(
    `${getApiBaseUrl()}${base(teamId, projectId)}/work-items/${itemId}`,
    {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    },
  );
  if (!res.ok && res.status !== 204) {
    throw new Error(`API ${res.status}: delete work item failed`);
  }
}

export function syncWorkItemToTask(
  token: string,
  teamId: string,
  projectId: string,
  itemId: string,
) {
  return apiFetch<PhaseWorkItem>(
    `${base(teamId, projectId)}/work-items/${itemId}/sync-task`,
    token,
    { method: "POST" },
  );
}

export function importTasksIntoSchedule(
  token: string,
  teamId: string,
  projectId: string,
  phaseId: string,
  taskIds?: string[],
) {
  return apiFetch<CycleSchedule>(`${base(teamId, projectId)}/import-tasks`, token, {
    method: "POST",
    body: JSON.stringify({
      phase_id: phaseId,
      task_ids: taskIds ?? null,
      only_unlinked: true,
    }),
  });
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
