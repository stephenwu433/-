"use client";

import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import {
  getPortfolio,
  type PortfolioProject,
  type PortfolioResponse,
  type ProjectStatus,
} from "@/lib/projects-api";
import { WorkbenchShell } from "@/components/WorkbenchShell";

const STATUS_LABELS: Record<ProjectStatus, string> = {
  active: "进行中",
  paused: "已暂停",
  done: "已完成",
};

function todayIso() {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

export default function PortfolioPage() {
  const { isLoaded, isSignedIn } = useAuth();

  return (
    <WorkbenchShell>
      <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col px-6 py-10">
      <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">
        项目总览
      </h1>
      <p className="mt-2 text-sm leading-6 text-zinc-600">
        跨团队看清所有项目进度、今日任务与负荷。需要细调时再进入具体项目设置。
      </p>

      {!isLoaded ? (
        <p className="mt-8 text-sm text-zinc-500">正在确认登录状态…</p>
      ) : !isSignedIn ? (
        <div className="mt-8 rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          请先{" "}
          <Link href="/sign-in" className="font-medium underline">
            登录
          </Link>{" "}
          后再查看项目总览。
        </div>
      ) : (
        <PortfolioPanel />
      )}
    </main>
    </WorkbenchShell>
  );
}

function PortfolioPanel() {
  const { getToken, isLoaded } = useAuth();
  const [viewDate, setViewDate] = useState(todayIso);
  const [data, setData] = useState<PortfolioResponse | null>(null);
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
    const payload = await getPortfolio(token, viewDate);
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

  const stats = data?.stats;

  return (
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
        <div className="flex flex-wrap gap-2">
          <Link
            href="/notifications"
            className="rounded-md border border-zinc-300 px-3 py-1.5 text-sm text-zinc-800 hover:bg-zinc-50"
          >
            站内提醒
          </Link>
          <Link
            href="/workload"
            className="rounded-md border border-zinc-300 px-3 py-1.5 text-sm text-zinc-800 hover:bg-zinc-50"
          >
            跨项目负荷
          </Link>
          <Link
            href="/teams"
            className="rounded-md border border-zinc-300 px-3 py-1.5 text-sm text-zinc-800 hover:bg-zinc-50"
          >
            管理团队 / 新建项目
          </Link>
        </div>
      </div>

      {error ? (
        <p className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          {error}
        </p>
      ) : null}

      {loading ? (
        <p className="text-sm text-zinc-500">加载总览…</p>
      ) : stats ? (
        <section className="grid grid-cols-2 gap-3 sm:grid-cols-5">
          <Stat label="进行中项目" value={String(stats.active_projects)} />
          <Stat label="全部任务" value={String(stats.total_tasks)} />
          <Stat label="当日任务" value={String(stats.day_tasks)} />
          <Stat
            label="当日估时(h)"
            value={String(stats.day_task_hours_estimate)}
          />
          <Stat label="高负荷成员" value={String(stats.high_load_members)} />
        </section>
      ) : null}

      <section>
        <h2 className="text-sm font-medium uppercase tracking-wide text-zinc-500">
          项目卡片
        </h2>
        {loading ? null : !data || data.projects.length === 0 ? (
          <p className="mt-3 text-sm text-zinc-500">
            还没有项目。先去「我的团队」创建一个，再回到这里看总览。
          </p>
        ) : (
          <ul className="mt-3 grid gap-4 sm:grid-cols-2">
            {data.projects.map((project) => (
              <ProjectCard key={project.id} project={project} />
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-zinc-200 bg-zinc-50 px-3 py-3">
      <p className="text-xs text-zinc-500">{label}</p>
      <p className="mt-1 text-xl font-semibold tabular-nums text-zinc-900">
        {value}
      </p>
    </div>
  );
}

function ProjectCard({ project }: { project: PortfolioProject }) {
  const status =
    project.status === "paused" || project.status === "done"
      ? project.status
      : "active";

  return (
    <li className="rounded-md border border-zinc-200 p-4">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate text-sm font-medium text-zinc-900">
            {project.name}
          </p>
          <p className="mt-0.5 text-xs text-zinc-500">
            {project.team_name}
            {project.owner_display_name
              ? ` · 负责人 ${project.owner_display_name}`
              : ""}
          </p>
        </div>
        <span className="shrink-0 rounded bg-zinc-100 px-2 py-0.5 text-xs text-zinc-700">
          {STATUS_LABELS[status]}
        </span>
      </div>

      <p className="mt-3 line-clamp-2 text-sm text-zinc-600">
        {project.objective || project.description || "暂无目标说明"}
      </p>

      <div className="mt-3">
        <div className="flex items-center justify-between text-xs text-zinc-500">
          <span>进度</span>
          <span>
            {project.done_task_count}/{project.task_count} ·{" "}
            {project.progress_percent}%
          </span>
        </div>
        <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-zinc-100">
          <div
            className="h-full rounded-full bg-zinc-800"
            style={{ width: `${Math.min(100, project.progress_percent)}%` }}
          />
        </div>
      </div>

      <div className="mt-3 flex flex-wrap gap-x-3 gap-y-1 text-xs text-zinc-500">
        <span>
          {project.planned_start || "未设开始"} →{" "}
          {project.planned_end || "未设结束"}
        </span>
        <span>日人均 {project.member_daily_hours}h</span>
        <span>当日任务 {project.day_task_count}</span>
        <span>{project.plan_confirmed ? "计划已确认" : "计划未确认"}</span>
      </div>

      <div className="mt-4 flex gap-2">
        <Link
          href={`/teams/${project.team_id}/projects/${project.id}`}
          className="rounded-md bg-zinc-900 px-3 py-1.5 text-xs font-medium text-white hover:bg-zinc-800"
        >
          打开任务 / 设置
        </Link>
        <Link
          href={`/teams/${project.team_id}/projects/${project.id}/schedule`}
          className="rounded-md border border-zinc-300 px-3 py-1.5 text-xs text-zinc-800 hover:bg-zinc-50"
        >
          周期排期
        </Link>
        <Link
          href={`/teams/${project.team_id}/projects/${project.id}/daily`}
          className="rounded-md border border-zinc-300 px-3 py-1.5 text-xs text-zinc-800 hover:bg-zinc-50"
        >
          每日任务
        </Link>
        <Link
          href={`/teams/${project.team_id}/projects/${project.id}/report`}
          className="rounded-md border border-zinc-300 px-3 py-1.5 text-xs text-zinc-800 hover:bg-zinc-50"
        >
          项目日报
        </Link>
        <Link
          href={`/teams/${project.team_id}`}
          className="rounded-md border border-zinc-300 px-3 py-1.5 text-xs text-zinc-800 hover:bg-zinc-50"
        >
          团队页
        </Link>
      </div>
    </li>
  );
}
