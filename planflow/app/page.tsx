import { Show } from "@clerk/nextjs";
import Link from "next/link";

export default function Home() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center px-6 py-20">
      <div className="max-w-xl text-center">
        <p className="mb-3 text-sm font-medium uppercase tracking-[0.2em] text-zinc-500">
          Team Portfolio
        </p>
        <h1 className="text-4xl font-semibold tracking-tight text-zinc-900">
          PlanFlow
        </h1>
        <p className="mt-4 text-base leading-7 text-zinc-600">
          团队版项目组合与排期协作。先完成注册/登录，确认账号可用后，再接入
          FastAPI 与 PostgreSQL。
        </p>

        <Show when="signed-out">
          <div className="mt-8 flex items-center justify-center gap-3">
            <Link
              href="/sign-up"
              className="rounded-md bg-zinc-900 px-5 py-2.5 text-sm font-medium text-white hover:bg-zinc-800"
            >
              注册账号
            </Link>
            <Link
              href="/sign-in"
              className="rounded-md border border-zinc-300 px-5 py-2.5 text-sm font-medium text-zinc-800 hover:bg-zinc-50"
            >
              已有账号登录
            </Link>
          </div>
        </Show>

        <Show when="signed-in">
          <p className="mt-8 rounded-md bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
            登录成功。后端已就绪；下一步会做「我的团队」页面（用你的登录
            token 调用 API）。
          </p>
        </Show>
      </div>
    </main>
  );
}
