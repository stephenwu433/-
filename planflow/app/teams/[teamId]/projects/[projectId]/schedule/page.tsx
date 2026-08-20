"use client";

import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import {
  confirmCycleSchedule,
  generateCycleSchedule,
  getCycleSchedule,
  updateWorkItem,
  type CycleSchedule,
  type WorkItemStatus,
} from "@/lib/cycle-schedule-api";
import { listMembers, type TeamMember } from "@/lib/members-api";
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
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [busyItemId, setBusyItemId] = useState<string | null>(null);
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
      setSchedule(null);
      return;
    }
    const [payload, membersPayload] = await Promise.all([
      getCycleSchedule(token, teamId, projectId),
      listMembers(token, teamId),
    ]);
    setSchedule(payload);
    setMembers(membersPayload.members);
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

  async function onGenerate(replaceExisting: boolean) {
    setBusy(true);
    setError(null);
    try {
      const token = await getToken();
      if (!token) throw new Error("拿不到登录 token");
      const payload = await generateCycleSchedule(
        token,
        teamId,
        projectId,
        replaceExisting,
      );
      setSchedule(payload);
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
        return {
          ...prev,
          phases,
          total_estimated_hours: Math.round(total * 10) / 10,
          plan_confirmed: false,
        };
      });
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
        按项目起止日期生成阶段计划，再调整各阶段工作项的负责人、日期与估时。
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
              <section className="grid grid-cols-2 gap-3 sm:grid-cols-4">
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
                  label="计划状态"
                  value={schedule.plan_confirmed ? "已确认" : "待确认"}
                />
              </section>

              {empty ? (
                <section className="rounded-md border border-dashed border-zinc-300 px-6 py-10 text-center">
                  <p className="text-sm font-medium text-zinc-900">
                    当前项目还没有排期
                  </p>
                  <p className="mt-2 text-sm text-zinc-600">
                    请先在项目设置里填好开始/结束日期，再生成全周期排期。
                  </p>
                  <div className="mt-5 flex flex-wrap justify-center gap-3">
                    <Link
                      href={`/teams/${teamId}/projects/${projectId}`}
                      className="rounded-md border border-zinc-300 px-4 py-2 text-sm text-zinc-800 hover:bg-zinc-50"
                    >
                      编辑项目设置
                    </Link>
                    <button
                      type="button"
                      disabled={busy}
                      onClick={() => onGenerate(true)}
                      className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 disabled:opacity-50"
                    >
                      {busy ? "生成中…" : "生成全周期排期"}
                    </button>
                  </div>
                </section>
              ) : (
                <>
                  <section>
                    <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                      <h2 className="text-sm font-medium uppercase tracking-wide text-zinc-500">
                        阶段总览
                      </h2>
                      <button
                        type="button"
                        disabled={busy}
                        onClick={() => {
                          if (
                            window.confirm(
                              "重新生成会覆盖现有阶段与工作项，确定吗？",
                            )
                          ) {
                            void onGenerate(true);
                          }
                        }}
                        className="rounded-md border border-zinc-300 px-3 py-1.5 text-xs text-zinc-700 hover:bg-zinc-50 disabled:opacity-50"
                      >
                        重新生成
                      </button>
                    </div>
                    <ul className="flex gap-3 overflow-x-auto pb-1">
                      {schedule.phases.map((phase, index) => (
                        <li
                          key={phase.id}
                          className={`min-w-[180px] shrink-0 rounded-md border px-3 py-3 ${
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
                          <p className="mt-1 text-sm font-medium">{phase.name}</p>
                          <p
                            className={`mt-2 text-xs ${index === 0 ? "text-zinc-400" : "text-zinc-500"}`}
                          >
                            {phase.planned_start || "?"} →{" "}
                            {phase.planned_end || "?"}
                          </p>
                        </li>
                      ))}
                    </ul>
                  </section>

                  <section>
                    <h2 className="text-sm font-medium uppercase tracking-wide text-zinc-500">
                      工作项安排
                    </h2>
                    <div className="mt-3 overflow-x-auto">
                      <table className="w-full min-w-[720px] border-collapse text-left text-sm">
                        <thead>
                          <tr className="border-b border-zinc-200 text-xs text-zinc-500">
                            <th className="py-2 pr-3 font-medium">阶段 / 工作项</th>
                            <th className="py-2 pr-3 font-medium">负责人</th>
                            <th className="py-2 pr-3 font-medium">计划开始</th>
                            <th className="py-2 pr-3 font-medium">计划结束</th>
                            <th className="py-2 pr-3 font-medium">估时(h)</th>
                            <th className="py-2 font-medium">状态</th>
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
                              memberLabel={memberLabel}
                              onPatch={patchItem}
                            />
                          ))}
                        </tbody>
                      </table>
                    </div>
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
  memberLabel,
  onPatch,
}: {
  phaseName: string;
  items: CycleSchedule["phases"][number]["work_items"];
  members: TeamMember[];
  busyItemId: string | null;
  memberLabel: (id: string | null) => string;
  onPatch: (
    itemId: string,
    input: Parameters<typeof updateWorkItem>[4],
  ) => Promise<void>;
}) {
  return (
    <>
      <tr className="border-b border-zinc-100 bg-zinc-50/80">
        <td colSpan={6} className="py-2 pr-3 text-xs font-medium text-zinc-600">
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
            <td className="py-2">
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
          </tr>
        );
      })}
    </>
  );
}
