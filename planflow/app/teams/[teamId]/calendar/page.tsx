"use client";

import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { listSchedule } from "@/lib/members-api";
import type { Project } from "@/lib/projects-api";
import { listMyTeams, type Team } from "@/lib/teams-api";

function startOfMonth(d: Date) {
  return new Date(d.getFullYear(), d.getMonth(), 1);
}

function addMonths(d: Date, n: number) {
  return new Date(d.getFullYear(), d.getMonth() + n, 1);
}

function ymd(d: Date) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

export default function TeamCalendarPage() {
  const { isLoaded, isSignedIn, getToken } = useAuth();
  const params = useParams<{ teamId: string }>();
  const teamId = typeof params.teamId === "string" ? params.teamId : "";

  const [team, setTeam] = useState<Team | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [cursor, setCursor] = useState(() => startOfMonth(new Date()));
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setError(null);
    const token = await getToken();
    if (!token) {
      setError("拿不到登录 token。");
      return;
    }
    const teams = await listMyTeams(token);
    const matched = teams.teams.find((t) => t.id === teamId) ?? null;
    setTeam(matched);
    if (!matched) {
      setError("找不到这个团队，或你不是成员。");
      setProjects([]);
      return;
    }
    const schedule = await listSchedule(token, teamId);
    setProjects(schedule.projects);
  }, [getToken, teamId]);

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

  const cells = useMemo(() => {
    const first = startOfMonth(cursor);
    const startWeekday = first.getDay(); // 0 Sun
    const daysInMonth = new Date(
      cursor.getFullYear(),
      cursor.getMonth() + 1,
      0,
    ).getDate();
    const blanks = Array.from({ length: startWeekday }, () => null);
    const days = Array.from({ length: daysInMonth }, (_, i) => i + 1);
    return [...blanks, ...days];
  }, [cursor]);

  function projectsOnDay(day: number) {
    const key = ymd(new Date(cursor.getFullYear(), cursor.getMonth(), day));
    return projects.filter((p) => {
      if (!p.planned_start) return false;
      const start = p.planned_start;
      const end = p.planned_end || p.planned_start;
      return start <= key && key <= end;
    });
  }

  const title = `${cursor.getFullYear()}年${cursor.getMonth() + 1}月`;

  return (
    <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col px-6 py-10">
      <p className="text-sm text-zinc-500">
        <Link href={`/teams/${teamId}`} className="underline hover:text-zinc-800">
          ← 返回团队项目
        </Link>
      </p>
      <h1 className="mt-3 text-2xl font-semibold tracking-tight text-zinc-900">
        排期日历
      </h1>
      <p className="mt-2 text-sm text-zinc-600">
        显示已设置起止日期的项目。可在团队项目页给项目填排期。
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
        <div className="mt-8 space-y-4">
          {team ? (
            <p className="text-sm font-medium text-zinc-800">{team.name}</p>
          ) : null}

          <div className="flex items-center justify-between gap-3">
            <button
              type="button"
              className="rounded-md border border-zinc-300 px-3 py-1.5 text-sm"
              onClick={() => setCursor((c) => addMonths(c, -1))}
            >
              上个月
            </button>
            <p className="text-sm font-medium text-zinc-900">{title}</p>
            <button
              type="button"
              className="rounded-md border border-zinc-300 px-3 py-1.5 text-sm"
              onClick={() => setCursor((c) => addMonths(c, 1))}
            >
              下个月
            </button>
          </div>

          {error ? (
            <p className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
              {error}
            </p>
          ) : null}

          {loading ? (
            <p className="text-sm text-zinc-500">加载中…</p>
          ) : (
            <>
              <div className="grid grid-cols-7 gap-px overflow-hidden rounded-md border border-zinc-200 bg-zinc-200 text-center text-xs">
                {["日", "一", "二", "三", "四", "五", "六"].map((d) => (
                  <div key={d} className="bg-zinc-50 py-2 font-medium text-zinc-600">
                    {d}
                  </div>
                ))}
                {cells.map((day, idx) => {
                  if (day == null) {
                    return <div key={`b-${idx}`} className="min-h-24 bg-white" />;
                  }
                  const items = projectsOnDay(day);
                  return (
                    <div
                      key={day}
                      className="min-h-24 bg-white p-1 text-left"
                    >
                      <p className="px-1 text-[11px] text-zinc-500">{day}</p>
                      <ul className="mt-1 space-y-1">
                        {items.slice(0, 3).map((p) => (
                          <li
                            key={p.id}
                            className="truncate rounded bg-zinc-900/90 px-1 py-0.5 text-[10px] text-white"
                            title={`${p.name} (${p.planned_start} ~ ${p.planned_end || p.planned_start})`}
                          >
                            {p.name}
                          </li>
                        ))}
                        {items.length > 3 ? (
                          <li className="px-1 text-[10px] text-zinc-500">
                            +{items.length - 3}
                          </li>
                        ) : null}
                      </ul>
                    </div>
                  );
                })}
              </div>

              <section>
                <h2 className="text-sm font-medium text-zinc-500">本月相关项目</h2>
                {projects.length === 0 ? (
                  <p className="mt-2 text-sm text-zinc-500">
                    还没有排期。去团队项目页给项目设置起止日期。
                  </p>
                ) : (
                  <ul className="mt-2 divide-y divide-zinc-200 border-t border-b border-zinc-200">
                    {projects.map((p) => (
                      <li key={p.id} className="py-2 text-sm">
                        <span className="font-medium text-zinc-900">{p.name}</span>
                        <span className="ml-2 text-xs text-zinc-500">
                          {p.planned_start}
                          {p.planned_end ? ` → ${p.planned_end}` : ""}
                          {" · "}
                          {p.status}
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </section>
            </>
          )}
        </div>
      )}
    </main>
  );
}
