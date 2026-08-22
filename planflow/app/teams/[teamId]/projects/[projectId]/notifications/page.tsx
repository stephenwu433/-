"use client";

import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import {
  listProjectNotifications,
  markNotificationRead,
  markProjectNotificationsRead,
  type AppNotification,
} from "@/lib/notifications-api";
import { listTeamProjects } from "@/lib/projects-api";
import { listMyTeams } from "@/lib/teams-api";
import { WorkbenchShell } from "@/components/WorkbenchShell";

function formatWhen(iso: string) {
  try {
    return new Date(iso).toLocaleString("zh-CN", {
      month: "numeric",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export default function ProjectNotificationsPage() {
  const { isLoaded, isSignedIn, getToken } = useAuth();
  const params = useParams<{ teamId: string; projectId: string }>();
  const teamId = typeof params.teamId === "string" ? params.teamId : "";
  const projectId = typeof params.projectId === "string" ? params.projectId : "";

  const [projectName, setProjectName] = useState("项目");
  const [items, setItems] = useState<AppNotification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setError(null);
    const token = await getToken();
    if (!token) {
      setError("拿不到登录 token。请重新登录。");
      return;
    }
    const teams = await listMyTeams(token);
    if (!teams.teams.some((t) => t.id === teamId)) {
      setError("你不是这个团队的成员。");
      return;
    }
    const [projects, payload] = await Promise.all([
      listTeamProjects(token, teamId),
      listProjectNotifications(token, teamId, projectId),
    ]);
    const matched = projects.projects.find((p) => p.id === projectId);
    if (matched) setProjectName(matched.name);
    setItems(payload.notifications);
    setUnreadCount(payload.unread_count);
  }, [getToken, teamId, projectId]);

  useEffect(() => {
    if (!isLoaded || !isSignedIn || !teamId || !projectId) return;
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        await refresh();
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : String(err));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [isLoaded, isSignedIn, teamId, projectId, refresh]);

  async function onMarkAll() {
    setBusy(true);
    try {
      const token = await getToken();
      if (!token) throw new Error("拿不到登录 token");
      await markProjectNotificationsRead(token, teamId, projectId);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function onOpen(item: AppNotification) {
    try {
      const token = await getToken();
      if (!token || !item.unread) return;
      await markNotificationRead(token, item.id);
      setItems((prev) =>
        prev.map((n) =>
          n.id === item.id
            ? { ...n, unread: false, read_at: new Date().toISOString() }
            : n,
        ),
      );
      setUnreadCount((c) => Math.max(0, c - 1));
    } catch {
      // ignore
    }
  }

  return (
    <WorkbenchShell
      teamId={teamId}
      projectId={projectId}
      projectName={projectName}
    >
    <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col px-6 py-10">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">
            {projectName} · 站内提醒
          </h1>
          <p className="mt-2 text-sm text-zinc-600">
            仅显示与当前项目相关的提醒。未读 {unreadCount} 条。
          </p>
        </div>
        {isSignedIn ? (
          <button
            type="button"
            disabled={busy || unreadCount === 0}
            onClick={() => void onMarkAll()}
            className="rounded-md border border-zinc-300 px-3 py-1.5 text-sm text-zinc-800 hover:bg-zinc-50 disabled:opacity-50"
          >
            {busy ? "处理中…" : "全部标为已读"}
          </button>
        ) : null}
      </div>

      {!isLoaded ? (
        <p className="mt-8 text-sm text-zinc-500">确认登录…</p>
      ) : !isSignedIn ? (
        <p className="mt-8 text-sm text-amber-800">
          请先{" "}
          <Link href="/sign-in" className="underline">
            登录
          </Link>
          。
        </p>
      ) : (
        <div className="mt-8 space-y-4">
          {error ? (
            <p className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
              {error}
            </p>
          ) : null}
          {loading ? (
            <p className="text-sm text-zinc-500">加载提醒…</p>
          ) : items.length === 0 ? (
            <p className="rounded-md border border-dashed border-zinc-300 px-4 py-8 text-center text-sm text-zinc-500">
              暂时没有本项目提醒。
            </p>
          ) : (
            <ul className="divide-y divide-zinc-200 border-t border-b border-zinc-200">
              {items.map((item) => {
                const row = (
                  <div className="flex items-start justify-between gap-3 py-4">
                    <div className="min-w-0">
                      <p
                        className={`text-sm ${item.unread ? "font-semibold text-zinc-900" : "font-medium text-zinc-800"}`}
                      >
                        {item.unread ? "● " : ""}
                        {item.title}
                      </p>
                      {item.body ? (
                        <p className="mt-1 text-sm text-zinc-600">{item.body}</p>
                      ) : null}
                      <p className="mt-1 text-xs text-zinc-400">
                        {formatWhen(item.created_at)}
                      </p>
                    </div>
                    <span className="shrink-0 rounded bg-zinc-100 px-2 py-0.5 text-xs text-zinc-600">
                      {item.category}
                    </span>
                  </div>
                );
                return (
                  <li key={item.id}>
                    {item.link_path ? (
                      <Link
                        href={item.link_path}
                        onClick={() => void onOpen(item)}
                        className="block hover:bg-zinc-50"
                      >
                        {row}
                      </Link>
                    ) : (
                      <button
                        type="button"
                        className="block w-full text-left hover:bg-zinc-50"
                        onClick={() => void onOpen(item)}
                      >
                        {row}
                      </button>
                    )}
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      )}
    </main>
    </WorkbenchShell>
  );
}
