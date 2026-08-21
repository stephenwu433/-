"use client";

import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { useParams } from "next/navigation";
import { FormEvent, useCallback, useEffect, useState } from "react";

import { listMembers, type TeamMember } from "@/lib/members-api";
import {
  listTeamProjects,
  updateProject,
  type Project,
  type ProjectStatus,
} from "@/lib/projects-api";
import {
  createTask,
  deleteTask,
  listTasks,
  updateTask,
  type Task,
  type TaskStatus,
} from "@/lib/tasks-api";
import { listMyTeams } from "@/lib/teams-api";

const TASK_STATUS_LABELS: Record<TaskStatus, string> = {
  todo: "待办",
  doing: "进行中",
  done: "已完成",
};

const PROJECT_STATUS_LABELS: Record<ProjectStatus, string> = {
  active: "进行中",
  paused: "已暂停",
  done: "已完成",
};

export default function ProjectTasksPage() {
  const { isLoaded, isSignedIn, getToken } = useAuth();
  const params = useParams<{ teamId: string; projectId: string }>();
  const teamId = typeof params.teamId === "string" ? params.teamId : "";
  const projectId = typeof params.projectId === "string" ? params.projectId : "";

  const [project, setProject] = useState<Project | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [title, setTitle] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [assignee, setAssignee] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [settingsSaving, setSettingsSaving] = useState(false);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // settings form state
  const [settingsName, setSettingsName] = useState("");
  const [settingsDescription, setSettingsDescription] = useState("");
  const [settingsObjective, setSettingsObjective] = useState("");
  const [settingsStart, setSettingsStart] = useState("");
  const [settingsEnd, setSettingsEnd] = useState("");
  const [settingsOwner, setSettingsOwner] = useState("");
  const [settingsHours, setSettingsHours] = useState("6");
  const [settingsStatus, setSettingsStatus] = useState<ProjectStatus>("active");
  const [settingsConfirmed, setSettingsConfirmed] = useState(false);

  const syncSettingsForm = useCallback((p: Project) => {
    setSettingsName(p.name);
    setSettingsDescription(p.description ?? "");
    setSettingsObjective(p.objective ?? "");
    setSettingsStart(p.planned_start ?? "");
    setSettingsEnd(p.planned_end ?? "");
    setSettingsOwner(p.owner_user_id ?? "");
    setSettingsHours(String(p.member_daily_hours ?? 6));
    setSettingsStatus(
      p.status === "paused" || p.status === "done" ? p.status : "active",
    );
    setSettingsConfirmed(Boolean(p.plan_confirmed));
  }, []);

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
      setProject(null);
      setTasks([]);
      return;
    }
    const [projectsPayload, tasksPayload, membersPayload] = await Promise.all([
      listTeamProjects(token, teamId),
      listTasks(token, teamId, projectId),
      listMembers(token, teamId),
    ]);
    const matched =
      projectsPayload.projects.find((p) => p.id === projectId) ?? null;
    setProject(matched);
    setTasks(tasksPayload.tasks);
    setMembers(membersPayload.members);
    if (matched) syncSettingsForm(matched);
    else setError("找不到这个项目。");
  }, [getToken, teamId, projectId, syncSettingsForm]);

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

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    const trimmed = title.trim();
    if (!trimmed) return;
    setSaving(true);
    setError(null);
    try {
      const token = await getToken();
      if (!token) throw new Error("拿不到登录 token");
      await createTask(token, teamId, projectId, {
        title: trimmed,
        due_date: dueDate || undefined,
        assignee_user_id: assignee || undefined,
      });
      setTitle("");
      setDueDate("");
      setAssignee("");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  }

  async function onSaveSettings(e: FormEvent) {
    e.preventDefault();
    const trimmed = settingsName.trim();
    if (!trimmed) return;
    setSettingsSaving(true);
    setError(null);
    try {
      const token = await getToken();
      if (!token) throw new Error("拿不到登录 token");
      const hours = Number(settingsHours);
      const updated = await updateProject(token, teamId, projectId, {
        name: trimmed,
        description: settingsDescription.trim() || null,
        objective: settingsObjective.trim() || null,
        status: settingsStatus,
        planned_start: settingsStart || null,
        planned_end: settingsEnd || null,
        clear_schedule: !settingsStart && !settingsEnd,
        owner_user_id: settingsOwner || null,
        clear_owner: !settingsOwner,
        member_daily_hours:
          Number.isFinite(hours) && hours >= 0 ? hours : 6,
        plan_confirmed: settingsConfirmed,
      });
      setProject(updated);
      syncSettingsForm(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSettingsSaving(false);
    }
  }

  async function onStatus(taskId: string, status: TaskStatus) {
    setBusyId(taskId);
    try {
      const token = await getToken();
      if (!token) throw new Error("拿不到登录 token");
      const updated = await updateTask(token, teamId, projectId, taskId, {
        status,
      });
      setTasks((prev) => prev.map((t) => (t.id === updated.id ? updated : t)));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusyId(null);
    }
  }

  async function onDelete(taskId: string) {
    if (!window.confirm("确定删除这个任务？")) return;
    setBusyId(taskId);
    try {
      const token = await getToken();
      if (!token) throw new Error("拿不到登录 token");
      await deleteTask(token, teamId, projectId, taskId);
      setTasks((prev) => prev.filter((t) => t.id !== taskId));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusyId(null);
    }
  }

  function memberLabel(userId: string | null) {
    if (!userId) return "未指派";
    const m = members.find((x) => x.user_id === userId);
    return m?.display_name || m?.email || m?.clerk_user_id || userId.slice(0, 8);
  }

  return (
    <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col px-6 py-10">
      <p className="text-sm text-zinc-500">
        <Link href={`/teams/${teamId}`} className="underline hover:text-zinc-800">
          ← 返回团队项目
        </Link>
        {" · "}
        <Link
          href={`/teams/${teamId}/projects/${projectId}/daily`}
          className="underline hover:text-zinc-800"
        >
          每日任务
        </Link>
        {" · "}
        <Link
          href={`/teams/${teamId}/projects/${projectId}/report`}
          className="underline hover:text-zinc-800"
        >
          项目日报
        </Link>
        {" · "}
        <Link
          href={`/teams/${teamId}/projects/${projectId}/schedule`}
          className="underline hover:text-zinc-800"
        >
          全局周期排期
        </Link>
        {" · "}
        <Link href="/portfolio" className="underline hover:text-zinc-800">
          项目总览
        </Link>
      </p>
      <h1 className="mt-3 text-2xl font-semibold tracking-tight text-zinc-900">
        项目任务与设置
      </h1>
      <p className="mt-2 text-sm text-zinc-600">
        上方改项目设置（目标、排期、负责人、日工时）；下方管理具体任务。
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
          {project ? (
            <div>
              <p className="text-lg font-medium text-zinc-900">{project.name}</p>
              <p className="text-xs text-zinc-500">
                {project.planned_start || "未设开始"} →{" "}
                {project.planned_end || "未设结束"} · {project.status}
                {project.plan_confirmed ? " · 计划已确认" : " · 计划未确认"}
              </p>
            </div>
          ) : null}

          {project ? (
            <form onSubmit={onSaveSettings} className="space-y-3">
              <h2 className="text-sm font-medium uppercase tracking-wide text-zinc-500">
                项目设置
              </h2>
              <input
                value={settingsName}
                onChange={(e) => setSettingsName(e.target.value)}
                placeholder="项目名称"
                maxLength={120}
                className="w-full rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500"
              />
              <input
                value={settingsDescription}
                onChange={(e) => setSettingsDescription(e.target.value)}
                placeholder="简介（可选）"
                maxLength={2000}
                className="w-full rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500"
              />
              <textarea
                value={settingsObjective}
                onChange={(e) => setSettingsObjective(e.target.value)}
                placeholder="项目目标 / 成功标准"
                maxLength={4000}
                rows={3}
                className="w-full rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500"
              />
              <div className="flex flex-col gap-3 sm:flex-row">
                <label className="flex flex-1 flex-col gap-1 text-xs text-zinc-500">
                  开始日期
                  <input
                    type="date"
                    value={settingsStart}
                    onChange={(e) => setSettingsStart(e.target.value)}
                    className="rounded-md border border-zinc-300 px-3 py-2 text-sm text-zinc-900"
                  />
                </label>
                <label className="flex flex-1 flex-col gap-1 text-xs text-zinc-500">
                  结束日期
                  <input
                    type="date"
                    value={settingsEnd}
                    onChange={(e) => setSettingsEnd(e.target.value)}
                    className="rounded-md border border-zinc-300 px-3 py-2 text-sm text-zinc-900"
                  />
                </label>
              </div>
              <div className="flex flex-col gap-3 sm:flex-row">
                <label className="flex flex-1 flex-col gap-1 text-xs text-zinc-500">
                  负责人
                  <select
                    value={settingsOwner}
                    onChange={(e) => setSettingsOwner(e.target.value)}
                    className="rounded-md border border-zinc-300 px-3 py-2 text-sm text-zinc-900"
                  >
                    <option value="">未指定</option>
                    {members.map((m) => (
                      <option key={m.user_id} value={m.user_id}>
                        {m.display_name || m.email || m.clerk_user_id}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="flex flex-1 flex-col gap-1 text-xs text-zinc-500">
                  成员日人均工时
                  <input
                    type="number"
                    min={0}
                    max={24}
                    step={0.5}
                    value={settingsHours}
                    onChange={(e) => setSettingsHours(e.target.value)}
                    className="rounded-md border border-zinc-300 px-3 py-2 text-sm text-zinc-900"
                  />
                </label>
              </div>
              <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
                <label className="flex flex-1 flex-col gap-1 text-xs text-zinc-500">
                  状态
                  <select
                    value={settingsStatus}
                    onChange={(e) =>
                      setSettingsStatus(e.target.value as ProjectStatus)
                    }
                    className="rounded-md border border-zinc-300 px-3 py-2 text-sm text-zinc-900"
                  >
                    <option value="active">{PROJECT_STATUS_LABELS.active}</option>
                    <option value="paused">{PROJECT_STATUS_LABELS.paused}</option>
                    <option value="done">{PROJECT_STATUS_LABELS.done}</option>
                  </select>
                </label>
                <label className="flex items-center gap-2 pb-2 text-sm text-zinc-700">
                  <input
                    type="checkbox"
                    checked={settingsConfirmed}
                    onChange={(e) => setSettingsConfirmed(e.target.checked)}
                  />
                  计划已确认
                </label>
                <button
                  type="submit"
                  disabled={settingsSaving || !settingsName.trim()}
                  className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 disabled:opacity-50"
                >
                  {settingsSaving ? "保存中…" : "保存设置"}
                </button>
                <Link
                  href={`/teams/${teamId}/projects/${projectId}/schedule`}
                  className="rounded-md border border-zinc-300 px-4 py-2 text-sm text-zinc-800 hover:bg-zinc-50"
                >
                  全周期排期 →
                </Link>
                <Link
                  href={`/teams/${teamId}/projects/${projectId}/daily`}
                  className="rounded-md border border-zinc-300 px-4 py-2 text-sm text-zinc-800 hover:bg-zinc-50"
                >
                  每日任务 / 工时 →
                </Link>
                <Link
                  href={`/teams/${teamId}/projects/${projectId}/report`}
                  className="rounded-md border border-zinc-300 px-4 py-2 text-sm text-zinc-800 hover:bg-zinc-50"
                >
                  项目日报 →
                </Link>
              </div>
            </form>
          ) : null}

          <form onSubmit={onCreate} className="space-y-3">
            <h2 className="text-sm font-medium uppercase tracking-wide text-zinc-500">
              新建任务
            </h2>
            <div className="flex flex-col gap-3 sm:flex-row">
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="例如：完成竞品调研"
                maxLength={200}
                className="min-w-0 flex-1 rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500"
              />
              <button
                type="submit"
                disabled={saving || !title.trim()}
                className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 disabled:opacity-50"
              >
                {saving ? "创建中…" : "添加任务"}
              </button>
            </div>
            <div className="flex flex-col gap-3 sm:flex-row">
              <label className="flex flex-1 flex-col gap-1 text-xs text-zinc-500">
                截止日期
                <input
                  type="date"
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                  className="rounded-md border border-zinc-300 px-3 py-2 text-sm text-zinc-900"
                />
              </label>
              <label className="flex flex-1 flex-col gap-1 text-xs text-zinc-500">
                负责人
                <select
                  value={assignee}
                  onChange={(e) => setAssignee(e.target.value)}
                  className="rounded-md border border-zinc-300 px-3 py-2 text-sm text-zinc-900"
                >
                  <option value="">暂不指派</option>
                  {members.map((m) => (
                    <option key={m.user_id} value={m.user_id}>
                      {m.display_name || m.email || m.clerk_user_id}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          </form>

          {error ? (
            <p className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
              {error}
            </p>
          ) : null}

          <section>
            <h2 className="text-sm font-medium uppercase tracking-wide text-zinc-500">
              任务列表
            </h2>
            {loading ? (
              <p className="mt-3 text-sm text-zinc-500">加载中…</p>
            ) : tasks.length === 0 ? (
              <p className="mt-3 text-sm text-zinc-500">
                还没有任务。在上面添加第一条。
              </p>
            ) : (
              <ul className="mt-3 divide-y divide-zinc-200 border-t border-b border-zinc-200">
                {tasks.map((task) => (
                  <li
                    key={task.id}
                    className="flex flex-col gap-3 py-3 sm:flex-row sm:items-center sm:justify-between"
                  >
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-zinc-900">{task.title}</p>
                      <p className="text-xs text-zinc-500">
                        {memberLabel(task.assignee_user_id)}
                        {task.due_date ? ` · 截止 ${task.due_date}` : ""}
                        {task.description ? ` · ${task.description}` : ""}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <select
                        value={
                          task.status === "doing" || task.status === "done"
                            ? task.status
                            : "todo"
                        }
                        disabled={busyId === task.id}
                        onChange={(e) =>
                          onStatus(task.id, e.target.value as TaskStatus)
                        }
                        className="rounded-md border border-zinc-300 bg-white px-2 py-1.5 text-sm disabled:opacity-50"
                      >
                        <option value="todo">{TASK_STATUS_LABELS.todo}</option>
                        <option value="doing">{TASK_STATUS_LABELS.doing}</option>
                        <option value="done">{TASK_STATUS_LABELS.done}</option>
                      </select>
                      <button
                        type="button"
                        disabled={busyId === task.id}
                        onClick={() => onDelete(task.id)}
                        className="rounded-md border border-zinc-300 px-2 py-1.5 text-xs text-zinc-700 hover:bg-zinc-50 disabled:opacity-50"
                      >
                        删除
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      )}
    </main>
  );
}
