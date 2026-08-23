# PlanFlow 团队上线指南

目标：给团队一个**固定可访问的网址**（不是临时 tunnel）。

推荐组合（都可用免费档起步）：

| 部分 | 平台 | 说明 |
|------|------|------|
| 前端 | [Vercel](https://vercel.com) | 部署 `planflow/` |
| 后端 API | [Render](https://render.com) | 用仓库里的 `backend/Dockerfile` |
| 数据库 | Neon（已有） | 继续用现有 `DATABASE_URL` |
| 登录 | Clerk（已有） | 把正式前端域名加进允许列表 |

---

## 1. 部署后端（Render）

1. 打开 Render → **New → Blueprint**，连上本仓库，选用根目录 `render.yaml`；或 **New Web Service**，Root 选 `backend`，Runtime = Docker。
2. 环境变量（必填）：

```text
PLANFLOW_AUTH_MODE=clerk
DATABASE_URL=（Neon 连接串，带 sslmode=require）
CLERK_PUBLISHABLE_KEY=（与前端相同的 pk_…）
PLANFLOW_CORS_ORIGINS=https://你的前端域名
```

3. 部署成功后记下 API 地址，例如：`https://planflow-api.onrender.com`  
4. 浏览器打开 `https://…/health` 应返回 `"status":"ok"`。

> 首次启动会自动跑 `scripts/migrate.py` 建表。

---

## 2. 部署前端（Vercel）

1. Vercel → Import 本仓库，**Root Directory** 设为 `planflow`。
2. 环境变量：

```text
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_…
CLERK_SECRET_KEY=sk_…
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_SIGN_IN_FALLBACK_REDIRECT_URL=/
NEXT_PUBLIC_CLERK_SIGN_UP_FALLBACK_REDIRECT_URL=/
NEXT_PUBLIC_PLANFLOW_API_URL=https://你的-API-域名
```

3. Deploy。记下前端地址，例如：`https://planflow.vercel.app`。

---

## 3. 互相对齐（很重要，漏一步会登录或接口失败）

1. **Render**：把 `PLANFLOW_CORS_ORIGINS` 改成真实前端 URL，Redeploy。  
2. **Clerk Dashboard** → Domains / Allowed origins：加上前端 URL；Sign-in/Sign-up 指向该域名。  
3. 确认后端是 `PLANFLOW_AUTH_MODE=clerk`（不要用 DEV）。

---

## 4. 给团队开用

1. 负责人用正式网址登录，打开「我的团队」→ 已有「产品一组」或新建团队。  
2. 「邀请成员」生成链接，发给同事（对方需能打开同一前端域名）。  
3. 建议每人先改显示名，避免负责人下拉出现 `user_…`。  
4. 用试用项目「品牌官网改版（试用）」演示：全周期排期 → 每日任务 → 日报。

---

## 5. 上线自检

- [ ] `/health` 正常  
- [ ] 能注册/登录  
- [ ] 能看到团队与项目  
- [ ] 每日任务能填工时  
- [ ] 另一台电脑 / 手机浏览器也能打开（同一域名）

---

## 可选：自己的服务器（Docker）

```bash
cd backend
docker build -t planflow-api .
docker run --rm -p 8000:8000 \
  -e PLANFLOW_AUTH_MODE=clerk \
  -e DATABASE_URL='…' \
  -e CLERK_PUBLISHABLE_KEY='pk_…' \
  -e PLANFLOW_CORS_ORIGINS='https://your-front.example.com' \
  planflow-api
```

前端仍建议用 Vercel；API 也可挂到任意支持 Docker 的主机。
