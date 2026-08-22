/**
 * Cross-project member workload API (day scope).
 */

import { apiFetch } from "./api-client";

export type WorkloadProjectSlice = {
  project_id: string;
  team_id: string;
  project_name: string;
  team_name: string;
  due_task_count: number;
  /** Planned hours for this project on the view day. */
  planned_hours: number;
  logged_hours: number;
  member_daily_hours: number;
};

export type WorkloadMember = {
  user_id: string;
  display_name: string;
  project_count: number;
  due_task_count: number;
  /** Sum of planned hours across projects for the day. */
  planned_hours: number;
  logged_hours: number;
  capacity_hours: number;
  load_ratio: number;
  projects_per_day: number;
  overloaded: boolean;
  /** e.g. 「负荷偏高」/「负荷正常」 */
  load_label: string;
  /** e.g. 「建议调整排期」/「可继续执行」 */
  action_hint: string;
  projects: WorkloadProjectSlice[];
};

export type WorkloadResponse = {
  view_date: string;
  /** @deprecated day scope: equals view_date */
  month_start: string;
  /** @deprecated day scope: equals view_date */
  month_end: string;
  weekday_count: number;
  scope: "day" | string;
  capacity_hours_default?: number;
  member_count: number;
  overloaded_count: number;
  members: WorkloadMember[];
};

export function getWorkload(token: string, viewDate?: string) {
  const qs = viewDate ? `?view_date=${encodeURIComponent(viewDate)}` : "";
  return apiFetch<WorkloadResponse>(`/workload${qs}`, token);
}
