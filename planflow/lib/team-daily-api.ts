/**
 * Team daily board API helpers.
 */

import { apiFetch } from "./api-client";

export type TeamDailyTaskItem = {
  task_id: string;
  title: string;
  status: string;
  due_date: string | null;
  project_id: string;
  project_name: string;
  phase_name: string | null;
  assignee_hours: number;
  assignee_note: string | null;
};

export type TeamDailyMemberColumn = {
  user_id: string;
  display_name: string;
  job_title: string | null;
  job_title_label: string | null;
  task_count: number;
  todo_count: number;
  doing_count: number;
  done_count: number;
  logged_hours: number;
  tasks: TeamDailyTaskItem[];
};

export type TeamDailyBoardResponse = {
  view_date: string;
  team_id: string;
  team_name: string;
  project_id: string | null;
  member_count: number;
  task_count: number;
  todo_count: number;
  doing_count: number;
  done_count: number;
  logged_hours: number;
  members: TeamDailyMemberColumn[];
  unassigned_tasks: TeamDailyTaskItem[];
};

export function getTeamDailyBoard(
  token: string,
  teamId: string,
  opts?: { viewDate?: string; projectId?: string },
) {
  const params = new URLSearchParams();
  if (opts?.viewDate) params.set("view_date", opts.viewDate);
  if (opts?.projectId) params.set("project_id", opts.projectId);
  const qs = params.toString() ? `?${params.toString()}` : "";
  return apiFetch<TeamDailyBoardResponse>(
    `/teams/${teamId}/team-daily${qs}`,
    token,
  );
}
