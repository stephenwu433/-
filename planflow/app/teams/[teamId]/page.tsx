"use client";

import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { useParams } from "next/navigation";
import { FormEvent, useCallback, useEffect, useState } from "react";

import {
  createProject,
  listTeamProjects,
  updateProjectStatus,
  type Project,
  type ProjectStatus,
} from "@/lib/projects-api";
import { listMyTeams, type Team } from "@/lib/teams-api";

const STATUS_LABELS: Record<ProjectStatus, string> = {
  active: "进行中",
  paused: "已暂停",
  done: "已完成",
};

/**
 * 团队详情：在某个团队里创建 / 查看项目。
 * 路由：/teams/[teamId]
 */
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
      </p>
      <h1 className="mt-3 text-2xl font-semibold tracking-tight text-zinc-900">
        团队项目
      </h1>
      <p className="mt-2 text-sm leading-6 text-zinc-600">
        调用后端{" "}
        <code className="text-zinc-800">/teams/&#123;id&#125;/projects</code>
        ：只有该团队的成员才能创建和查看项目。
      </p>

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
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [updatingId, setUpdatingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

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
      setError("找不到这个团队，或你不是成员。请回到「我的团队」再选一次。");
      return;
    }

    const data = await listTeamProjects(token, teamId);
    setProjects(data.projects);
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
      await createProject(token, teamId, trimmed, description);
      setName("");
      setDescription("");
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

  return (
    <div className="mt-8 space-y-8">
      {team ? (
        <div>
          <p className="text-lg font-medium text-zinc-900">{team.name}</p>
          <p className="text-xs text-zinc-500">
            {team.slug} · {team.role}
          </p>
        </div>
      ) : null}

      <form onSubmit={onCreate} className="space-y-3">
        <div className="flex flex-col gap-3 sm:flex-row">
          <label className="sr-only" htmlFor="project-name">
            项目名称
          </label>
          <input
            id="project-name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="例如：Q3 官网改版"
            maxLength={120}
            className="min-w-0 flex-1 rounded-md border border-zinc-300 px-3 py-2 text-sm text-zinc-900 outline-none focus:border-zinc-500"
          />
          <button
            type="submit"
            disabled={saving || !name.trim() || !team}
            className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {saving ? "创建中…" : "创建项目"}
          </button>
        </div>
        <label className="sr-only" htmlFor="project-description">
          项目简介（可选）
        </label>
        <input
          id="project-description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="简介（可选）"
          maxLength={2000}
          className="w-full rounded-md border border-zinc-300 px-3 py-2 text-sm text-zinc-900 outline-none focus:border-zinc-500"
        />
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
          <p className="mt-3 text-sm text-zinc-500">
            还没有项目。在上面输入名称，点「创建项目」。
          </p>
        ) : (
          <ul className="mt-3 divide-y divide-zinc-200 border-t border-b border-zinc-200">
            {projects.map((project) => (
              <li
                key={project.id}
                className="flex flex-col gap-3 py-3 sm:flex-row sm:items-center sm:justify-between"
              >
                <div className="min-w-0">
                  <p className="text-sm font-medium text-zinc-900">{project.name}</p>
                  <p className="text-xs text-zinc-500">
                    {project.description ? project.description : "暂无简介"}
                  </p>
                </div>
                <label className="flex items-center gap-2 text-sm text-zinc-700">
                  <span className="sr-only">项目状态</span>
                  <select
                    value={
                      project.status === "paused" || project.status === "done"
                        ? project.status
                        : "active"
                    }
                    disabled={updatingId === project.id || !team}
                    onChange={(e) =>
                      onStatusChange(
                        project.id,
                        e.target.value as ProjectStatus,
                      )
                    }
                    className="rounded-md border border-zinc-300 bg-white px-2 py-1.5 text-sm outline-none focus:border-zinc-500 disabled:opacity-50"
                  >
                    <option value="active">{STATUS_LABELS.active}</option>
                    <option value="paused">{STATUS_LABELS.paused}</option>
                    <option value="done">{STATUS_LABELS.done}</option>
                  </select>
                </label>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
