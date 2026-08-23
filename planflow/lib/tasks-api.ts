/**
 * Project task APIs.
 */

import { apiFetch } from "./api-client";

export type TaskStatus = "todo" | "doing" | "review" | "done" | "returned";

export const STATUS_LABELS: Record<TaskStatus, string> = {
  todo: "未开始",
  doing: "进行中",
  review: "待验收",
  done: "已完成",
  returned: "已退回",
};

export const TASK_STATUSES: TaskStatus[] = [
  "todo",
  "doing",
  "review",
  "done",
  "returned",
];

export type Task = {
  id: string;
  team_id: string;
  project_id: string;
  title: string;
  description: string | null;
  status: TaskStatus | string;
  assignee_user_id: string | null;
  due_date: string | null;
  sort_order: number;
  /** Estimated / planned hours for this task. */
  estimated_hours: number;
  created_at: string;
};

export function listTasks(token: string, teamId: string, projectId: string) {
  return apiFetch<{ tasks: Task[] }>(
    `/teams/${teamId}/projects/${projectId}/tasks`,
    token,
  );
}

export function createTask(
  token: string,
  teamId: string,
  projectId: string,
  body: {
    title: string;
    description?: string;
    due_date?: string;
    assignee_user_id?: string;
  },
) {
  return apiFetch<Task>(`/teams/${teamId}/projects/${projectId}/tasks`, token, {
    method: "POST",
    body: JSON.stringify({
      title: body.title,
      description: body.description || null,
      due_date: body.due_date || null,
      assignee_user_id: body.assignee_user_id || null,
    }),
  });
}

export function updateTask(
  token: string,
  teamId: string,
  projectId: string,
  taskId: string,
  body: Record<string, unknown>,
) {
  return apiFetch<Task>(
    `/teams/${teamId}/projects/${projectId}/tasks/${taskId}`,
    token,
    {
      method: "PATCH",
      body: JSON.stringify(body),
    },
  );
}

export async function deleteTask(
  token: string,
  teamId: string,
  projectId: string,
  taskId: string,
) {
  const { getApiBaseUrl } = await import("./api");
  const res = await fetch(
    `${getApiBaseUrl()}/teams/${teamId}/projects/${projectId}/tasks/${taskId}`,
    {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    },
  );
  if (!res.ok && res.status !== 204) {
    throw new Error(`API ${res.status}: delete task failed`);
  }
}
