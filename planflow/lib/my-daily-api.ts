/**
 * Cross-project "my daily tasks" API helpers.
 */

import { apiFetch } from "./api-client";

export type MyDailyTaskItem = {
  task_id: string;
  title: string;
  status: string;
  due_date: string | null;
  team_id: string;
  team_name: string;
  project_id: string;
  project_name: string;
  phase_name: string | null;
  my_hours: number;
  my_note: string | null;
  my_entry_id: string | null;
};

export type MyDailyTasksResponse = {
  view_date: string;
  task_count: number;
  todo_count: number;
  doing_count: number;
  done_count: number;
  my_logged_hours: number;
  tasks: MyDailyTaskItem[];
};

export function getMyDailyTasks(token: string, viewDate?: string) {
  const qs = viewDate ? `?view_date=${encodeURIComponent(viewDate)}` : "";
  return apiFetch<MyDailyTasksResponse>(`/my-daily-tasks${qs}`, token);
}
