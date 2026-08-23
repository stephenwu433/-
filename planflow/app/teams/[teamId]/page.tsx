"use client";

import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { useParams } from "next/navigation";
import { FormEvent, useCallback, useEffect, useState } from "react";

import {
  createInvite,
  listInvites,
  listMembers,
  updateMemberDisplayName,
  updateMemberJobTitle,
  JOB_TITLE_LABELS,
  type Invite,
  type JobTitle,
  type TeamMember,
} from "@/lib/members-api";
import {
  createProject,
  listTeamProjects,
  updateProjectSchedule,
  updateProjectStatus,
  type Project,
  type ProjectStatus,
} from "@/lib/projects-api";
import { listMyTeams, type Team } from "@/lib/teams-api";

const DEFAULT_DAILY_HOURS = 6;

const STATUS_LABELS: Record<ProjectStatus, string> = {
  active: "进行中",
  paused: "已暂停",
  done: "已完成",
};

export default function TeamProjectsPage() {
  const { isLoaded, isSignedIn } = useAuth();
  const params = useParams<{ teamId: string }>();
  const teamId = typeof params.teamId === "string" ? params.teamId : "";

  return (
    <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col px-6 py-10">
      <p className="text-sm text-zinc-500">
        <Link href="/teams" className="underline hover:text-zinc-800">
          ← 返回我的团队
        </Link>
        {" · "}
        <Link href="/portfolio" className="underline hover:text-zinc-800">
          项目总览
        </Link>
      </p>
      <div className="mt-3 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">
            团队项目
          </h1>
          <p className="mt-2 text-sm leading-6 text-zinc-600">
            管理项目设置、成员邀请，以及排期日期。
          </p>
        </div>
        {teamId ? (
          <Link
            href={`/teams/${teamId}/calendar`}
            className="rounded-md border border-zinc-300 px-3 py-1.5 text-sm text-zinc-800 hover:bg-zinc-50"
          >
            打开排期日历
          </Link>
        ) : null}
      </div>

      {!isLoaded ? (
        <p className="mt-8 text-sm text-zinc-500">正在确认登录状态…</p>
      ) : !isSignedIn ? (
        <div className="mt-8 rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          请先{" "}
          <Link href="/sign-in" className="font-medium underline">
            登录
          </Link>{" "}
          后再查看项目。
        </div>
      ) : !teamId ? (
        <p className="mt-8 text-sm text-red-700">缺少团队 ID。</p>
      ) : (
        <TeamProjectsPanel teamId={teamId} />
      )}
    </main>
  );
}

function TeamProjectsPanel({ teamId }: { teamId: string }) {
  const { getToken, isLoaded } = useAuth();
  const [team, setTeam] = useState<Team | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [invites, setInvites] = useState<Invite[]>([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [objective, setObjective] = useState("");
  const [plannedStart, setPlannedStart] = useState("");
  const [plannedEnd, setPlannedEnd] = useState("");
  const [ownerUserId, setOwnerUserId] = useState("");
  const [dailyHours, setDailyHours] = useState(String(DEFAULT_DAILY_HOURS));
  const [inviteEmail, setInviteEmail] = useState("");
  const [latestInvitePath, setLatestInvitePath] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [inviting, setInviting] = useState(false);
  const [updatingId, setUpdatingId] = useState<string | null>(null);
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [renameDraft, setRenameDraft] = useState("");
  const [error, setError] = useState<string | null>(null);

  const canManageInvites = team?.role === "owner" || team?.role === "admin";

  const refresh = useCallback(async () => {
    setError(null);
    const token = await getToken();
    if (!token) {
      setError("拿不到登录 token。请重新登录后再试。");
      setTeam(null);
      setProjects([]);
      return;
    }

    const teamsPayload = await listMyTeams(token);
    const matched = teamsPayload.teams.find((item) => item.id === teamId) ?? null;
    setTeam(matched);
    if (!matched) {
      setProjects([]);
      setMembers([]);
      setInvites([]);
      setError("找不到这个团队，或你不是成员。请回到「我的团队」再选一次。");
      return;
    }

    const [projectData, memberData] = await Promise.all([
      listTeamProjects(token, teamId),
      listMembers(token, teamId),
    ]);
    setProjects(projectData.projects);
    setMembers(memberData.members);

    if (matched.role === "owner" || matched.role === "admin") {
      try {
        const inviteData = await listInvites(token, teamId);
        setInvites(inviteData.invites.filter((i) => i.status === "pending"));
      } catch {
        setInvites([]);
      }
    } else {
      setInvites([]);
    }
  }, [getToken, teamId]);

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

  async function onCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) return;

    setSaving(true);
    setError(null);
    try {
      const token = await getToken();
      if (!token) {
        setError("拿不到登录 token。请重新登录后再试。");
        return;
      }
      const hours = Number(dailyHours);
      await createProject(token, teamId, {
        name: trimmed,
        description,
        objective,
        planned_start: plannedStart || undefined,
        planned_end: plannedEnd || undefined,
        owner_user_id: ownerUserId || undefined,
        member_daily_hours:
          Number.isFinite(hours) && hours >= 0 ? hours : DEFAULT_DAILY_HOURS,
      });
      setName("");
      setDescription("");
      setObjective("");
      setPlannedStart("");
      setPlannedEnd("");
      setOwnerUserId("");
      setDailyHours(String(DEFAULT_DAILY_HOURS));
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  }

  async function onStatusChange(projectId: string, status: ProjectStatus) {
    setUpdatingId(projectId);
    setError(null);
    try {
      const token = await getToken();
      if (!token) {
        setError("拿不到登录 token。请重新登录后再试。");
        return;
      }
      const updated = await updateProjectStatus(token, teamId, projectId, status);
      setProjects((prev) =>
        prev.map((item) => (item.id === updated.id ? updated : item)),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setUpdatingId(null);
    }
  }

  async function onScheduleChange(
    projectId: string,
    start: string,
    end: string,
  ) {
    setUpdatingId(projectId);
    setError(null);
    try {
      const token = await getToken();
      if (!token) {
        setError("拿不到登录 token。请重新登录后再试。");
        return;
      }
      const updated = await updateProjectSchedule(
        token,
        teamId,
        projectId,
        start || null,
        end || null,
      );
      setProjects((prev) =>
        prev.map((item) => (item.id === updated.id ? updated : item)),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setUpdatingId(null);
    }
  }

  async function onCreateInvite(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setInviting(true);
    setError(null);
    try {
      const token = await getToken();
      if (!token) {
        setError("拿不到登录 token。请重新登录后再试。");
        return;
      }
      const invite = await createInvite(token, teamId, {
        email: inviteEmail.trim() || undefined,
        role: "member",
      });
      setLatestInvitePath(invite.invite_path);
      setInviteEmail("");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setInviting(false);
    }
  }

  return (
    <div className="mt-8 space-y-10">
      {team ? (
        <div>
          <p className="text-lg font-medium text-zinc-900">{team.name}</p>
          <p className="text-xs text-zinc-500">
            {team.slug} · {team.role}
          </p>
        </div>
      ) : null}

      <section className="space-y-3">
        <h2 className="text-sm font-medium uppercase tracking-wide text-zinc-500">
          成员
        </h2>
        {loading ? (
          <p className="text-sm text-zinc-500">加载中…</p>
        ) : (
          <ul className="divide-y divide-zinc-200 border-t border-b border-zinc-200">
            {members.map((m) => (
              <li
                key={m.user_id}
                className="flex flex-wrap items-center justify-between gap-3 py-2 text-sm"
              >
                <div className="min-w-0 flex-1">
                  {renamingId === m.user_id ? (
                    <form
                      className="flex flex-wrap items-center gap-2"
                      onSubmit={async (e) => {
                        e.preventDefault();
                        setSaving(true);
                        setError(null);
                        try {
                          const token = await getToken();
                          if (!token) throw new Error("拿不到登录 token");
                          const updated = await updateMemberDisplayName(
                            token,
                            teamId,
                            m.user_id,
                            renameDraft.trim(),
                          );
                          setMembers((prev) =>
                            prev.map((x) =>
                              x.user_id === m.user_id
                                ? { ...x, display_name: updated.display_name }
                                : x,
                            ),
                          );
                          setRenamingId(null);
                        } catch (err) {
                          setError(
                            err instanceof Error ? err.message : String(err),
                          );
                        } finally {
                          setSaving(false);
                        }
                      }}
                    >
                      <input
                        value={renameDraft}
                        onChange={(e) => setRenameDraft(e.target.value)}
                        placeholder="显示名"
                        maxLength={80}
                        className="min-w-0 flex-1 rounded-md border border-zinc-300 px-2 py-1 text-sm outline-none focus:border-zinc-500"
                        autoFocus
                      />
                      <button
                        type="submit"
                        disabled={saving || !renameDraft.trim()}
                        className="rounded-md bg-zinc-900 px-2 py-1 text-xs text-white disabled:opacity-50"
                      >
                        保存
                      </button>
                      <button
                        type="button"
                        disabled={saving}
                        onClick={() => setRenamingId(null)}
                        className="rounded-md border border-zinc-300 px-2 py-1 text-xs text-zinc-700"
                      >
                        取消
                      </button>
                    </form>
                  ) : (
                    <span className="text-zinc-900">
                      {m.display_name || m.email || m.clerk_user_id}
                      <span className="ml-2 text-xs text-zinc-400">{m.role}</span>
                      <button
                        type="button"
                        disabled={saving}
                        onClick={() => {
                          setRenamingId(m.user_id);
                          setRenameDraft(m.display_name || "");
                        }}
                        className="ml-2 text-xs text-zinc-500 underline hover:text-zinc-800"
                      >
                        改名
                      </button>
                    </span>
                  )}
                </div>
                <select
                  value={m.job_title || ""}
                  disabled={saving}
                  onChange={async (e) => {
                    setSaving(true);
                    setError(null);
                    try {
                      const token = await getToken();
                      if (!token) throw new Error("拿不到登录 token");
                      const updated = await updateMemberJobTitle(
                        token,
                        teamId,
                        m.user_id,
                        e.target.value || null,
                      );
                      setMembers((prev) =>
                        prev.map((x) =>
                          x.user_id === m.user_id
                            ? { ...x, job_title: updated.job_title }
                            : x,
                        ),
                      );
                    } catch (err) {
                      setError(err instanceof Error ? err.message : String(err));
                    } finally {
                      setSaving(false);
                    }
                  }}
                  className="rounded-md border border-zinc-300 px-2 py-1 text-xs"
                >
                  <option value="">未设置岗位</option>
                  {(Object.keys(JOB_TITLE_LABELS) as JobTitle[]).map((key) => (
                    <option key={key} value={key}>
                      {JOB_TITLE_LABELS[key]}
                    </option>
                  ))}
                </select>
              </li>
            ))}
          </ul>
        )}
      </section>

      {canManageInvites ? (
        <section className="space-y-3">
          <h2 className="text-sm font-medium uppercase tracking-wide text-zinc-500">
            邀请成员
          </h2>
          <p className="text-sm text-zinc-600">
            生成邀请链接，发给同事。对方登录后打开链接即可加入。
          </p>
          <form onSubmit={onCreateInvite} className="flex flex-col gap-3 sm:flex-row">
            <input
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
              placeholder="对方邮箱（可选备注）"
              className="min-w-0 flex-1 rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500"
            />
            <button
              type="submit"
              disabled={inviting}
              className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 disabled:opacity-50"
            >
              {inviting ? "生成中…" : "生成邀请链接"}
            </button>
          </form>
          {latestInvitePath ? (
            <p className="break-all rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-900">
              邀请链接路径：{latestInvitePath}
              <br />
              完整地址：{typeof window !== "undefined" ? window.location.origin : ""}
              {latestInvitePath}
            </p>
          ) : null}
          {invites.length > 0 ? (
            <ul className="text-xs text-zinc-500">
              {invites.slice(0, 5).map((inv) => (
                <li key={inv.id}>
                  pending · {inv.invite_path}
                  {inv.email ? ` · ${inv.email}` : ""}
                </li>
              ))}
            </ul>
          ) : null}
        </section>
      ) : null}

      <form onSubmit={onCreate} className="space-y-3">
        <h2 className="text-sm font-medium uppercase tracking-wide text-zinc-500">
          创建项目
        </h2>
        <p className="text-sm text-zinc-600">
          填写名称、目标、排期、负责人与日人均工时。创建后可在项目页继续改设置。
        </p>
        <div className="flex flex-col gap-3 sm:flex-row">
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="项目名称，例如：Q3 官网改版"
            maxLength={120}
            className="min-w-0 flex-1 rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500"
          />
          <button
            type="submit"
            disabled={saving || !name.trim() || !team}
            className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 disabled:opacity-50"
          >
            {saving ? "创建中…" : "创建项目"}
          </button>
        </div>
        <input
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="简介（可选）"
          maxLength={2000}
          className="w-full rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500"
        />
        <textarea
          value={objective}
          onChange={(e) => setObjective(e.target.value)}
          placeholder="项目目标 / 成功标准（可选）"
          maxLength={4000}
          rows={3}
          className="w-full rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500"
        />
        <div className="flex flex-col gap-3 sm:flex-row">
          <label className="flex flex-1 flex-col gap-1 text-xs text-zinc-500">
            开始日期
            <input
              type="date"
              value={plannedStart}
              onChange={(e) => setPlannedStart(e.target.value)}
              className="rounded-md border border-zinc-300 px-3 py-2 text-sm text-zinc-900"
            />
          </label>
          <label className="flex flex-1 flex-col gap-1 text-xs text-zinc-500">
            结束日期
            <input
              type="date"
              value={plannedEnd}
              onChange={(e) => setPlannedEnd(e.target.value)}
              className="rounded-md border border-zinc-300 px-3 py-2 text-sm text-zinc-900"
            />
          </label>
        </div>
        <div className="flex flex-col gap-3 sm:flex-row">
          <label className="flex flex-1 flex-col gap-1 text-xs text-zinc-500">
            负责人
            <select
              value={ownerUserId}
              onChange={(e) => setOwnerUserId(e.target.value)}
              className="rounded-md border border-zinc-300 px-3 py-2 text-sm text-zinc-900"
            >
              <option value="">默认：我自己</option>
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
              value={dailyHours}
              onChange={(e) => setDailyHours(e.target.value)}
              className="rounded-md border border-zinc-300 px-3 py-2 text-sm text-zinc-900"
            />
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
          项目列表
        </h2>
        {loading ? (
          <p className="mt-3 text-sm text-zinc-500">加载中…</p>
        ) : projects.length === 0 ? (
          <p className="mt-3 text-sm text-zinc-500">还没有项目。</p>
        ) : (
          <ul className="mt-3 divide-y divide-zinc-200 border-t border-b border-zinc-200">
            {projects.map((project) => (
              <li key={project.id} className="space-y-3 py-4">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-zinc-900">{project.name}</p>
                    <p className="text-xs text-zinc-500">
                      {project.objective || project.description || "暂无目标/简介"}
                      {" · "}
                      {project.plan_confirmed ? "计划已确认" : "计划未确认"}
                      {" · "}
                      日人均 {project.member_daily_hours ?? DEFAULT_DAILY_HOURS}h
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Link
                      href={`/teams/${teamId}/projects/${project.id}`}
                      className="rounded-md border border-zinc-300 px-3 py-1.5 text-sm text-zinc-800 hover:bg-zinc-50"
                    >
                      任务 / 设置
                    </Link>
                    <select
                      value={
                        project.status === "paused" || project.status === "done"
                          ? project.status
                          : "active"
                      }
                      disabled={updatingId === project.id || !team}
                      onChange={(e) =>
                        onStatusChange(project.id, e.target.value as ProjectStatus)
                      }
                      className="rounded-md border border-zinc-300 bg-white px-2 py-1.5 text-sm disabled:opacity-50"
                    >
                      <option value="active">{STATUS_LABELS.active}</option>
                      <option value="paused">{STATUS_LABELS.paused}</option>
                      <option value="done">{STATUS_LABELS.done}</option>
                    </select>
                  </div>
                </div>
                <div className="flex flex-col gap-2 sm:flex-row sm:items-end">
                  <label className="flex flex-1 flex-col gap-1 text-xs text-zinc-500">
                    排期开始
                    <input
                      type="date"
                      defaultValue={project.planned_start ?? ""}
                      key={`${project.id}-start-${project.planned_start}`}
                      disabled={updatingId === project.id}
                      onBlur={(e) => {
                        const start = e.target.value;
                        const end = project.planned_end ?? "";
                        if (start === (project.planned_start ?? "")) return;
                        void onScheduleChange(project.id, start, end);
                      }}
                      className="rounded-md border border-zinc-300 px-2 py-1.5 text-sm text-zinc-900"
                    />
                  </label>
                  <label className="flex flex-1 flex-col gap-1 text-xs text-zinc-500">
                    排期结束
                    <input
                      type="date"
                      defaultValue={project.planned_end ?? ""}
                      key={`${project.id}-end-${project.planned_end}`}
                      disabled={updatingId === project.id}
                      onBlur={(e) => {
                        const end = e.target.value;
                        const start = project.planned_start ?? "";
                        if (end === (project.planned_end ?? "")) return;
                        void onScheduleChange(project.id, start, end);
                      }}
                      className="rounded-md border border-zinc-300 px-2 py-1.5 text-sm text-zinc-900"
                    />
                  </label>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
