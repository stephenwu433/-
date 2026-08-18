"use client";

import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";

import { createTeam, listMyTeams, type Team } from "@/lib/teams-api";

/**
 * 「我的团队」——登录后才能用。
 * 步骤：拿 Clerk token → 调后端 /teams → 显示列表 / 创建团队。
 */
export default function TeamsPage() {
  const { isLoaded, isSignedIn } = useAuth();

  return (
    <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col px-6 py-10">
      <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">
        我的团队
      </h1>
      <p className="mt-2 text-sm leading-6 text-zinc-600">
        这里会调用后端 <code className="text-zinc-800">/teams</code>
        ：先校验你的登录身份，再创建或查看属于你的团队。
      </p>

      {!isLoaded ? (
        <p className="mt-8 text-sm text-zinc-500">正在确认登录状态…</p>
      ) : !isSignedIn ? (
        <div className="mt-8 rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          请先{" "}
          <Link href="/sign-in" className="font-medium underline">
            登录
          </Link>{" "}
          或{" "}
          <Link href="/sign-up" className="font-medium underline">
            注册
          </Link>
          ，然后再创建团队。
        </div>
      ) : (
        <TeamsPanel />
      )}
    </main>
  );
}

function TeamsPanel() {
  const { getToken, isLoaded } = useAuth();
  const [teams, setTeams] = useState<Team[]>([]);
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setError(null);
    const token = await getToken();
    if (!token) {
      setError("拿不到登录 token。请重新登录后再试。");
      setTeams([]);
      return;
    }
    const data = await listMyTeams(token);
    setTeams(data.teams);
  }, [getToken]);

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
      await createTeam(token, trimmed);
      setName("");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="mt-8 space-y-8">
      <form onSubmit={onCreate} className="flex flex-col gap-3 sm:flex-row">
        <label className="sr-only" htmlFor="team-name">
          团队名称
        </label>
        <input
          id="team-name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="例如：产品一组"
          maxLength={80}
          className="min-w-0 flex-1 rounded-md border border-zinc-300 px-3 py-2 text-sm text-zinc-900 outline-none focus:border-zinc-500"
        />
        <button
          type="submit"
          disabled={saving || !name.trim()}
          className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {saving ? "创建中…" : "创建团队"}
        </button>
      </form>

      {error ? (
        <p className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          {error}
          <span className="mt-2 block text-red-700/80">
            提示：后端需配置相同的 Clerk Publishable Key，且
            PLANFLOW_AUTH_MODE=clerk（不要用 DEV 模式联调真登录）。
          </span>
        </p>
      ) : null}

      <section>
        <h2 className="text-sm font-medium uppercase tracking-wide text-zinc-500">
          团队列表
        </h2>
        {loading ? (
          <p className="mt-3 text-sm text-zinc-500">加载中…</p>
        ) : teams.length === 0 ? (
          <p className="mt-3 text-sm text-zinc-500">
            还没有团队。在上面输入名称，点「创建团队」。
          </p>
        ) : (
          <ul className="mt-3 divide-y divide-zinc-200 border-t border-b border-zinc-200">
            {teams.map((team) => (
              <li
                key={team.id}
                className="flex items-center justify-between gap-4 py-3"
              >
                <div>
                  <p className="text-sm font-medium text-zinc-900">{team.name}</p>
                  <p className="text-xs text-zinc-500">
                    {team.slug} · {team.role}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
