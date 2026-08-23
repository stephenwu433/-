"use client";

import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { useParams } from "next/navigation";
import { FormEvent, useCallback, useEffect, useState } from "react";

import { WorkbenchShell } from "@/components/WorkbenchShell";
import {
  getDailyTasks,
  upsertTimeEntry,
  type DailyTaskCard,
  type DailyTasksResponse,
} from "@/lib/daily-tasks-api";
import { createTask, STATUS_LABELS, type TaskStatus } from "@/lib/tasks-api";
import { listMyTeams } from "@/lib/teams-api";

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
  return `${Number(m)}月${Number(d)}日`;
}

export default function DailyTasksPage() {
  const { isLoaded, isSignedIn, getToken } = useAuth();
  const params = useParams<{ teamId: string; projectId: string }>();
  const teamId = typeof params.teamId === "string" ? params.teamId : "";
  const projectId = typeof params.projectId === "string" ? params.projectId : "";

  const [viewDate, setViewDate] = useState(todayIso);
  const [data, setData] = useState<DailyTasksResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [savingTaskId, setSavingTaskId] = useState<string | null>(null);
  const [newTitle, setNewTitle] = useState("");
  const [creating, setCreating] = useState(false);

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
      setData(null);
      return;
    }
    const payload = await getDailyTasks(token, teamId, projectId, viewDate);
    setData(payload);
  }, [getToken, teamId, projectId, viewDate]);

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

  async function onCreateForDay(e: FormEvent) {
    e.preventDefault();
    const title = newTitle.trim();
    if (!title) return;
    setCreating(true);
    setError(null);
    try {
      const token = await getToken();
      if (!token) throw new Error("拿不到登录 token");
      await createTask(token, teamId, projectId, {
        title,
        due_date: viewDate,
      });
      setNewTitle("");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setCreating(false);
    }
  }

  async function onSaveTask(
    card: DailyTaskCard,
    hoursRaw: string,
    note: string,
    completionPercent: number,
  ) {
    const hours = Number(hoursRaw);
    if (!Number.isFinite(hours) || hours < 0 || hours > 24) {
      setError("工时需在 0–24 之间。");
      return;
    }
    const pct = Math.min(100, Math.max(0, Math.round(completionPercent)));
    setSavingTaskId(card.task.id);
    setError(null);
    try {
      const token = await getToken();
      if (!token) throw new Error("拿不到登录 token");
      await upsertTimeEntry(token, teamId, projectId, card.task.id, viewDate, {
        hours,
        note,
        completion_percent: pct,
        apply_review_status: pct >= 100,
      });
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSavingTaskId(null);
    }
  }

  return (
    <WorkbenchShell
      teamId={teamId}
      projectId={projectId}
      projectName={data?.project_name}
    >
      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col px-6 py-10">
        <p className="text-xs font-medium uppercase tracking-[0.16em] text-zinc-500">
          Daily Tasks · Current Project
        </p>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight text-zinc-900">
          {data?.project_name || "项目"} · 每日任务
        </h1>
        <p className="mt-2 text-sm leading-6 text-zinc-600">
          按任务填写完成度、当日实际工时与进展说明。完成度到 100% 时任务将进入「待验收」。
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
          <div className="mt-8 space-y-8">
            <div className="flex flex-wrap items-end justify-between gap-3">
              <label className="flex flex-col gap-1 text-xs text-zinc-500">
                查看日期
                <input
                  type="date"
                  value={viewDate}
                  onChange={(e) => setViewDate(e.target.value)}
                  className="rounded-md border border-zinc-300 px-3 py-2 text-sm text-zinc-900"
                />
              </label>
              {data ? (
                <p className="text-sm text-zinc-600">
                  {formatCnDate(data.view_date)} · 当日已填{" "}
                  <span className="font-semibold text-zinc-900">
                    {data.my_logged_hours}h
                  </span>
                  （合计 {data.total_logged_hours}h）
                </p>
              ) : null}
            </div>

            <form onSubmit={onCreateForDay} className="flex flex-col gap-3 sm:flex-row">
              <input
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                placeholder={`为 ${formatCnDate(viewDate)} 添加任务`}
                maxLength={200}
                className="min-w-0 flex-1 rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500"
              />
              <button
                type="submit"
                disabled={creating || !newTitle.trim()}
                className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 disabled:opacity-50"
              >
                {creating ? "添加中…" : "添加当日任务"}
              </button>
            </form>

            {error ? (
              <p className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
                {error}
              </p>
            ) : null}

            {loading ? (
              <p className="text-sm text-zinc-500">加载每日任务…</p>
            ) : !data || data.tasks.length === 0 ? (
              <p className="rounded-md border border-dashed border-zinc-300 px-4 py-8 text-center text-sm text-zinc-500">
                这一天还没有任务。可以在上面添加，或在项目任务页给任务设置截止日期。
              </p>
            ) : (
              <ul className="space-y-4">
                {data.tasks.map((card) => (
                  <DailyTaskRow
                    key={card.task.id}
                    card={card}
                    saving={savingTaskId === card.task.id}
                    onSave={onSaveTask}
                  />
                ))}
              </ul>
            )}
          </div>
        )}
      </main>
    </WorkbenchShell>
  );
}

function DailyTaskRow({
  card,
  saving,
  onSave,
}: {
  card: DailyTaskCard;
  saving: boolean;
  onSave: (
    card: DailyTaskCard,
    hours: string,
    note: string,
    completionPercent: number,
  ) => Promise<void>;
}) {
  const [hours, setHours] = useState(String(card.my_hours ?? 0));
  const [note, setNote] = useState(card.my_note ?? "");
  const [completion, setCompletion] = useState(card.my_completion_percent ?? 0);

  useEffect(() => {
    setHours(String(card.my_hours ?? 0));
    setNote(card.my_note ?? "");
    setCompletion(card.my_completion_percent ?? 0);
  }, [
    card.my_hours,
    card.my_note,
    card.my_completion_percent,
    card.task.id,
  ]);

  const statusKey = card.task.status as TaskStatus;
  const status = STATUS_LABELS[statusKey] || card.task.status;
  const planned = card.planned_hours ?? card.task.estimated_hours ?? 0;

  return (
    <li className="rounded-md border border-zinc-200 p-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="text-sm font-medium text-zinc-900">{card.task.title}</p>
          <p className="mt-1 text-xs text-zinc-500">
            {card.assignee_display_name || "未指派"} · {status}
            {card.task.due_date ? ` · 截止 ${card.task.due_date}` : ""}
            {planned > 0 ? ` · 计划 ${planned}h` : ""}
          </p>
        </div>
        <p className="text-xs text-zinc-500">合计 {card.total_hours}h</p>
      </div>

      <div className="mt-4 space-y-3 border-t border-zinc-100 pt-3">
        <label className="flex flex-col gap-2 text-xs text-zinc-500">
          <span className="flex items-center justify-between">
            <span>任务完成度</span>
            <span className="tabular-nums text-sm font-medium text-zinc-900">
              {completion}%
            </span>
          </span>
          <input
            type="range"
            min={0}
            max={100}
            step={5}
            value={completion}
            onChange={(e) => setCompletion(Number(e.target.value))}
            className="w-full"
          />
          {completion >= 100 ? (
            <span className="text-[11px] text-amber-800">
              保存后将标记为「待验收」
            </span>
          ) : null}
        </label>

        <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <label className="flex w-28 flex-col gap-1 text-xs text-zinc-500">
            当日实际工时
            <input
              type="number"
              min={0}
              max={24}
              step={0.1}
              value={hours}
              onChange={(e) => setHours(e.target.value)}
              className="rounded-md border border-zinc-300 px-2 py-1.5 text-sm text-zinc-900"
            />
          </label>
          <label className="flex min-w-0 flex-1 flex-col gap-1 text-xs text-zinc-500">
            当日进展说明
            <input
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="今天在这项任务上做了什么"
              maxLength={2000}
              className="rounded-md border border-zinc-300 px-2 py-1.5 text-sm text-zinc-900"
            />
          </label>
          <button
            type="button"
            disabled={saving}
            onClick={() => void onSave(card, hours, note, completion)}
            className="rounded-md bg-zinc-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-zinc-800 disabled:opacity-50"
          >
            {saving ? "保存中…" : "保存"}
          </button>
        </div>
      </div>
    </li>
  );
}
