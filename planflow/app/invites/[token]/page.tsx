"use client";

import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { acceptInvite, previewInvite, type InvitePreview } from "@/lib/members-api";

export default function AcceptInvitePage() {
  const params = useParams<{ token: string }>();
  const token = typeof params.token === "string" ? params.token : "";
  const { isLoaded, isSignedIn, getToken } = useAuth();
  const router = useRouter();

  const [preview, setPreview] = useState<InvitePreview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [accepting, setAccepting] = useState(false);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const data = await previewInvite(token);
        if (!cancelled) setPreview(data);
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
  }, [token]);

  async function onAccept() {
    setAccepting(true);
    setError(null);
    try {
      const authToken = await getToken();
      if (!authToken) {
        setError("拿不到登录 token，请重新登录。");
        return;
      }
      const member = await acceptInvite(authToken, token);
      router.push(`/teams/${preview?.team_id ?? ""}`);
      void member;
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setAccepting(false);
    }
  }

  return (
    <main className="mx-auto flex w-full max-w-lg flex-1 flex-col px-6 py-10">
      <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">
        加入团队
      </h1>
      <p className="mt-2 text-sm text-zinc-600">
        有人邀请你加入 PlanFlow 团队。登录后点「接受邀请」即可。
      </p>

      {loading ? (
        <p className="mt-8 text-sm text-zinc-500">加载邀请信息…</p>
      ) : preview ? (
        <div className="mt-8 space-y-4 rounded-md border border-zinc-200 p-4">
          <p className="text-lg font-medium text-zinc-900">{preview.team_name}</p>
          <p className="text-sm text-zinc-600">
            角色：{preview.role === "admin" ? "管理员" : "成员"}
          </p>
          <p className="text-xs text-zinc-500">
            有效期至 {new Date(preview.expires_at).toLocaleString()}
          </p>
          {preview.expired ? (
            <p className="text-sm text-red-700">此邀请已失效或已使用。</p>
          ) : !isLoaded ? (
            <p className="text-sm text-zinc-500">确认登录状态…</p>
          ) : !isSignedIn ? (
            <p className="text-sm text-amber-800">
              请先{" "}
              <Link href="/sign-in" className="underline">
                登录
              </Link>{" "}
              或{" "}
              <Link href="/sign-up" className="underline">
                注册
              </Link>
              ，再回来接受邀请。
            </p>
          ) : (
            <button
              type="button"
              disabled={accepting}
              onClick={onAccept}
              className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 disabled:opacity-50"
            >
              {accepting ? "加入中…" : "接受邀请"}
            </button>
          )}
        </div>
      ) : null}

      {error ? (
        <p className="mt-4 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          {error}
        </p>
      ) : null}
    </main>
  );
}
