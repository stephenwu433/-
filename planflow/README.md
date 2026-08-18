# PlanFlow（前端）

Next.js + Clerk 登录骨架。当前为开发用 keyless Clerk 应用；本地 `.env.local` 已写入密钥（不会提交到 Git）。

## 本地启动

```bash
cd planflow
npm install
npm run dev
```

打开 http://localhost:3000 ，右上角可「注册 / 登录」。

## 接后端地址（已完成这一步）

在 `.env.local` 里可加（不写也有默认值）：

```bash
NEXT_PUBLIC_PLANFLOW_API_URL=http://127.0.0.1:8000
```

代码里用 `lib/api.ts` 的 `getApiBaseUrl()` 读取。后端已开 CORS，浏览器才能从 `:3000` 访问 `:8000`。

## 下一步（团队版）

1. 登录后做「我的团队」页：用 Clerk `getToken()` 调 `POST/GET /teams`  
2. 需要接到你自己的 Clerk 应用时，替换 `.env.local` 里的密钥  

