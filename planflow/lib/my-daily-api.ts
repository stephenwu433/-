/**
 * Cross-project "my daily tasks" API helpers.
 */

import { apiFetch } from "./api-client";

export type MyDailyBucket = "overdue" | "today" | "later";

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
  estimated_hours: number;
  my_hours: number;
  my_note: string | null;
  my_entry_id: string | null;
  my_completion_percent: number;
  bucket: MyDailyBucket | string;
};

export type MyDailyTasksResponse = {
  view_date: string;
  task_count: number;
  todo_count: number;
  doing_count: number;
  review_count: number;
  done_count: number;
  returned_count: number;
  overdue_count: number;
  today_count: number;
  later_count: number;
  my_logged_hours: number;
  planned_hours: number;
  capacity_hours: number;
  tasks: MyDailyTaskItem[];
};

export function getMyDailyTasks(token: string, viewDate?: string) {
  const qs = viewDate ? `?view_date=${encodeURIComponent(viewDate)}` : "";
  return apiFetch<MyDailyTasksResponse>(`/my-daily-tasks${qs}`, token);
}
