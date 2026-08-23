/**
 * In-app notifications API helpers.
 */

import { apiFetch } from "./api-client";

export type AppNotification = {
  id: string;
  user_id: string;
  team_id: string | null;
  project_id: string | null;
  type: string;
  category: string;
  title: string;
  body: string | null;
  link_path: string | null;
  read_at: string | null;
  created_at: string;
  unread: boolean;
};

export type NotificationListResponse = {
  unread_count: number;
  notifications: AppNotification[];
};

export function listNotifications(token: string, unreadOnly = false) {
  const qs = unreadOnly ? "?unread_only=true" : "";
  return apiFetch<NotificationListResponse>(`/notifications${qs}`, token);
}

export function listProjectNotifications(
  token: string,
  teamId: string,
  projectId: string,
  unreadOnly = false,
) {
  const qs = unreadOnly ? "?unread_only=true" : "";
  return apiFetch<NotificationListResponse>(
    `/teams/${teamId}/projects/${projectId}/notifications${qs}`,
    token,
  );
}

export function getUnreadCount(token: string) {
  return apiFetch<{ unread_count: number }>("/notifications/unread-count", token);
}

export function markAllNotificationsRead(token: string, projectId?: string) {
  const qs = projectId ? `?project_id=${encodeURIComponent(projectId)}` : "";
  return apiFetch<{ unread_count: number }>(
    `/notifications/mark-all-read${qs}`,
    token,
    { method: "POST" },
  );
}

export function markProjectNotificationsRead(
  token: string,
  teamId: string,
  projectId: string,
) {
  return apiFetch<{ unread_count: number }>(
    `/teams/${teamId}/projects/${projectId}/notifications/mark-all-read`,
    token,
    { method: "POST" },
  );
}

export function markNotificationRead(token: string, notificationId: string) {
  return apiFetch<AppNotification>(
    `/notifications/${notificationId}/read`,
    token,
    { method: "POST" },
  );
}
