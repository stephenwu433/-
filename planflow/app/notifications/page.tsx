"use client";

import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import {
  listNotifications,
  markAllNotificationsRead,
  markNotificationRead,
  type AppNotification,
} from "@/lib/notifications-api";

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

export default function NotificationsPage() {
  const { isLoaded, isSignedIn, getToken } = useAuth();
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
    const payload = await listNotifications(token);
    setItems(payload.notifications);
    setUnreadCount(payload.unread_count);
  }, [getToken]);

  useEffect(() => {
    if (!isLoaded || !isSignedIn) return;
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
  }, [isLoaded, isSignedIn, refresh]);

  async function onMarkAll() {
    setBusy(true);
    setError(null);
    try {
      const token = await getToken();
      if (!token) throw new Error("拿不到登录 token");
      await markAllNotificationsRead(token);
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
      if (!token) return;
      if (item.unread) {
        await markNotificationRead(token, item.id);
        setItems((prev) =>
          prev.map((n) =>
            n.id === item.id
              ? { ...n, unread: false, read_at: new Date().toISOString() }
              : n,
          ),
        );
        setUnreadCount((c) => Math.max(0, c - 1));
      }
    } catch {
      // navigation still ok
    }
  }

  return (
    <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col px-6 py-10">
      <p className="text-sm text-zinc-500">
        <Link href="/portfolio" className="underline hover:text-zinc-800">
          ← 项目总览
        </Link>
      </p>
      <div className="mt-3 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">
            站内提醒
          </h1>
          <p className="mt-2 text-sm leading-6 text-zinc-600">
            周期排期、日报保存、任务指派等事件会出现在这里。未读 {unreadCount} 条。
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
        <div className="mt-8 rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          请先{" "}
          <Link href="/sign-in" className="font-medium underline">
            登录
          </Link>{" "}
          后再查看提醒。
        </div>
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
            <section className="rounded-md border border-dashed border-zinc-300 px-6 py-10 text-center">
              <p className="text-sm font-medium text-zinc-900">暂时没有提醒</p>
              <p className="mt-2 text-sm text-zinc-600">
                生成周期排期、保存日报或指派任务后，提醒会出现在这里。
              </p>
              <Link
                href="/portfolio"
                className="mt-5 inline-block rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800"
              >
                回到项目总览
              </Link>
            </section>
          ) : (
            <ul className="divide-y divide-zinc-200 border-t border-b border-zinc-200">
              {items.map((item) => {
                const content = (
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
                        {content}
                      </Link>
                    ) : (
                      <button
                        type="button"
                        className="block w-full text-left hover:bg-zinc-50"
                        onClick={() => void onOpen(item)}
                      >
                        {content}
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
  );
}
