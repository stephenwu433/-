"use client";

import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import {
  confirmCycleSchedule,
  createPhase,
  createWorkItem,
  deletePhase,
  deleteWorkItem,
  expandCycleScheduleToDaily,
  generateCycleSchedule,
  getCycleSchedule,
  getDailyPlan,
  importTasksIntoSchedule,
  syncWorkItemToTask,
  updatePhase,
  updateWorkItem,
  type CycleSchedule,
  type DailyPlan,
  type SeedMode,
  type WorkItemStatus,
} from "@/lib/cycle-schedule-api";
import { listMembers, type TeamMember } from "@/lib/members-api";
import { listTeamProjects } from "@/lib/projects-api";
import { listTasks, type Task } from "@/lib/tasks-api";
import { listMyTeams } from "@/lib/teams-api";

const STATUS_LABELS: Record<WorkItemStatus, string> = {
  todo: "未开始",
  doing: "进行中",
  done: "已完成",
};

export default function ProjectCycleSchedulePage() {
  const { isLoaded, isSignedIn, getToken } = useAuth();
  const params = useParams<{ teamId: string; projectId: string }>();
  const teamId = typeof params.teamId === "string" ? params.teamId : "";
  const projectId = typeof params.projectId === "string" ? params.projectId : "";

  const [schedule, setSchedule] = useState<CycleSchedule | null>(null);
  const [dailyPlan, setDailyPlan] = useState<DailyPlan | null>(null);
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [busyItemId, setBusyItemId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [seedMode, setSeedMode] = useState<SeedMode>("from_requirements");
  const [requirementsText, setRequirementsText] = useState("");
  const [createTasks, setCreateTasks] = useState(true);
  const [weekdaysOnly, setWeekdaysOnly] = useState(true);
  const [newPhaseName, setNewPhaseName] = useState("");
  const [importPhaseId, setImportPhaseId] = useState("");
  const [newItemTitleByPhase, setNewItemTitleByPhase] = useState<Record<string, string>>(
    {},
  );

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
      setSchedule(null);
      return;
    }
    const [payload, membersPayload, tasksPayload, projectsPayload, planPayload] =
      await Promise.all([
        getCycleSchedule(token, teamId, projectId),
        listMembers(token, teamId),
        listTasks(token, teamId, projectId),
        listTeamProjects(token, teamId),
        getDailyPlan(token, teamId, projectId).catch(() => null),
      ]);
    setSchedule(payload);
    setMembers(membersPayload.members);
    setTasks(tasksPayload.tasks);
    setDailyPlan(planPayload);
    setImportPhaseId((prev) => prev || payload.phases[0]?.id || "");
    const project = projectsPayload.projects.find((p) => p.id === projectId);
    if (project?.objective) {
      setRequirementsText((prev) => prev || project.objective || "");
    }
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

  const linkedTaskIds = useMemo(() => {
    const ids = new Set<string>();
    schedule?.phases.forEach((phase) => {
      phase.work_items.forEach((item) => {
        if (item.task_id) ids.add(item.task_id);
      });
    });
    return ids;
  }, [schedule]);

  const unlinkedTasks = useMemo(
    () => tasks.filter((t) => !linkedTaskIds.has(t.id)),
    [tasks, linkedTaskIds],
  );

  async function onGenerate(replaceExisting: boolean, mode: SeedMode = seedMode) {
    setBusy(true);
    setError(null);
    try {
      const token = await getToken();
      if (!token) throw new Error("拿不到登录 token");
      if (mode === "from_requirements" && !requirementsText.trim()) {
        throw new Error("请先填写需求（每行一条），再生成全周期排期。");
      }
      const payload = await generateCycleSchedule(token, teamId, projectId, {
        replace_existing: replaceExisting,
        seed_mode: mode,
        phase_count: 5,
        requirements_text:
          mode === "from_requirements" ? requirementsText.trim() : null,
        save_requirements_to_project: mode === "from_requirements",
        create_tasks: mode === "from_requirements" ? createTasks : false,
      });
      setSchedule(payload);
      setSeedMode(mode);
      if (payload.phases[0]) setImportPhaseId(payload.phases[0].id);
      const tasksPayload = await listTasks(token, teamId, projectId);
      setTasks(tasksPayload.tasks);
      // After generating from requirements, auto-expand into daily plan.
      if (mode === "from_requirements") {
        const plan = await expandCycleScheduleToDaily(token, teamId, projectId, {
          weekdays_only: weekdaysOnly,
          create_tasks: createTasks,
          pin_work_item_dates: true,
        });
        setDailyPlan(plan);
        if (plan.schedule) setSchedule(plan.schedule);
        const tasksAfter = await listTasks(token, teamId, projectId);
        setTasks(tasksAfter.tasks);
      } else {
        const plan = await getDailyPlan(token, teamId, projectId).catch(() => null);
        setDailyPlan(plan);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function onExpandDaily() {
    setBusy(true);
    setError(null);
    try {
      const token = await getToken();
      if (!token) throw new Error("拿不到登录 token");
      const plan = await expandCycleScheduleToDaily(token, teamId, projectId, {
        weekdays_only: weekdaysOnly,
        create_tasks: true,
        pin_work_item_dates: true,
      });
      setDailyPlan(plan);
      if (plan.schedule) setSchedule(plan.schedule);
      const tasksPayload = await listTasks(token, teamId, projectId);
      setTasks(tasksPayload.tasks);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function onConfirm() {
    setBusy(true);
    setError(null);
    try {
      const token = await getToken();
      if (!token) throw new Error("拿不到登录 token");
      const payload = await confirmCycleSchedule(token, teamId, projectId);
      setSchedule(payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function onAddPhase() {
    const name = newPhaseName.trim();
    if (!name) return;
    setBusy(true);
    setError(null);
    try {
      const token = await getToken();
      if (!token) throw new Error("拿不到登录 token");
      await createPhase(token, teamId, projectId, { name });
      setNewPhaseName("");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function onDeletePhase(phaseId: string, phaseName: string) {
    if (!window.confirm(`删除阶段「${phaseName}」及其工作项？`)) return;
    setBusy(true);
    setError(null);
    try {
      const token = await getToken();
      if (!token) throw new Error("拿不到登录 token");
      await deletePhase(token, teamId, projectId, phaseId);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function onRenamePhase(phaseId: string, name: string) {
    const next = name.trim();
    if (!next) return;
    setBusy(true);
    setError(null);
    try {
      const token = await getToken();
      if (!token) throw new Error("拿不到登录 token");
      await updatePhase(token, teamId, projectId, phaseId, { name: next });
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function onAddWorkItem(phaseId: string) {
    const title = (newItemTitleByPhase[phaseId] || "").trim();
    if (!title) return;
    setBusy(true);
    setError(null);
    try {
      const token = await getToken();
      if (!token) throw new Error("拿不到登录 token");
      await createWorkItem(token, teamId, projectId, phaseId, { title });
      setNewItemTitleByPhase((prev) => ({ ...prev, [phaseId]: "" }));
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function onImportUnlinked(phaseId: string) {
    if (!phaseId) {
      setError("请先选择要导入到的阶段");
      return;
    }
    if (unlinkedTasks.length === 0) {
      setError("没有可导入的未关联任务。可先在「每日任务」创建任务。");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const token = await getToken();
      if (!token) throw new Error("拿不到登录 token");
      const payload = await importTasksIntoSchedule(
        token,
        teamId,
        projectId,
        phaseId,
      );
      setSchedule(payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function patchItem(
    itemId: string,
    input: Parameters<typeof updateWorkItem>[4],
  ) {
    setBusyItemId(itemId);
    setError(null);
    try {
      const token = await getToken();
      if (!token) throw new Error("拿不到登录 token");
      const updated = await updateWorkItem(token, teamId, projectId, itemId, input);
      setSchedule((prev) => {
        if (!prev) return prev;
        const phases = prev.phases.map((phase) => ({
          ...phase,
          work_items: phase.work_items.map((item) =>
            item.id === updated.id ? updated : item,
          ),
        }));
        const total = phases
          .flatMap((p) => p.work_items)
          .reduce((sum, item) => sum + Number(item.estimated_hours || 0), 0);
        const linked = phases
          .flatMap((p) => p.work_items)
          .filter((item) => item.task_id).length;
        return {
          ...prev,
          phases,
          total_estimated_hours: Math.round(total * 10) / 10,
          linked_task_count: linked,
          plan_confirmed: false,
        };
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusyItemId(null);
    }
  }

  async function onSyncTask(itemId: string) {
    setBusyItemId(itemId);
    setError(null);
    try {
      const token = await getToken();
      if (!token) throw new Error("拿不到登录 token");
      const updated = await syncWorkItemToTask(token, teamId, projectId, itemId);
      setSchedule((prev) => {
        if (!prev) return prev;
        const phases = prev.phases.map((phase) => ({
          ...phase,
          work_items: phase.work_items.map((item) =>
            item.id === updated.id ? updated : item,
          ),
        }));
        const linked = phases
          .flatMap((p) => p.work_items)
          .filter((item) => item.task_id).length;
        return { ...prev, phases, linked_task_count: linked, plan_confirmed: false };
      });
      const tasksPayload = await listTasks(token, teamId, projectId);
      setTasks(tasksPayload.tasks);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusyItemId(null);
    }
  }

  async function onDeleteItem(itemId: string) {
    if (!window.confirm("删除这个工作项？已关联的任务不会被删除。")) return;
    setBusyItemId(itemId);
    setError(null);
    try {
      const token = await getToken();
      if (!token) throw new Error("拿不到登录 token");
      await deleteWorkItem(token, teamId, projectId, itemId);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusyItemId(null);
    }
  }

  function memberLabel(userId: string | null) {
    if (!userId) return "未指派";
    const m = members.find((x) => x.user_id === userId);
    return m?.display_name || m?.email || m?.clerk_user_id || userId.slice(0, 8);
  }

  const empty = !loading && schedule && schedule.phase_count === 0;

  return (
    <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col px-6 py-10">
      <p className="text-sm text-zinc-500">
        <Link
          href={`/teams/${teamId}/projects/${projectId}`}
          className="underline hover:text-zinc-800"
        >
          ← 返回项目设置
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
        <Link href="/portfolio" className="underline hover:text-zinc-800">
          项目总览
        </Link>
      </p>
      <p className="mt-3 text-xs font-medium uppercase tracking-[0.16em] text-zinc-500">
        Project Master Plan
      </p>
      <h1 className="mt-1 text-2xl font-semibold tracking-tight text-zinc-900">
        {schedule?.project_name || "项目"} · 全局周期排期
      </h1>
      <p className="mt-2 text-sm leading-6 text-zinc-600">
        写出需求后生成全周期阶段，并自动排到「每一天具体做什么」；也可在「每日任务」按天执行。
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
          {error ? (
            <p className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
              {error}
            </p>
          ) : null}

          {loading ? (
            <p className="text-sm text-zinc-500">加载排期…</p>
          ) : schedule ? (
            <>
              <section className="grid grid-cols-2 gap-3 sm:grid-cols-5">
                <Summary
                  label="项目整体"
                  value={
                    schedule.planned_start || schedule.planned_end
                      ? `${schedule.planned_start || "?"} → ${schedule.planned_end || "?"}`
                      : "未设日期"
                  }
                />
                <Summary
                  label="预估工期(h)"
                  value={String(schedule.total_estimated_hours)}
                />
                <Summary
                  label="阶段 / 工作项"
                  value={`${schedule.phase_count} / ${schedule.work_item_count}`}
                />
                <Summary
                  label="已关联任务"
                  value={String(schedule.linked_task_count ?? 0)}
                />
                <Summary
                  label="计划状态"
                  value={schedule.plan_confirmed ? "已确认" : "待确认"}
                />
              </section>

              {empty ? (
                <section className="rounded-md border border-dashed border-zinc-300 px-6 py-8">
                  <p className="text-center text-sm font-medium text-zinc-900">
                    根据需求生成全周期排期
                  </p>
                  <p className="mt-2 text-center text-sm text-zinc-600">
                    先确认项目设置里有起止日期，再在下方填写需求。系统会按全周期拆成可执行工作项。
                  </p>
                  <div className="mx-auto mt-5 max-w-2xl">
                    <label className="block text-xs font-medium text-zinc-500">
                      项目需求（每行一条）
                    </label>
                    <textarea
                      value={requirementsText}
                      onChange={(e) => setRequirementsText(e.target.value)}
                      rows={8}
                      placeholder={
                        "例如：\n- 支持邮箱登录与邀请成员\n- 项目总览看板\n- 全局周期排期\n- 每日任务与工时\n- 项目日报"
                      }
                      className="mt-1 w-full rounded-md border border-zinc-300 px-3 py-2 text-sm leading-6 text-zinc-900"
                    />
                    <label className="mt-3 flex items-center gap-2 text-sm text-zinc-700">
                      <input
                        type="checkbox"
                        checked={createTasks}
                        onChange={(e) => setCreateTasks(e.target.checked)}
                      />
                      生成时同步创建真实任务（推荐）
                    </label>
                    <label className="mt-2 flex items-center gap-2 text-sm text-zinc-700">
                      <input
                        type="checkbox"
                        checked={weekdaysOnly}
                        onChange={(e) => setWeekdaysOnly(e.target.checked)}
                      />
                      每日排期只排工作日
                    </label>
                  </div>
                  <div className="mt-5 flex flex-wrap justify-center gap-3">
                    <Link
                      href={`/teams/${teamId}/projects/${projectId}`}
                      className="rounded-md border border-zinc-300 px-4 py-2 text-sm text-zinc-800 hover:bg-zinc-50"
                    >
                      编辑项目设置
                    </Link>
                    <button
                      type="button"
                      disabled={busy || !requirementsText.trim()}
                      onClick={() => void onGenerate(true, "from_requirements")}
                      className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 disabled:opacity-50"
                    >
                      {busy ? "生成中…" : "生成全周期排期"}
                    </button>
                  </div>
                  <details className="mx-auto mt-6 max-w-2xl text-sm text-zinc-600">
                    <summary className="cursor-pointer text-zinc-500">其他生成方式</summary>
                    <div className="mt-3 flex flex-wrap gap-2">
                      <button
                        type="button"
                        disabled={busy}
                        onClick={() => void onGenerate(true, "from_tasks")}
                        className="rounded-md border border-zinc-300 px-3 py-1.5 text-xs hover:bg-zinc-50 disabled:opacity-50"
                      >
                        从现有任务生成
                      </button>
                      <button
                        type="button"
                        disabled={busy}
                        onClick={() => void onGenerate(true, "phases_only")}
                        className="rounded-md border border-zinc-300 px-3 py-1.5 text-xs hover:bg-zinc-50 disabled:opacity-50"
                      >
                        只生成空阶段
                      </button>
                    </div>
                  </details>
                </section>
              ) : (
                <>
                  <section>
                    <div className="mb-3 flex flex-wrap items-end justify-between gap-3">
                      <h2 className="text-sm font-medium uppercase tracking-wide text-zinc-500">
                        阶段总览
                      </h2>
                      <div className="flex flex-wrap items-center gap-2">
                        <button
                          type="button"
                          disabled={busy || !requirementsText.trim()}
                          onClick={() => {
                            if (
                              window.confirm(
                                "将按当前需求重新生成全周期排期（覆盖现有阶段与工作项），确定吗？",
                              )
                            ) {
                              void onGenerate(true, "from_requirements");
                            }
                          }}
                          className="rounded-md bg-zinc-900 px-3 py-1.5 text-xs font-medium text-white hover:bg-zinc-800 disabled:opacity-50"
                        >
                          按需求重新生成
                        </button>
                        <button
                          type="button"
                          disabled={busy}
                          onClick={() => {
                            if (
                              window.confirm(
                                "重新生成会覆盖现有阶段与工作项，确定吗？",
                              )
                            ) {
                              void onGenerate(true, seedMode);
                            }
                          }}
                          className="rounded-md border border-zinc-300 px-3 py-1.5 text-xs text-zinc-700 hover:bg-zinc-50 disabled:opacity-50"
                        >
                          其他方式重生成
                        </button>
                      </div>
                    </div>
                    <div className="mb-4 rounded-md border border-zinc-200 bg-zinc-50 px-4 py-3">
                      <label className="block text-xs font-medium text-zinc-500">
                        项目需求（每行一条，可改后点「按需求重新生成」）
                      </label>
                      <textarea
                        value={requirementsText}
                        onChange={(e) => setRequirementsText(e.target.value)}
                        rows={4}
                        className="mt-1 w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm leading-6"
                      />
                      <label className="mt-2 flex items-center gap-2 text-xs text-zinc-700">
                        <input
                          type="checkbox"
                          checked={createTasks}
                          onChange={(e) => setCreateTasks(e.target.checked)}
                        />
                        重新生成时同步创建真实任务
                      </label>
                      <label className="mt-2 flex items-center gap-2 text-xs text-zinc-700">
                        <input
                          type="checkbox"
                          checked={weekdaysOnly}
                          onChange={(e) => setWeekdaysOnly(e.target.checked)}
                        />
                        每日排期只排工作日
                      </label>
                      <div className="mt-3 flex flex-wrap gap-2">
                        <button
                          type="button"
                          disabled={busy || schedule.work_item_count === 0}
                          onClick={() => void onExpandDaily()}
                          className="rounded-md border border-zinc-300 bg-white px-3 py-1.5 text-xs text-zinc-800 hover:bg-zinc-50 disabled:opacity-50"
                        >
                          {busy ? "展开中…" : "重新展开为每日排期"}
                        </button>
                        <Link
                          href={`/teams/${teamId}/projects/${projectId}/daily`}
                          className="rounded-md border border-zinc-300 bg-white px-3 py-1.5 text-xs text-zinc-800 hover:bg-zinc-50"
                        >
                          打开每日任务
                        </Link>
                      </div>
                    </div>
                    <ul className="flex gap-3 overflow-x-auto pb-1">
                      {schedule.phases.map((phase, index) => (
                        <li
                          key={phase.id}
                          className={`min-w-[200px] shrink-0 rounded-md border px-3 py-3 ${
                            index === 0
                              ? "border-zinc-800 bg-zinc-900 text-white"
                              : "border-zinc-200 bg-zinc-50 text-zinc-900"
                          }`}
                        >
                          <p
                            className={`text-xs ${index === 0 ? "text-zinc-300" : "text-zinc-500"}`}
                          >
                            阶段 {index + 1}
                          </p>
                          <input
                            defaultValue={phase.name}
                            key={`${phase.id}-${phase.name}`}
                            disabled={busy}
                            onBlur={(e) => {
                              const next = e.target.value.trim();
                              if (!next || next === phase.name) return;
                              void onRenamePhase(phase.id, next);
                            }}
                            className={`mt-1 w-full rounded-md border px-2 py-1 text-sm font-medium ${
                              index === 0
                                ? "border-zinc-600 bg-zinc-800 text-white"
                                : "border-zinc-300 bg-white text-zinc-900"
                            }`}
                          />
                          <p
                            className={`mt-2 text-xs ${index === 0 ? "text-zinc-400" : "text-zinc-500"}`}
                          >
                            {phase.planned_start || "?"} →{" "}
                            {phase.planned_end || "?"}
                          </p>
                          <button
                            type="button"
                            disabled={busy}
                            onClick={() => void onDeletePhase(phase.id, phase.name)}
                            className={`mt-2 text-xs underline disabled:opacity-50 ${
                              index === 0 ? "text-zinc-300" : "text-zinc-500"
                            }`}
                          >
                            删除阶段
                          </button>
                        </li>
                      ))}
                    </ul>
                    <div className="mt-3 flex flex-wrap gap-2">
                      <input
                        value={newPhaseName}
                        onChange={(e) => setNewPhaseName(e.target.value)}
                        placeholder="新阶段名称，例如：联调验收"
                        className="min-w-[220px] flex-1 rounded-md border border-zinc-300 px-3 py-2 text-sm"
                      />
                      <button
                        type="button"
                        disabled={busy || !newPhaseName.trim()}
                        onClick={() => void onAddPhase()}
                        className="rounded-md border border-zinc-300 px-3 py-2 text-sm text-zinc-800 hover:bg-zinc-50 disabled:opacity-50"
                      >
                        添加阶段
                      </button>
                    </div>
                  </section>

                  <section className="rounded-md border border-zinc-200 bg-zinc-50 px-4 py-4">
                    <h2 className="text-sm font-medium text-zinc-900">
                      从现有任务导入
                    </h2>
                    <p className="mt-1 text-xs text-zinc-600">
                      未关联排期的任务：{unlinkedTasks.length} 个。导入后工作项会带上
                      task 链接。
                    </p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      <select
                        value={importPhaseId}
                        onChange={(e) => setImportPhaseId(e.target.value)}
                        className="rounded-md border border-zinc-300 px-3 py-2 text-sm"
                      >
                        <option value="">选择阶段</option>
                        {schedule.phases.map((phase) => (
                          <option key={phase.id} value={phase.id}>
                            {phase.name}
                          </option>
                        ))}
                      </select>
                      <button
                        type="button"
                        disabled={busy || !importPhaseId}
                        onClick={() => void onImportUnlinked(importPhaseId)}
                        className="rounded-md bg-zinc-900 px-3 py-2 text-sm font-medium text-white hover:bg-zinc-800 disabled:opacity-50"
                      >
                        导入未关联任务
                      </button>
                      <Link
                        href={`/teams/${teamId}/projects/${projectId}/daily`}
                        className="rounded-md border border-zinc-300 px-3 py-2 text-sm text-zinc-800 hover:bg-white"
                      >
                        去每日任务创建
                      </Link>
                    </div>
                  </section>

                  <section>
                    <h2 className="text-sm font-medium uppercase tracking-wide text-zinc-500">
                      工作项安排
                    </h2>
                    <div className="mt-3 overflow-x-auto">
                      <table className="w-full min-w-[860px] border-collapse text-left text-sm">
                        <thead>
                          <tr className="border-b border-zinc-200 text-xs text-zinc-500">
                            <th className="py-2 pr-3 font-medium">阶段 / 工作项</th>
                            <th className="py-2 pr-3 font-medium">负责人</th>
                            <th className="py-2 pr-3 font-medium">计划开始</th>
                            <th className="py-2 pr-3 font-medium">计划结束</th>
                            <th className="py-2 pr-3 font-medium">估时(h)</th>
                            <th className="py-2 pr-3 font-medium">状态</th>
                            <th className="py-2 font-medium">任务</th>
                          </tr>
                        </thead>
                        <tbody>
                          {schedule.phases.map((phase) => (
                            <PhaseRows
                              key={phase.id}
                              phaseName={phase.name}
                              items={phase.work_items}
                              members={members}
                              busyItemId={busyItemId}
                              busy={busy}
                              newItemTitle={newItemTitleByPhase[phase.id] || ""}
                              onNewItemTitle={(value) =>
                                setNewItemTitleByPhase((prev) => ({
                                  ...prev,
                                  [phase.id]: value,
                                }))
                              }
                              onAddItem={() => void onAddWorkItem(phase.id)}
                              memberLabel={memberLabel}
                              onPatch={patchItem}
                              onSync={(id) => void onSyncTask(id)}
                              onDelete={(id) => void onDeleteItem(id)}
                            />
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </section>

                  <section>
                    <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                      <h2 className="text-sm font-medium uppercase tracking-wide text-zinc-500">
                        每日具体排期
                      </h2>
                      <p className="text-xs text-zinc-500">
                        {dailyPlan
                          ? `${dailyPlan.day_count} 天 · ${dailyPlan.assigned_work_item_count} 项`
                          : "生成需求排期后会自动展开到每一天"}
                      </p>
                    </div>
                    {!dailyPlan || dailyPlan.days.length === 0 ? (
                      <div className="rounded-md border border-dashed border-zinc-300 px-4 py-6 text-center text-sm text-zinc-600">
                        还没有按天排期。点「重新展开为每日排期」，系统会按阶段日期与工时容量，把工作项落到具体日期。
                      </div>
                    ) : (
                      <ul className="space-y-3">
                        {dailyPlan.days.map((day) => (
                          <li
                            key={day.date}
                            className="rounded-md border border-zinc-200 px-4 py-3"
                          >
                            <div className="flex flex-wrap items-baseline justify-between gap-2">
                              <p className="text-sm font-medium text-zinc-900">
                                {day.date}
                                {day.phase_name ? (
                                  <span className="ml-2 text-xs font-normal text-zinc-500">
                                    {day.phase_name}
                                  </span>
                                ) : null}
                              </p>
                              <p className="text-xs text-zinc-500">
                                约 {day.total_planned_hours}h
                              </p>
                            </div>
                            <ul className="mt-2 space-y-1">
                              {day.assignments.map((a) => (
                                <li
                                  key={`${day.date}-${a.work_item_id}-${a.title}`}
                                  className="flex flex-wrap items-center justify-between gap-2 text-sm text-zinc-700"
                                >
                                  <span>
                                    {a.title}
                                    <span className="ml-2 text-xs text-zinc-400">
                                      {a.phase_name}
                                    </span>
                                  </span>
                                  <span className="text-xs text-zinc-500">
                                    {a.planned_hours}h · {memberLabel(a.assignee_user_id)}
                                  </span>
                                </li>
                              ))}
                            </ul>
                          </li>
                        ))}
                      </ul>
                    )}
                  </section>

                  <div className="flex flex-wrap items-center justify-between gap-3 border-t border-zinc-200 pt-5">
                    <Link
                      href={`/teams/${teamId}/projects/${projectId}`}
                      className="text-sm text-zinc-600 underline hover:text-zinc-900"
                    >
                      ← 返回项目设置
                    </Link>
                    <button
                      type="button"
                      disabled={busy || schedule.plan_confirmed}
                      onClick={() => void onConfirm()}
                      className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 disabled:opacity-50"
                    >
                      {schedule.plan_confirmed
                        ? "计划已确认"
                        : busy
                          ? "确认中…"
                          : "确认本项目计划"}
                    </button>
                  </div>
                </>
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

function PhaseRows({
  phaseName,
  items,
  members,
  busyItemId,
  busy,
  newItemTitle,
  onNewItemTitle,
  onAddItem,
  memberLabel,
  onPatch,
  onSync,
  onDelete,
}: {
  phaseName: string;
  items: CycleSchedule["phases"][number]["work_items"];
  members: TeamMember[];
  busyItemId: string | null;
  busy: boolean;
  newItemTitle: string;
  onNewItemTitle: (value: string) => void;
  onAddItem: () => void;
  memberLabel: (id: string | null) => string;
  onPatch: (
    itemId: string,
    input: Parameters<typeof updateWorkItem>[4],
  ) => Promise<void>;
  onSync: (itemId: string) => void;
  onDelete: (itemId: string) => void;
}) {
  return (
    <>
      <tr className="border-b border-zinc-100 bg-zinc-50/80">
        <td colSpan={7} className="py-2 pr-3 text-xs font-medium text-zinc-600">
          {phaseName}
        </td>
      </tr>
      {items.map((item) => {
        const disabled = busyItemId === item.id;
        const status =
          item.status === "doing" || item.status === "done" ? item.status : "todo";
        return (
          <tr key={item.id} className="border-b border-zinc-100 align-top">
            <td className="py-2 pr-3">
              <input
                defaultValue={item.title}
                disabled={disabled}
                onBlur={(e) => {
                  const next = e.target.value.trim();
                  if (!next || next === item.title) return;
                  void onPatch(item.id, { title: next });
                }}
                className="w-full rounded-md border border-zinc-300 px-2 py-1.5 text-sm"
              />
            </td>
            <td className="py-2 pr-3">
              <select
                value={item.assignee_user_id ?? ""}
                disabled={disabled}
                onChange={(e) => {
                  const value = e.target.value;
                  void onPatch(
                    item.id,
                    value
                      ? { assignee_user_id: value }
                      : { clear_assignee: true },
                  );
                }}
                className="rounded-md border border-zinc-300 px-2 py-1.5 text-sm"
                title={memberLabel(item.assignee_user_id)}
              >
                <option value="">未指派</option>
                {members.map((m) => (
                  <option key={m.user_id} value={m.user_id}>
                    {m.display_name || m.email || m.clerk_user_id}
                  </option>
                ))}
              </select>
            </td>
            <td className="py-2 pr-3">
              <input
                type="date"
                defaultValue={item.planned_start ?? ""}
                key={`${item.id}-start-${item.planned_start}`}
                disabled={disabled}
                onBlur={(e) => {
                  const start = e.target.value;
                  if (start === (item.planned_start ?? "")) return;
                  void onPatch(item.id, {
                    planned_start: start || null,
                    planned_end: item.planned_end,
                    clear_dates: !start && !item.planned_end,
                  });
                }}
                className="rounded-md border border-zinc-300 px-2 py-1.5 text-sm"
              />
            </td>
            <td className="py-2 pr-3">
              <input
                type="date"
                defaultValue={item.planned_end ?? ""}
                key={`${item.id}-end-${item.planned_end}`}
                disabled={disabled}
                onBlur={(e) => {
                  const end = e.target.value;
                  if (end === (item.planned_end ?? "")) return;
                  void onPatch(item.id, {
                    planned_start: item.planned_start,
                    planned_end: end || null,
                    clear_dates: !item.planned_start && !end,
                  });
                }}
                className="rounded-md border border-zinc-300 px-2 py-1.5 text-sm"
              />
            </td>
            <td className="py-2 pr-3">
              <input
                type="number"
                min={0}
                max={1000}
                step={0.1}
                defaultValue={item.estimated_hours}
                key={`${item.id}-hours-${item.estimated_hours}`}
                disabled={disabled}
                onBlur={(e) => {
                  const hours = Number(e.target.value);
                  if (!Number.isFinite(hours) || hours === item.estimated_hours) {
                    return;
                  }
                  void onPatch(item.id, { estimated_hours: hours });
                }}
                className="w-20 rounded-md border border-zinc-300 px-2 py-1.5 text-sm"
              />
            </td>
            <td className="py-2 pr-3">
              <select
                value={status}
                disabled={disabled}
                onChange={(e) =>
                  void onPatch(item.id, {
                    status: e.target.value as WorkItemStatus,
                  })
                }
                className="rounded-md border border-zinc-300 px-2 py-1.5 text-sm"
              >
                <option value="todo">{STATUS_LABELS.todo}</option>
                <option value="doing">{STATUS_LABELS.doing}</option>
                <option value="done">{STATUS_LABELS.done}</option>
              </select>
            </td>
            <td className="py-2">
              <div className="flex flex-col gap-1">
                {item.task_id ? (
                  <span className="text-xs text-emerald-700">已关联</span>
                ) : (
                  <button
                    type="button"
                    disabled={disabled}
                    onClick={() => onSync(item.id)}
                    className="text-left text-xs text-zinc-700 underline disabled:opacity-50"
                  >
                    同步为任务
                  </button>
                )}
                <button
                  type="button"
                  disabled={disabled}
                  onClick={() => onDelete(item.id)}
                  className="text-left text-xs text-zinc-500 underline disabled:opacity-50"
                >
                  删除
                </button>
              </div>
            </td>
          </tr>
        );
      })}
      <tr className="border-b border-zinc-100">
        <td colSpan={7} className="py-2">
          <div className="flex flex-wrap gap-2">
            <input
              value={newItemTitle}
              onChange={(e) => onNewItemTitle(e.target.value)}
              placeholder={`在「${phaseName}」添加工作项`}
              className="min-w-[240px] flex-1 rounded-md border border-zinc-300 px-2 py-1.5 text-sm"
            />
            <button
              type="button"
              disabled={busy || !newItemTitle.trim()}
              onClick={onAddItem}
              className="rounded-md border border-zinc-300 px-3 py-1.5 text-xs text-zinc-700 hover:bg-zinc-50 disabled:opacity-50"
            >
              添加工作项
            </button>
          </div>
        </td>
      </tr>
    </>
  );
}
