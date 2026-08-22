"use client";

import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { upsertTimeEntry } from "@/lib/daily-tasks-api";
import {
  getMyDailyTasks,
  type MyDailyTaskItem,
  type MyDailyTasksResponse,
} from "@/lib/my-daily-api";
import { updateTask } from "@/lib/tasks-api";

const STATUS_LABELS: Record<string, string> = {
  todo: "待办",
  doing: "进行中",
  done: "已完成",
};

function todayIso() {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function formatCnDate(iso: string) {
  const [y, m, d] = iso.split("-");
  if (!y || !m || !d) return iso;
  return `${y}年${Number(m)}月${Number(d)}日`;
}

export default function MyDailyPage() {
  const { isLoaded, isSignedIn, getToken } = useAuth();
  const [viewDate, setViewDate] = useState(todayIso);
  const [data, setData] = useState<MyDailyTasksResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyTaskId, setBusyTaskId] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setError(null);
    const token = await getToken();
    if (!token) {
      setError("拿不到登录 token。请重新登录。");
      return;
    }
    const payload = await getMyDailyTasks(token, viewDate);
    setData(payload);
  }, [getToken, viewDate]);

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

  async function onStatus(item: MyDailyTaskItem, status: string) {
    setBusyTaskId(item.task_id);
    setError(null);
    try {
      const token = await getToken();
      if (!token) throw new Error("拿不到登录 token");
      await updateTask(token, item.team_id, item.project_id, item.task_id, {
        status,
      });
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusyTaskId(null);
    }
  }

  async function onSaveHours(item: MyDailyTaskItem, hoursRaw: string, note: string) {
    const hours = Number(hoursRaw);
    if (!Number.isFinite(hours) || hours < 0 || hours > 24) {
      setError("工时需在 0–24 之间。");
      return;
    }
    setBusyTaskId(item.task_id);
    setError(null);
    try {
      const token = await getToken();
      if (!token) throw new Error("拿不到登录 token");
      await upsertTimeEntry(
        token,
        item.team_id,
        item.project_id,
        item.task_id,
        viewDate,
        { hours, note },
      );
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusyTaskId(null);
    }
  }

  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col px-6 py-10">
      <p className="text-sm text-zinc-500">
        <Link href="/portfolio" className="underline hover:text-zinc-800">
          ← 项目总览
        </Link>
        {" · "}
        <Link href="/workload" className="underline hover:text-zinc-800">
          跨项目负荷
        </Link>
      </p>
      <p className="mt-3 text-xs font-medium uppercase tracking-[0.16em] text-zinc-500">
        My Day
      </p>
      <h1 className="mt-1 text-2xl font-semibold tracking-tight text-zinc-900">
        我的今日任务
      </h1>
      <p className="mt-2 text-sm leading-6 text-zinc-600">
        汇总所有项目里指派给你、且排在当天的任务。可直接改状态、填工时。
      </p>

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
        <div className="mt-8 space-y-6">
          <div className="flex flex-wrap items-end gap-3">
            <label className="text-sm text-zinc-700">
              日期
              <input
                type="date"
                value={viewDate}
                onChange={(e) => setViewDate(e.target.value)}
                className="mt-1 block rounded-md border border-zinc-300 px-3 py-2 text-sm"
              />
            </label>
            <button
              type="button"
              onClick={() => setViewDate(todayIso())}
              className="rounded-md border border-zinc-300 px-3 py-2 text-sm text-zinc-700 hover:bg-zinc-50"
            >
              回到今天
            </button>
          </div>

          {error ? (
            <p className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
              {error}
            </p>
          ) : null}

          {loading ? (
            <p className="text-sm text-zinc-500">加载今日任务…</p>
          ) : data ? (
            <>
              <section className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                <Summary label="日期" value={formatCnDate(data.view_date)} />
                <Summary label="任务数" value={String(data.task_count)} />
                <Summary
                  label="待办 / 进行中"
                  value={`${data.todo_count} / ${data.doing_count}`}
                />
                <Summary label="我已填工时" value={`${data.my_logged_hours}h`} />
              </section>

              {data.tasks.length === 0 ? (
                <section className="rounded-md border border-dashed border-zinc-300 px-6 py-10 text-center">
                  <p className="text-sm font-medium text-zinc-900">这一天没有指派给你的任务</p>
                  <p className="mt-2 text-sm text-zinc-600">
                    可先在项目排期里「按岗位分派每人每日任务」，或打开某项目的每日任务页添加。
                  </p>
                  <div className="mt-5 flex flex-wrap justify-center gap-3">
                    <Link
                      href="/portfolio"
                      className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800"
                    >
                      去项目总览
                    </Link>
                  </div>
                </section>
              ) : (
                <ul className="space-y-4">
                  {data.tasks.map((item) => (
                    <TaskCard
                      key={item.task_id}
                      item={item}
                      busy={busyTaskId === item.task_id}
                      onStatus={(status) => void onStatus(item, status)}
                      onSaveHours={(hours, note) => void onSaveHours(item, hours, note)}
                    />
                  ))}
                </ul>
              )}
            </>
          ) : null}
        </div>
      )}
    </main>
  );
}

function Summary({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-zinc-200 bg-zinc-50 px-3 py-3">
      <p className="text-xs text-zinc-500">{label}</p>
      <p className="mt-1 text-sm font-semibold text-zinc-900">{value}</p>
    </div>
  );
}

function TaskCard({
  item,
  busy,
  onStatus,
  onSaveHours,
}: {
  item: MyDailyTaskItem;
  busy: boolean;
  onStatus: (status: string) => void;
  onSaveHours: (hours: string, note: string) => void;
}) {
  const [hours, setHours] = useState(String(item.my_hours || ""));
  const [note, setNote] = useState(item.my_note || "");
  const status =
    item.status === "doing" || item.status === "done" ? item.status : "todo";

  useEffect(() => {
    setHours(String(item.my_hours || ""));
    setNote(item.my_note || "");
  }, [item.my_hours, item.my_note, item.task_id]);

  return (
    <li className="rounded-md border border-zinc-200 px-4 py-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-zinc-900">{item.title}</p>
          <p className="mt-1 text-xs text-zinc-500">
            {item.team_name} · {item.project_name}
            {item.phase_name ? ` · ${item.phase_name}` : ""}
          </p>
        </div>
        <Link
          href={`/teams/${item.team_id}/projects/${item.project_id}/daily`}
          className="text-xs text-zinc-600 underline hover:text-zinc-900"
        >
          项目每日任务
        </Link>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <label className="text-xs text-zinc-500">
          状态
          <select
            value={status}
            disabled={busy}
            onChange={(e) => onStatus(e.target.value)}
            className="ml-2 rounded-md border border-zinc-300 px-2 py-1.5 text-sm"
          >
            <option value="todo">{STATUS_LABELS.todo}</option>
            <option value="doing">{STATUS_LABELS.doing}</option>
            <option value="done">{STATUS_LABELS.done}</option>
          </select>
        </label>
      </div>

      <div className="mt-3 flex flex-wrap items-end gap-2">
        <label className="text-xs text-zinc-500">
          今日工时
          <input
            type="number"
            min={0}
            max={24}
            step={0.5}
            value={hours}
            disabled={busy}
            onChange={(e) => setHours(e.target.value)}
            className="mt-1 block w-24 rounded-md border border-zinc-300 px-2 py-1.5 text-sm"
          />
        </label>
        <label className="min-w-[180px] flex-1 text-xs text-zinc-500">
          备注
          <input
            value={note}
            disabled={busy}
            onChange={(e) => setNote(e.target.value)}
            placeholder="可选"
            className="mt-1 block w-full rounded-md border border-zinc-300 px-2 py-1.5 text-sm"
          />
        </label>
        <button
          type="button"
          disabled={busy}
          onClick={() => onSaveHours(hours, note)}
          className="rounded-md bg-zinc-900 px-3 py-2 text-xs font-medium text-white hover:bg-zinc-800 disabled:opacity-50"
        >
          {busy ? "保存中…" : "保存工时"}
        </button>
      </div>
    </li>
  );
}
