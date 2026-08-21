"use client";

import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import {
  getWorkload,
  type WorkloadMember,
  type WorkloadResponse,
} from "@/lib/workload-api";

function todayIso() {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function monthLabel(iso: string) {
  const [y, m] = iso.split("-");
  if (!y || !m) return iso;
  return `${y}年${Number(m)}月`;
}

function initials(name: string) {
  const parts = name.trim().split(/\s+/);
  if (parts.length >= 2) {
    return (parts[0][0] + parts[1][0]).toUpperCase();
  }
  return name.slice(0, 2).toUpperCase() || "?";
}

export default function WorkloadPage() {
  const { isLoaded, isSignedIn } = useAuth();

  return (
    <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col px-6 py-10">
      <p className="text-sm text-zinc-500">
        <Link href="/portfolio" className="underline hover:text-zinc-800">
          ← 项目总览
        </Link>
      </p>
      <p className="mt-3 text-xs font-medium uppercase tracking-[0.16em] text-zinc-500">
        Cross-Project Capacity
      </p>
      <h1 className="mt-1 text-2xl font-semibold tracking-tight text-zinc-900">
        跨项目成员工作量
      </h1>
      <p className="mt-2 text-sm leading-6 text-zinc-600">
        按月汇总你所在团队里各成员的未完成到期任务与已填工时，用来发现多项目资源冲突。
      </p>

      {!isLoaded ? (
        <p className="mt-8 text-sm text-zinc-500">正在确认登录状态…</p>
      ) : !isSignedIn ? (
        <div className="mt-8 rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          请先{" "}
          <Link href="/sign-in" className="font-medium underline">
            登录
          </Link>{" "}
          后再查看跨项目负荷。
        </div>
      ) : (
        <WorkloadPanel />
      )}
    </main>
  );
}

function WorkloadPanel() {
  const { getToken, isLoaded } = useAuth();
  const [viewDate, setViewDate] = useState(todayIso);
  const [data, setData] = useState<WorkloadResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setError(null);
    const token = await getToken();
    if (!token) {
      setError("拿不到登录 token。请重新登录后再试。");
      setData(null);
      return;
    }
    const payload = await getWorkload(token, viewDate);
    setData(payload);
  }, [getToken, viewDate]);

  useEffect(() => {
    if (!isLoaded) return;
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        await refresh();
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : String(err));
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [isLoaded, refresh]);

  return (
    <div className="mt-8 space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <label className="flex flex-col gap-1 text-xs text-zinc-500">
          查看月份（任选月内一天）
          <input
            type="date"
            value={viewDate}
            onChange={(e) => setViewDate(e.target.value)}
            className="rounded-md border border-zinc-300 px-3 py-2 text-sm text-zinc-900"
          />
        </label>
        {data ? (
          <p className="text-sm text-zinc-600">
            {monthLabel(data.month_start)} · {data.member_count} 人有任务/工时 ·
            偏高 {data.overloaded_count} 人 · 工作日 {data.weekday_count} 天
          </p>
        ) : null}
      </div>

      {error ? (
        <p className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          {error}
        </p>
      ) : null}

      {loading ? (
        <p className="text-sm text-zinc-500">加载跨项目负荷…</p>
      ) : !data || data.members.length === 0 ? (
        <section className="rounded-md border border-dashed border-zinc-300 px-6 py-10 text-center">
          <p className="text-sm font-medium text-zinc-900">
            这个月还没有跨项目任务或工时
          </p>
          <p className="mt-2 text-sm text-zinc-600">
            给任务设置负责人与截止日期，或在每日任务里填工时后，这里会汇总成员负荷。
          </p>
          <Link
            href="/portfolio"
            className="mt-5 inline-block rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800"
          >
            回到项目总览
          </Link>
        </section>
      ) : (
        <ul className="grid gap-4 sm:grid-cols-2">
          {data.members.map((member) => (
            <MemberCard key={member.user_id} member={member} />
          ))}
        </ul>
      )}
    </div>
  );
}

function MemberCard({ member }: { member: WorkloadMember }) {
  return (
    <li className="rounded-md border border-zinc-200 p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-zinc-900 text-xs font-semibold text-white">
            {initials(member.display_name)}
          </div>
          <div className="min-w-0">
            <p className="truncate text-sm font-medium text-zinc-900">
              {member.display_name}
            </p>
            <p className="text-xs text-zinc-500">
              涉及 {member.project_count} 个项目 · 未完成到期任务{" "}
              {member.due_task_count}
            </p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-2xl font-semibold tabular-nums text-zinc-900">
            {member.load_ratio.toFixed(1)}x
          </p>
          <p className="text-xs text-zinc-500">相对月容量</p>
        </div>
      </div>

      {member.overloaded ? (
        <p className="mt-3 text-sm text-red-700">
          每天约 {member.projects_per_day} 项到期任务，可能超负荷
        </p>
      ) : (
        <p className="mt-3 text-sm text-zinc-600">
          已填 {member.logged_hours}h / 月容量约 {member.capacity_hours}h
        </p>
      )}

      <ul className="mt-3 space-y-1 border-t border-zinc-100 pt-3">
        {member.projects.map((p) => (
          <li
            key={p.project_id}
            className="flex items-center justify-between gap-2 text-xs text-zinc-600"
          >
            <Link
              href={`/teams/${p.team_id}/projects/${p.project_id}/daily`}
              className="truncate underline hover:text-zinc-900"
            >
              {p.project_name}
              {p.team_name ? ` · ${p.team_name}` : ""}
            </Link>
            <span className="shrink-0 tabular-nums">
              {p.due_task_count} 任务 · {p.logged_hours}h
            </span>
          </li>
        ))}
      </ul>
    </li>
  );
}
