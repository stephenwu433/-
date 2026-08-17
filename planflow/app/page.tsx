import { Show } from "@clerk/nextjs";

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
          <p className="mt-8 text-sm text-zinc-500">
            请点击右上角「注册」创建第一个测试账号。
          </p>
        </Show>

        <Show when="signed-in">
          <p className="mt-8 rounded-md bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
            登录成功。下一步我们将搭建 FastAPI 后端，并把你的用户身份传给接口。
          </p>
        </Show>
      </div>
    </main>
  );
}
