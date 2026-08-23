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
          团队版项目组合与排期协作：管理项目、全周期排期、每日任务与负荷一览。
          登录后即可直接使用，无需自行搭建服务。
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
          <div className="mt-8 flex flex-col items-center gap-3">
            <p className="rounded-md bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
              登录成功。可以从项目总览开始，或先管理团队。
            </p>
            <div className="flex flex-wrap items-center justify-center gap-3">
              <Link
                href="/my-day"
                className="rounded-md bg-zinc-900 px-5 py-2.5 text-sm font-medium text-white hover:bg-zinc-800"
              >
                我的今日任务
              </Link>
              <Link
                href="/team-day"
                className="rounded-md border border-zinc-300 px-5 py-2.5 text-sm font-medium text-zinc-800 hover:bg-zinc-50"
              >
                团队今日看板
              </Link>
              <Link
                href="/portfolio"
                className="rounded-md border border-zinc-300 px-5 py-2.5 text-sm font-medium text-zinc-800 hover:bg-zinc-50"
              >
                打开项目总览
              </Link>
              <Link
                href="/workload"
                className="rounded-md border border-zinc-300 px-5 py-2.5 text-sm font-medium text-zinc-800 hover:bg-zinc-50"
              >
                跨项目负荷
              </Link>
              <Link
                href="/teams"
                className="rounded-md border border-zinc-300 px-5 py-2.5 text-sm font-medium text-zinc-800 hover:bg-zinc-50"
              >
                我的团队
              </Link>
            </div>
          </div>
        </Show>
      </div>
    </main>
  );
}
