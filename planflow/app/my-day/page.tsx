"use client";

import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { WorkbenchShell } from "@/components/WorkbenchShell";
import { upsertTimeEntry } from "@/lib/daily-tasks-api";
import {
  getMyDailyTasks,
  type MyDailyBucket,
  type MyDailyTaskItem,
  type MyDailyTasksResponse,
} from "@/lib/my-daily-api";
import { getUnreadCount } from "@/lib/notifications-api";
import {
  updateTask,
  STATUS_LABELS,
  TASK_STATUSES,
  type TaskStatus,
} from "@/lib/tasks-api";

function todayIso() {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function shiftIso(iso: string, days: number) {
  const d = new Date(`${iso}T12:00:00`);
  d.setDate(d.getDate() + days);
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function formatCnDate(iso: string) {
  const [y, m, d] = iso.split("-");
  if (!y || !m || !d) return iso;
  const weekday = ["日", "一", "二", "三", "四", "五", "六"][
    new Date(`${iso}T12:00:00`).getDay()
  ];
  return `${y}年${Number(m)}月${Number(d)}日 · 周${weekday}`;
}

const STATUS_PILL: Record<TaskStatus, string> = {
  todo: "bg-zinc-100 text-zinc-700",
  doing: "bg-sky-50 text-sky-800",
  review: "bg-amber-50 text-amber-800",
  done: "bg-emerald-50 text-emerald-800",
  returned: "bg-red-50 text-red-800",
};

const BUCKET_META: Record<
  MyDailyBucket,
  { title: string; hint: string }
> = {
  overdue: {
    title: "逾期未完成",
    hint: "截止日期已过，仍指派给你",
  },
  today: {
    title: "今天要做",
    hint: "当天到期，或你已填写今日工时",
  },
  later: {
    title: "进行中 / 待跟进",
    hint: "未排在当天、但仍需推进的任务",
  },
};

export default function MyDailyPage() {
  const { isLoaded, isSignedIn, getToken } = useAuth();
  const [viewDate, setViewDate] = useState(todayIso);
  const [data, setData] = useState<MyDailyTasksResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyTaskId, setBusyTaskId] = useState<string | null>(null);
  const [unreadCount, setUnreadCount] = useState(0);

  const refresh = useCallback(async () => {
    setError(null);
    const token = await getToken();
    if (!token) {
      setError("拿不到登录 token。请重新登录。");
      return;
    }
    const [payload, unread] = await Promise.all([
      getMyDailyTasks(token, viewDate),
      getUnreadCount(token).catch(() => ({ unread_count: 0 })),
    ]);
    setData(payload);
    setUnreadCount(unread.unread_count);
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

  async function onSaveProgress(
    item: MyDailyTaskItem,
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
        {
          hours,
          note,
          completion_percent: pct,
          apply_review_status: pct >= 100,
        },
      );
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusyTaskId(null);
    }
  }

  const grouped = useMemo(() => {
    const buckets: Record<MyDailyBucket, MyDailyTaskItem[]> = {
      overdue: [],
      today: [],
      later: [],
    };
    for (const item of data?.tasks ?? []) {
      const key: MyDailyBucket =
        item.bucket === "overdue" || item.bucket === "later"
          ? item.bucket
          : "today";
      buckets[key].push(item);
    }
    return buckets;
  }, [data]);

  const isToday = viewDate === todayIso();
  const overtime =
    data != null && data.my_logged_hours > data.capacity_hours;

  return (
    <WorkbenchShell>
      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col px-6 py-10">
        <p className="text-xs font-medium uppercase tracking-[0.16em] text-zinc-500">
          Personal Workbench
        </p>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight text-zinc-900">
          我的今日工作台
        </h1>
        <p className="mt-2 text-sm leading-6 text-zinc-600">
          跨项目汇总指派给你的事：先清逾期，再做今天，顺手填完成度和工时。
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
            <div className="flex flex-wrap items-end justify-between gap-3">
              <div className="flex flex-wrap items-end gap-2">
                <button
                  type="button"
                  onClick={() => setViewDate((d) => shiftIso(d, -1))}
                  className="rounded-md border border-zinc-300 px-3 py-2 text-sm text-zinc-700 hover:bg-zinc-50"
                >
                  前一天
                </button>
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
                  onClick={() => setViewDate((d) => shiftIso(d, 1))}
                  className="rounded-md border border-zinc-300 px-3 py-2 text-sm text-zinc-700 hover:bg-zinc-50"
                >
                  后一天
                </button>
                {!isToday ? (
                  <button
                    type="button"
                    onClick={() => setViewDate(todayIso())}
                    className="rounded-md bg-zinc-900 px-3 py-2 text-sm font-medium text-white hover:bg-zinc-800"
                  >
                    回到今天
                  </button>
                ) : null}
              </div>
              <div className="flex flex-wrap gap-2">
                <Link
                  href="/team-day"
                  className="rounded-md border border-zinc-300 px-3 py-1.5 text-sm text-zinc-800 hover:bg-zinc-50"
                >
                  团队今日
                </Link>
                <Link
                  href="/workload"
                  className="rounded-md border border-zinc-300 px-3 py-1.5 text-sm text-zinc-800 hover:bg-zinc-50"
                >
                  跨项目负荷
                </Link>
              </div>
            </div>

            {unreadCount > 0 ? (
              <Link
                href="/notifications"
                className="block rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900 hover:bg-amber-100"
              >
                有 {unreadCount} 条未读提醒，打开站内提醒查看。
              </Link>
            ) : null}

            {error ? (
              <p className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
                {error}
              </p>
            ) : null}

            {loading ? (
              <p className="text-sm text-zinc-500">加载今日工作台…</p>
            ) : data ? (
              <>
                <section className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                  <Summary
                    label={isToday ? "今天" : "查看日期"}
                    value={formatCnDate(data.view_date)}
                  />
                  <Summary
                    label="逾期 / 今日 / 待跟进"
                    value={`${data.overdue_count} / ${data.today_count} / ${data.later_count}`}
                  />
                  <Summary
                    label="未开始 · 进行中 · 待验收"
                    value={`${data.todo_count} · ${data.doing_count} · ${data.review_count}`}
                  />
                  <Summary
                    label="已填 / 可用工时"
                    value={`${data.my_logged_hours}h / ${data.capacity_hours}h`}
                  />
                </section>

                <div>
                  <div className="flex items-center justify-between text-xs text-zinc-500">
                    <span>
                      计划 {data.planned_hours}h · 已填 {data.my_logged_hours}h
                      {overtime ? " · 已超过当日可用工时" : ""}
                    </span>
                    <span>
                      {Math.min(
                        100,
                        Math.round(
                          (data.my_logged_hours /
                            Math.max(data.capacity_hours, 0.1)) *
                            100,
                        ),
                      )}
                      %
                    </span>
                  </div>
                  <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-zinc-100">
                    <div
                      className={`h-full rounded-full ${overtime ? "bg-red-600" : "bg-zinc-800"}`}
                      style={{
                        width: `${Math.min(
                          100,
                          (data.my_logged_hours /
                            Math.max(data.capacity_hours, 0.1)) *
                            100,
                        )}%`,
                      }}
                    />
                  </div>
                </div>

                {data.tasks.length === 0 ? (
                  <section className="rounded-md border border-dashed border-zinc-300 px-6 py-10 text-center">
                    <p className="text-sm font-medium text-zinc-900">
                      这一天没有需要你处理的任务
                    </p>
                    <p className="mt-2 text-sm text-zinc-600">
                      没有逾期、当天到期或进行中的指派。可去项目排期分派每日任务，或打开某项目的每日任务页添加。
                    </p>
                    <div className="mt-5 flex flex-wrap justify-center gap-3">
                      <Link
                        href="/portfolio"
                        className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800"
                      >
                        去项目总览
                      </Link>
                      <Link
                        href="/team-day"
                        className="rounded-md border border-zinc-300 px-4 py-2 text-sm text-zinc-800 hover:bg-zinc-50"
                      >
                        看团队今日
                      </Link>
                    </div>
                  </section>
                ) : (
                  <div className="space-y-8">
                    {(["overdue", "today", "later"] as MyDailyBucket[]).map(
                      (bucket) => {
                        const items = grouped[bucket];
                        if (items.length === 0) return null;
                        const meta = BUCKET_META[bucket];
                        return (
                          <section key={bucket} className="space-y-3">
                            <div>
                              <h2 className="text-sm font-medium uppercase tracking-wide text-zinc-500">
                                {meta.title} · {items.length}
                              </h2>
                              <p className="mt-0.5 text-xs text-zinc-500">
                                {meta.hint}
                              </p>
                            </div>
                            {groupByProject(items).map((group) => (
                              <div key={group.project_id} className="space-y-2">
                                <p className="text-xs font-medium text-zinc-600">
                                  {group.team_name} · {group.project_name}
                                </p>
                                <ul className="space-y-3">
                                  {group.tasks.map((item) => (
                                    <TaskCard
                                      key={item.task_id}
                                      item={item}
                                      busy={busyTaskId === item.task_id}
                                      onStatus={(status) =>
                                        void onStatus(item, status)
                                      }
                                      onSave={(hours, note, pct) =>
                                        void onSaveProgress(
                                          item,
                                          hours,
                                          note,
                                          pct,
                                        )
                                      }
                                    />
                                  ))}
                                </ul>
                              </div>
                            ))}
                          </section>
                        );
                      },
                    )}
                  </div>
                )}
              </>
            ) : null}
          </div>
        )}
      </main>
    </WorkbenchShell>
  );
}

function groupByProject(items: MyDailyTaskItem[]) {
  const map = new Map<
    string,
    {
      project_id: string;
      project_name: string;
      team_name: string;
      tasks: MyDailyTaskItem[];
    }
  >();
  for (const item of items) {
    const existing = map.get(item.project_id);
    if (existing) {
      existing.tasks.push(item);
    } else {
      map.set(item.project_id, {
        project_id: item.project_id,
        project_name: item.project_name,
        team_name: item.team_name,
        tasks: [item],
      });
    }
  }
  return [...map.values()];
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
  onSave,
}: {
  item: MyDailyTaskItem;
  busy: boolean;
  onStatus: (status: string) => void;
  onSave: (hours: string, note: string, completionPercent: number) => void;
}) {
  const [hours, setHours] = useState(String(item.my_hours || ""));
  const [note, setNote] = useState(item.my_note || "");
  const [completion, setCompletion] = useState(item.my_completion_percent || 0);
  const status = (TASK_STATUSES as string[]).includes(item.status)
    ? (item.status as TaskStatus)
    : "todo";

  useEffect(() => {
    setHours(String(item.my_hours || ""));
    setNote(item.my_note || "");
    setCompletion(item.my_completion_percent || 0);
  }, [
    item.my_hours,
    item.my_note,
    item.my_completion_percent,
    item.task_id,
  ]);

  return (
    <li className="rounded-md border border-zinc-200 px-4 py-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm font-medium text-zinc-900">{item.title}</p>
          <p className="mt-1 text-xs text-zinc-500">
            {item.phase_name ? `${item.phase_name} · ` : ""}
            {item.due_date ? `截止 ${item.due_date}` : "未设截止日期"}
            {item.estimated_hours > 0 ? ` · 计划 ${item.estimated_hours}h` : ""}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={`rounded px-2 py-0.5 text-[11px] font-medium ${STATUS_PILL[status]}`}
          >
            {STATUS_LABELS[status]}
          </span>
          <Link
            href={`/teams/${item.team_id}/projects/${item.project_id}/daily`}
            className="text-xs text-zinc-600 underline hover:text-zinc-900"
          >
            项目每日
          </Link>
        </div>
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
            {TASK_STATUSES.map((s) => (
              <option key={s} value={s}>
                {STATUS_LABELS[s]}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="mt-3 space-y-3 border-t border-zinc-100 pt-3">
        <label className="flex flex-col gap-2 text-xs text-zinc-500">
          <span className="flex items-center justify-between">
            <span>完成度</span>
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
            disabled={busy}
            onChange={(e) => setCompletion(Number(e.target.value))}
            className="w-full"
          />
          {completion >= 100 ? (
            <span className="text-[11px] text-amber-800">
              保存后将标记为「待验收」
            </span>
          ) : null}
        </label>

        <div className="flex flex-wrap items-end gap-2">
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
            进展说明
            <input
              value={note}
              disabled={busy}
              onChange={(e) => setNote(e.target.value)}
              placeholder="今天在这项任务上做了什么"
              className="mt-1 block w-full rounded-md border border-zinc-300 px-2 py-1.5 text-sm"
            />
          </label>
          <button
            type="button"
            disabled={busy}
            onClick={() => onSave(hours, note, completion)}
            className="rounded-md bg-zinc-900 px-3 py-2 text-xs font-medium text-white hover:bg-zinc-800 disabled:opacity-50"
          >
            {busy ? "保存中…" : "保存进展"}
          </button>
        </div>
      </div>
    </li>
  );
}
