# PlanFlow（前端）

Next.js + Clerk 登录骨架。当前为开发用 keyless Clerk 应用；本地 `.env.local` 已写入密钥（不会提交到 Git）。

## 本地启动

```bash
cd planflow
npm install
npm run dev
```

打开 http://localhost:3000 ，右上角可「注册 / 登录」。

## 下一步（团队版）

1. 你在页面上注册第一个测试账号  
2. 之后接 FastAPI + PostgreSQL，用 Clerk JWT 校验身份  
3. 需要接到你自己的 Clerk 应用时，在本机运行 `clerk auth login` 认领，或替换 `.env.local` 里的密钥  
