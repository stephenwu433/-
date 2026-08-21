"use client";

import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { useParams } from "next/navigation";
import { FormEvent, useCallback, useEffect, useState } from "react";

import {
  getDailyReport,
  saveDailyReport,
  type DailyReport,
} from "@/lib/daily-report-api";
import { listMyTeams } from "@/lib/teams-api";

const STATUS_LABELS: Record<string, string> = {
  todo: "待办",
  doing: "进行中",
  done: "已完成",
};

function todayIso() {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function formatCnDate(iso: string) {
  const [, m, d] = iso.split("-");
  if (!m || !d) return iso;
  return `${Number(m)}月${Number(d)}日`;
}

export default function ProjectDailyReportPage() {
  const { isLoaded, isSignedIn, getToken } = useAuth();
  const params = useParams<{ teamId: string; projectId: string }>();
  const teamId = typeof params.teamId === "string" ? params.teamId : "";
  const projectId = typeof params.projectId === "string" ? params.projectId : "";

  const [viewDate, setViewDate] = useState(todayIso);
  const [report, setReport] = useState<DailyReport | null>(null);
  const [summary, setSummary] = useState("");
  const [nextActions, setNextActions] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedMsg, setSavedMsg] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setError(null);
    setSavedMsg(null);
    const token = await getToken();
    if (!token) {
      setError("拿不到登录 token。请重新登录。");
      return;
    }
    const teams = await listMyTeams(token);
    if (!teams.teams.some((t) => t.id === teamId)) {
      setError("你不是这个团队的成员。");
      setReport(null);
      return;
    }
    const payload = await getDailyReport(token, teamId, projectId, viewDate);
    setReport(payload);
    setSummary(payload.summary_text || payload.auto_summary);
    setNextActions(payload.next_actions || "");
  }, [getToken, teamId, projectId, viewDate]);

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

  async function onSave(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSavedMsg(null);
    try {
      const token = await getToken();
      if (!token) throw new Error("拿不到登录 token");
      const payload = await saveDailyReport(
        token,
        teamId,
        projectId,
        {
          summary_text: summary,
          next_actions: nextActions,
        },
        viewDate,
      );
      setReport(payload);
      setSummary(payload.summary_text || payload.auto_summary);
      setNextActions(payload.next_actions || "");
      setSavedMsg("日报已保存。");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col px-6 py-10">
      <p className="text-sm text-zinc-500">
        <Link
          href={`/teams/${teamId}/projects/${projectId}`}
          className="underline hover:text-zinc-800"
        >
          ← 返回项目
        </Link>
        {" · "}
        <Link
          href={`/teams/${teamId}/projects/${projectId}/daily`}
          className="underline hover:text-zinc-800"
        >
          每日任务
        </Link>
        {" · "}
        <Link href="/portfolio" className="underline hover:text-zinc-800">
          项目总览
        </Link>
      </p>
      <p className="mt-3 text-xs font-medium uppercase tracking-[0.16em] text-zinc-500">
        Daily Project Report
      </p>
      <h1 className="mt-1 text-2xl font-semibold tracking-tight text-zinc-900">
        {report?.project_name || "项目"} · 项目日报
      </h1>
      <p className="mt-2 text-sm leading-6 text-zinc-600">
        汇总所选日期的任务与实际工时；可补充进展摘要和下一步。
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
          <label className="flex w-fit flex-col gap-1 text-xs text-zinc-500">
            查看日期
            <input
              type="date"
              value={viewDate}
              onChange={(e) => setViewDate(e.target.value)}
              className="rounded-md border border-zinc-300 px-3 py-2 text-sm text-zinc-900"
            />
          </label>

          {error ? (
            <p className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
              {error}
            </p>
          ) : null}
          {savedMsg ? (
            <p className="rounded-md border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900">
              {savedMsg}
            </p>
          ) : null}

          {loading || !report ? (
            <p className="text-sm text-zinc-500">生成日报…</p>
          ) : (
            <>
              <section className="rounded-md bg-zinc-900 px-5 py-5 text-white">
                <p className="text-xs uppercase tracking-wide text-zinc-400">
                  {formatCnDate(report.view_date)} · 项目进展概况
                </p>
                <p className="mt-3 text-sm leading-6 text-zinc-100">
                  {report.summary_text || report.auto_summary}
                </p>
                <div className="mt-5 flex flex-wrap items-end justify-between gap-3">
                  <p className="text-xs text-zinc-400">
                    当日任务 {report.day_task_count} · 已填工时{" "}
                    {report.day_logged_hours}h · 完成 {report.done_tasks}/
                    {report.total_tasks}
                  </p>
                  <p className="text-3xl font-semibold tabular-nums">
                    {report.progress_percent}%
                  </p>
                </div>
              </section>

              <section>
                <h2 className="text-sm font-medium uppercase tracking-wide text-zinc-500">
                  当日任务
                </h2>
                {report.work_items.length === 0 ? (
                  <p className="mt-3 text-sm text-zinc-500">
                    当天没有项目任务日志。可去每日任务页添加或填工时。
                  </p>
                ) : (
                  <ul className="mt-3 divide-y divide-zinc-200 border-t border-b border-zinc-200">
                    {report.work_items.map((item) => (
                      <li
                        key={item.task_id}
                        className="flex flex-col gap-1 py-3 sm:flex-row sm:items-center sm:justify-between"
                      >
                        <div className="min-w-0">
                          <p className="text-sm font-medium text-zinc-900">
                            {item.title}
                          </p>
                          <p className="text-xs text-zinc-500">
                            {item.assignee_display_name || "未指派"} ·{" "}
                            {STATUS_LABELS[item.status] || item.status}
                            {item.notes.length
                              ? ` · ${item.notes.join("；")}`
                              : ""}
                          </p>
                        </div>
                        <p className="shrink-0 text-sm tabular-nums text-zinc-700">
                          {item.logged_hours}h
                        </p>
                      </li>
                    ))}
                  </ul>
                )}
              </section>

              <form onSubmit={onSave} className="space-y-4">
                <h2 className="text-sm font-medium uppercase tracking-wide text-zinc-500">
                  编辑日报
                </h2>
                <label className="flex flex-col gap-1 text-xs text-zinc-500">
                  进展摘要
                  <textarea
                    value={summary}
                    onChange={(e) => setSummary(e.target.value)}
                    rows={4}
                    maxLength={4000}
                    className="rounded-md border border-zinc-300 px-3 py-2 text-sm text-zinc-900 outline-none focus:border-zinc-500"
                  />
                </label>
                <label className="flex flex-col gap-1 text-xs text-zinc-500">
                  下一步（每行一条）
                  <textarea
                    value={nextActions}
                    onChange={(e) => setNextActions(e.target.value)}
                    rows={4}
                    maxLength={4000}
                    placeholder={"1. 完成接口联调\n2. 同步风险给负责人"}
                    className="rounded-md border border-zinc-300 px-3 py-2 text-sm text-zinc-900 outline-none focus:border-zinc-500"
                  />
                </label>
                {nextActions.trim() ? (
                  <div>
                    <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
                      下一步预览
                    </p>
                    <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm text-zinc-800">
                      {nextActions
                        .split("\n")
                        .map((line) => line.trim())
                        .filter(Boolean)
                        .map((line) => (
                          <li key={line}>{line.replace(/^\d+[\.\、]\s*/, "")}</li>
                        ))}
                    </ol>
                  </div>
                ) : null}
                <button
                  type="submit"
                  disabled={saving}
                  className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 disabled:opacity-50"
                >
                  {saving ? "保存中…" : "保存项目日报"}
                </button>
              </form>
            </>
          )}
        </div>
      )}
    </main>
  );
}
