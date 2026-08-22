"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

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
  const nav = buildNav(teamId, projectId);

  return (
    <div className="flex min-h-0 flex-1">
      <aside className="flex w-56 shrink-0 flex-col border-r border-zinc-200 bg-zinc-50">
        <div className="border-b border-zinc-200 px-4 py-4">
          <p className="text-sm font-semibold tracking-tight text-zinc-900">
            PlanFlow
          </p>
          <p className="mt-0.5 text-xs text-zinc-500">项目工作台</p>
          {projectName ? (
            <p className="mt-2 truncate text-xs text-zinc-700">{projectName}</p>
          ) : null}
        </div>

        <nav className="flex flex-1 flex-col gap-0.5 px-2 py-3">
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

        <div className="border-t border-zinc-200 px-4 py-3">
          <p className="text-[11px] uppercase tracking-wide text-zinc-400">
            快捷入口
          </p>
          <div className="mt-2 flex flex-col gap-1">
            <Link
              href="/my-day"
              className="text-xs text-zinc-600 underline hover:text-zinc-900"
            >
              我的今日
            </Link>
            <Link
              href="/team-day"
              className="text-xs text-zinc-600 underline hover:text-zinc-900"
            >
              团队今日
            </Link>
            <Link
              href="/teams"
              className="text-xs text-zinc-600 underline hover:text-zinc-900"
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
