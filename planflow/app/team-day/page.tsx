"use client";

import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { listTeamProjects, type Project } from "@/lib/projects-api";
import {
  getTeamDailyBoard,
  type TeamDailyBoardResponse,
  type TeamDailyMemberColumn,
  type TeamDailyTaskItem,
} from "@/lib/team-daily-api";
import { listMyTeams, type Team } from "@/lib/teams-api";
import { STATUS_LABELS, type TaskStatus } from "@/lib/tasks-api";

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

function statusLabel(status: string) {
  return STATUS_LABELS[status as TaskStatus] || status;
}

export default function TeamDayPage() {
  const { isLoaded, isSignedIn, getToken } = useAuth();
  const [teams, setTeams] = useState<Team[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [teamId, setTeamId] = useState("");
  const [projectId, setProjectId] = useState("");
  const [viewDate, setViewDate] = useState(todayIso);
  const [data, setData] = useState<TeamDailyBoardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoaded || !isSignedIn) return;
    let cancelled = false;
    (async () => {
      try {
        const token = await getToken();
        if (!token) throw new Error("拿不到登录 token。请重新登录。");
        const res = await listMyTeams(token);
        if (cancelled) return;
        setTeams(res.teams);
        setTeamId((prev) => prev || res.teams[0]?.id || "");
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : String(err));
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [isLoaded, isSignedIn, getToken]);

  useEffect(() => {
    if (!isLoaded || !isSignedIn || !teamId) {
      setProjects([]);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const token = await getToken();
        if (!token) return;
        const res = await listTeamProjects(token, teamId);
        if (cancelled) return;
        setProjects(res.projects);
        setProjectId("");
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : String(err));
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [isLoaded, isSignedIn, getToken, teamId]);

  const refresh = useCallback(async () => {
    if (!teamId) {
      setData(null);
      return;
    }
    setError(null);
    const token = await getToken();
    if (!token) {
      setError("拿不到登录 token。请重新登录。");
      return;
    }
    const payload = await getTeamDailyBoard(token, teamId, {
      viewDate,
      projectId: projectId || undefined,
    });
    setData(payload);
  }, [getToken, teamId, viewDate, projectId]);

  useEffect(() => {
    if (!isLoaded || !isSignedIn || !teamId) return;
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
  }, [isLoaded, isSignedIn, teamId, refresh]);

  return (
    <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col px-6 py-10">
      <p className="text-sm text-zinc-500">
        <Link href="/my-day" className="underline hover:text-zinc-800">
          ← 我的今日
        </Link>
        {" · "}
        <Link href="/workload" className="underline hover:text-zinc-800">
          跨项目负荷
        </Link>
      </p>
      <p className="mt-3 text-xs font-medium uppercase tracking-[0.16em] text-zinc-500">
        Team Day
      </p>
      <h1 className="mt-1 text-2xl font-semibold tracking-tight text-zinc-900">
        团队今日看板
      </h1>
      <p className="mt-2 text-sm leading-6 text-zinc-600">
        按成员查看当天指派任务与已填工时。只读总览；改状态或工时请打开对应项目每日任务页。
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
      ) : teams.length === 0 ? (
        <section className="mt-8 rounded-md border border-dashed border-zinc-300 px-6 py-10 text-center">
          <p className="text-sm font-medium text-zinc-900">你还没有加入任何团队</p>
          <Link
            href="/teams"
            className="mt-5 inline-block rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800"
          >
            去创建团队
          </Link>
        </section>
      ) : (
        <div className="mt-8 space-y-6">
          <div className="flex flex-wrap items-end gap-3">
            <label className="text-sm text-zinc-700">
              团队
              <select
                value={teamId}
                onChange={(e) => setTeamId(e.target.value)}
                className="mt-1 block min-w-[180px] rounded-md border border-zinc-300 px-3 py-2 text-sm"
              >
                {teams.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="text-sm text-zinc-700">
              项目（可选）
              <select
                value={projectId}
                onChange={(e) => setProjectId(e.target.value)}
                className="mt-1 block min-w-[180px] rounded-md border border-zinc-300 px-3 py-2 text-sm"
              >
                <option value="">全部项目</option>
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </label>
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
            <p className="text-sm text-zinc-500">加载团队今日…</p>
          ) : data ? (
            <>
              <section className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                <Summary label="日期" value={formatCnDate(data.view_date)} />
                <Summary label="成员" value={String(data.member_count)} />
                <Summary
                  label="任务（未开始/进行中）"
                  value={`${data.task_count}（${data.todo_count}/${data.doing_count}）`}
                />
                <Summary label="已填工时" value={`${data.logged_hours}h`} />
              </section>

              <div className="space-y-4">
                {data.members.map((member) => (
                  <MemberBlock key={member.user_id} member={member} teamId={data.team_id} />
                ))}
                {data.unassigned_tasks.length > 0 ? (
                  <UnassignedBlock tasks={data.unassigned_tasks} teamId={data.team_id} />
                ) : null}
              </div>
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

function MemberBlock({
  member,
  teamId,
}: {
  member: TeamDailyMemberColumn;
  teamId: string;
}) {
  return (
    <section className="rounded-md border border-zinc-200 px-4 py-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <div>
          <h2 className="text-sm font-semibold text-zinc-900">{member.display_name}</h2>
          <p className="mt-0.5 text-xs text-zinc-500">
            {member.job_title_label || "未设岗位"}
            {" · "}
            {member.task_count} 项 · 已填 {member.logged_hours}h
          </p>
        </div>
        <p className="text-xs text-zinc-500">
          未开始 {member.todo_count} / 进行中 {member.doing_count} / 完成{" "}
          {member.done_count}
        </p>
      </div>
      {member.tasks.length === 0 ? (
        <p className="mt-3 text-sm text-zinc-500">这一天没有指派任务</p>
      ) : (
        <ul className="mt-3 space-y-2">
          {member.tasks.map((task) => (
            <TaskRow key={task.task_id} task={task} teamId={teamId} />
          ))}
        </ul>
      )}
    </section>
  );
}

function UnassignedBlock({
  tasks,
  teamId,
}: {
  tasks: TeamDailyTaskItem[];
  teamId: string;
}) {
  return (
    <section className="rounded-md border border-dashed border-amber-300 bg-amber-50/40 px-4 py-4">
      <h2 className="text-sm font-semibold text-zinc-900">未指派</h2>
      <p className="mt-0.5 text-xs text-zinc-500">{tasks.length} 项当天任务尚未指派人</p>
      <ul className="mt-3 space-y-2">
        {tasks.map((task) => (
          <TaskRow key={task.task_id} task={task} teamId={teamId} />
        ))}
      </ul>
    </section>
  );
}

function TaskRow({ task, teamId }: { task: TeamDailyTaskItem; teamId: string }) {
  return (
    <li className="flex flex-wrap items-start justify-between gap-2 rounded-md bg-zinc-50 px-3 py-2">
      <div>
        <p className="text-sm text-zinc-900">{task.title}</p>
        <p className="mt-0.5 text-xs text-zinc-500">
          {task.project_name}
          {task.phase_name ? ` · ${task.phase_name}` : ""}
          {" · "}
          {statusLabel(task.status)}
          {task.assignee_hours > 0 ? ` · ${task.assignee_hours}h` : ""}
        </p>
      </div>
      <Link
        href={`/teams/${teamId}/projects/${task.project_id}/daily`}
        className="text-xs text-zinc-600 underline hover:text-zinc-900"
      >
        项目每日
      </Link>
    </li>
  );
}
