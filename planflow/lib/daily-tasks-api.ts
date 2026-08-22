/**
 * Daily tasks + time entry (hours logging) API helpers.
 */

import { apiFetch } from "./api-client";
import type { Task } from "./tasks-api";

export type DailyTaskCard = {
  task: Task;
  assignee_display_name: string | null;
  my_hours: number;
  my_note: string | null;
  my_entry_id: string | null;
  total_hours: number;
};

export type DailyTasksResponse = {
  view_date: string;
  project_id: string;
  team_id: string;
  project_name: string;
  task_count: number;
  total_logged_hours: number;
  my_logged_hours: number;
  completion_percent: number;
  day_note: string | null;
  tasks: DailyTaskCard[];
};

export type TimeEntry = {
  id: string;
  team_id: string;
  project_id: string;
  task_id: string;
  user_id: string;
  work_date: string;
  hours: number;
  note: string | null;
  created_at: string;
  updated_at: string;
};

function base(teamId: string, projectId: string) {
  return `/teams/${teamId}/projects/${projectId}`;
}

export function getDailyTasks(
  token: string,
  teamId: string,
  projectId: string,
  viewDate?: string,
) {
  const qs = viewDate ? `?view_date=${encodeURIComponent(viewDate)}` : "";
  return apiFetch<DailyTasksResponse>(
    `${base(teamId, projectId)}/daily-tasks${qs}`,
    token,
  );
}

export function saveDailyFeedback(
  token: string,
  teamId: string,
  projectId: string,
  viewDate: string,
  body: {
    completion_percent: number;
    day_note?: string | null;
    apply_review_status?: boolean;
  },
) {
  const qs = `?view_date=${encodeURIComponent(viewDate)}`;
  return apiFetch<DailyTasksResponse>(
    `${base(teamId, projectId)}/daily-tasks/feedback${qs}`,
    token,
    {
      method: "PUT",
      body: JSON.stringify({
        completion_percent: body.completion_percent,
        day_note: body.day_note?.trim() ? body.day_note.trim() : null,
        apply_review_status: body.apply_review_status ?? true,
      }),
    },
  );
}

export function upsertTimeEntry(
  token: string,
  teamId: string,
  projectId: string,
  taskId: string,
  workDate: string,
  body: { hours: number; note?: string },
) {
  return apiFetch<TimeEntry>(
    `${base(teamId, projectId)}/tasks/${taskId}/time-entries/${workDate}`,
    token,
    {
      method: "PUT",
      body: JSON.stringify({
        hours: body.hours,
        note: body.note?.trim() ? body.note.trim() : null,
      }),
    },
  );
}
