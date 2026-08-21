/**
 * Project daily report API helpers.
 */

import { apiFetch } from "./api-client";

export type DailyReportWorkItem = {
  task_id: string;
  title: string;
  status: string;
  assignee_user_id: string | null;
  assignee_display_name: string | null;
  due_date: string | null;
  logged_hours: number;
  notes: string[];
};

export type DailyReport = {
  view_date: string;
  project_id: string;
  team_id: string;
  project_name: string;
  project_status: string;
  progress_percent: number;
  total_tasks: number;
  done_tasks: number;
  day_task_count: number;
  day_logged_hours: number;
  auto_summary: string;
  summary_text: string | null;
  next_actions: string | null;
  saved: boolean;
  work_items: DailyReportWorkItem[];
};

function base(teamId: string, projectId: string) {
  return `/teams/${teamId}/projects/${projectId}/daily-report`;
}

export function getDailyReport(
  token: string,
  teamId: string,
  projectId: string,
  viewDate?: string,
) {
  const qs = viewDate ? `?view_date=${encodeURIComponent(viewDate)}` : "";
  return apiFetch<DailyReport>(`${base(teamId, projectId)}${qs}`, token);
}

export function saveDailyReport(
  token: string,
  teamId: string,
  projectId: string,
  body: { summary_text?: string; next_actions?: string },
  viewDate?: string,
) {
  const qs = viewDate ? `?view_date=${encodeURIComponent(viewDate)}` : "";
  return apiFetch<DailyReport>(`${base(teamId, projectId)}${qs}`, token, {
    method: "PUT",
    body: JSON.stringify({
      summary_text: body.summary_text?.trim() ? body.summary_text.trim() : null,
      next_actions: body.next_actions?.trim() ? body.next_actions.trim() : null,
    }),
  });
}
