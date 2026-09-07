"use client";

import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  FormEvent,
  type ReactNode,
  useCallback,
  useEffect,
  useState,
} from "react";

import {
  createProject,
  getPortfolio,
  type PortfolioProject,
} from "@/lib/projects-api";
import { listMyTeams } from "@/lib/teams-api";

type WorkbenchShellProps = {
  children: ReactNode;
  teamId?: string | null;
  projectId?: string | null;
  projectName?: string | null;
};

type NavItem = {
  key: string;
  label: string;
  href: string | null;
  match: (pathname: string) => boolean;
};

function buildNav(
  teamId?: string | null,
  projectId?: string | null,
): NavItem[] {
  const hasProject = Boolean(teamId && projectId);
  const base = hasProject
    ? `/teams/${teamId}/projects/${projectId}`
    : null;

  return [
    {
      key: "my-day",
      label: "我的今日",
      href: "/my-day",
      match: (p) => p === "/my-day" || p.startsWith("/my-day/"),
    },
    {
      key: "portfolio",
      label: "项目总览",
      href: "/portfolio",
      match: (p) => p === "/portfolio" || p.startsWith("/portfolio/"),
    },
    {
      key: "settings",
      label: "项目设置",
      href: base,
      match: (p) =>
        Boolean(base) &&
        (p === base || p === `${base}/`),
    },
    {
      key: "schedule",
      label: "全周期排期",
      href: base ? `${base}/schedule` : null,
      match: (p) => Boolean(base) && p.startsWith(`${base}/schedule`),
    },
    {
      key: "daily",
      label: "每日任务",
      href: base ? `${base}/daily` : null,
      match: (p) => Boolean(base) && p.startsWith(`${base}/daily`),
    },
    {
      key: "report",
      label: "项目日报",
      href: base ? `${base}/report` : null,
      match: (p) => Boolean(base) && p.startsWith(`${base}/report`),
    },
    {
      key: "workload",
      label: "跨项目负荷",
      href: "/workload",
      match: (p) => p === "/workload" || p.startsWith("/workload/"),
    },
    {
      key: "notifications",
      label: "站内提醒",
      href: base ? `${base}/notifications` : "/notifications",
      match: (p) =>
        p === "/notifications" ||
        p.startsWith("/notifications/") ||
        (Boolean(base) && p.startsWith(`${base}/notifications`)),
    },
  ];
}

export function WorkbenchShell({
  children,
  teamId,
  projectId,
  projectName,
}: WorkbenchShellProps) {
  const pathname = usePathname() || "";
  const router = useRouter();
  const { isLoaded, isSignedIn, getToken } = useAuth();
  const nav = buildNav(teamId, projectId);

  const [projects, setProjects] = useState<PortfolioProject[]>([]);
  const [portfolioLoading, setPortfolioLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState("");
  const [createError, setCreateError] = useState<string | null>(null);

  const refreshPortfolio = useCallback(async () => {
    if (!isSignedIn) {
      setProjects([]);
      return;
    }
    const token = await getToken();
    if (!token) return;
    const payload = await getPortfolio(token);
    setProjects(payload.projects);
  }, [getToken, isSignedIn]);

  useEffect(() => {
    if (!isLoaded || !isSignedIn) return;
    let cancelled = false;
    (async () => {
      setPortfolioLoading(true);
      try {
        await refreshPortfolio();
      } catch {
        if (!cancelled) setProjects([]);
      } finally {
        if (!cancelled) setPortfolioLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [isLoaded, isSignedIn, refreshPortfolio]);

  async function onCreateProject(e: FormEvent) {
    e.preventDefault();
    const name = newName.trim();
    if (!name) return;
    setCreating(true);
    setCreateError(null);
    try {
      const token = await getToken();
      if (!token) throw new Error("拿不到登录 token");
      const teams = await listMyTeams(token);
      if (teams.teams.length === 0) {
        throw new Error("请先创建或加入一个团队，再新建项目。");
      }
      const team =
        (teamId && teams.teams.find((t) => t.id === teamId)) ||
        (teams.teams.length === 1 ? teams.teams[0] : null) ||
        teams.teams[0];
      const created = await createProject(token, team.id, { name });
      setNewName("");
      setShowCreate(false);
      await refreshPortfolio();
      router.push(`/teams/${team.id}/projects/${created.id}`);
    } catch (err) {
      setCreateError(err instanceof Error ? err.message : String(err));
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="flex min-h-0 flex-1">
      <aside className="flex w-60 shrink-0 flex-col border-r border-zinc-200 bg-zinc-50">
        <div className="border-b border-zinc-200 px-4 py-4">
          <p className="text-sm font-semibold tracking-tight text-zinc-900">
            PlanFlow
          </p>
          <p className="mt-0.5 text-xs text-zinc-500">
            {projectName ? "当前项目" : "个人工作台"}
          </p>
          {projectName ? (
            <p className="mt-2 truncate text-xs text-zinc-700">{projectName}</p>
          ) : null}
        </div>

        <nav className="flex flex-col gap-0.5 border-b border-zinc-200 px-2 py-3">
          {nav.map((item) => {
            const active = item.href ? item.match(pathname) : false;
            const className = [
              "rounded-md px-3 py-2 text-sm",
              active
                ? "bg-zinc-900 text-white"
                : item.href
                  ? "text-zinc-700 hover:bg-zinc-100"
                  : "cursor-not-allowed text-zinc-400",
            ].join(" ");

            if (!item.href) {
              return (
                <span key={item.key} className={className} title="请先选择项目">
                  {item.label}
                </span>
              );
            }

            return (
              <Link key={item.key} href={item.href} className={className}>
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="flex min-h-0 flex-1 flex-col px-2 py-3">
          <div className="flex items-center justify-between gap-2 px-2">
            <p className="text-xs font-medium text-zinc-500">
              项目列表 · {portfolioLoading ? "…" : projects.length}
            </p>
            <button
              type="button"
              onClick={() => {
                setShowCreate((v) => !v);
                setCreateError(null);
              }}
              className="text-xs font-medium text-zinc-700 hover:text-zinc-900"
            >
              ＋ 新建项目
            </button>
          </div>

          {showCreate ? (
            <form
              onSubmit={onCreateProject}
              className="mt-2 space-y-2 rounded-md border border-zinc-200 bg-white px-2 py-2"
            >
              <input
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="项目名称"
                maxLength={120}
                autoFocus
                className="w-full rounded-md border border-zinc-300 px-2 py-1.5 text-xs outline-none focus:border-zinc-500"
              />
              {createError ? (
                <p className="text-[11px] text-red-700">{createError}</p>
              ) : null}
              <div className="flex gap-2">
                <button
                  type="submit"
                  disabled={creating || !newName.trim()}
                  className="rounded-md bg-zinc-900 px-2 py-1 text-xs font-medium text-white disabled:opacity-50"
                >
                  {creating ? "创建中…" : "创建"}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowCreate(false);
                    setCreateError(null);
                  }}
                  className="rounded-md border border-zinc-300 px-2 py-1 text-xs text-zinc-700"
                >
                  取消
                </button>
              </div>
            </form>
          ) : null}

          <ul className="mt-2 min-h-0 flex-1 space-y-0.5 overflow-auto">
            {!isSignedIn ? (
              <li className="px-2 py-1 text-xs text-zinc-400">登录后显示项目</li>
            ) : portfolioLoading && projects.length === 0 ? (
              <li className="px-2 py-1 text-xs text-zinc-400">加载中…</li>
            ) : projects.length === 0 ? (
              <li className="px-2 py-1 text-xs text-zinc-400">
                还没有项目
                <button
                  type="button"
                  onClick={() => {
                    setShowCreate(true);
                    setCreateError(null);
                  }}
                  className="ml-1 underline"
                >
                  立即新建
                </button>
              </li>
            ) : (
              projects.map((p) => {
                const active = p.id === projectId;
                return (
                  <li key={p.id}>
                    <Link
                      href={`/teams/${p.team_id}/projects/${p.id}`}
                      className={[
                        "block rounded-md px-2 py-1.5 text-xs",
                        active
                          ? "bg-zinc-200 font-medium text-zinc-900"
                          : "text-zinc-700 hover:bg-zinc-100",
                      ].join(" ")}
                    >
                      <span className="block truncate">{p.name}</span>
                      <span className="mt-0.5 block truncate text-[10px] text-zinc-500">
                        {p.plan_confirmed ? "计划已确认" : "计划未确认"}
                        {typeof p.progress_percent === "number"
                          ? ` · ${p.progress_percent}%`
                          : ""}
                      </span>
                    </Link>
                  </li>
                );
              })
            )}
          </ul>
        </div>

        <div className="border-t border-zinc-200 px-4 py-3">
          <Link
            href="/portfolio"
            className="block text-xs font-medium text-zinc-700 hover:text-zinc-900"
          >
            ▦ 返回项目总览
          </Link>
          <div className="mt-2 flex flex-col gap-1">
            <Link
              href="/team-day"
              className="text-[11px] text-zinc-500 underline hover:text-zinc-800"
            >
              团队今日
            </Link>
            <Link
              href="/teams"
              className="text-[11px] text-zinc-500 underline hover:text-zinc-800"
            >
              我的团队
            </Link>
          </div>
        </div>
      </aside>

      <div className="min-w-0 flex-1 overflow-auto">{children}</div>
    </div>
  );
}
