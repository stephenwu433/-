# PlanFlow 团队上线指南

目标：给团队一个**固定可访问的网址**（不是临时 tunnel）。

推荐组合（都可用免费档起步）：

| 部分 | 平台 | 说明 |
|------|------|------|
| 前端 | [Vercel](https://vercel.com) | 部署 `planflow/` |
| 后端 API | [Vercel](https://vercel.com)（推荐，免绑新卡）或 [Render](https://render.com) | 第二个 Vercel 项目，Root=`backend`；或 Render Docker |
| 数据库 | Neon（已有） | 继续用现有 `DATABASE_URL` |
| 登录 | Clerk（已有） | 把正式前端域名加进允许列表 |

---

## 1. 部署后端 API（推荐：第二个 Vercel 项目）

不用绑新卡（你已有 Vercel 账号即可）。

1. Vercel → **Add New… → Project**，仍选仓库 `ban`。
2. **Root Directory** 选 `backend`（不要选 planflow）。
3. Framework 若识别为 Other/Python/FastAPI 即可。
4. 环境变量（必填）：

```text
PLANFLOW_AUTH_MODE=clerk
DATABASE_URL=（Neon 连接串，带 sslmode=require）
CLERK_PUBLISHABLE_KEY=（与前端相同的 pk_…）
PLANFLOW_CORS_ORIGINS=https://ban-weld.vercel.app

# 可选：AI 自动分析排期（不配也能用规则模板）
OPENAI_API_KEY=sk-…
# PLANFLOW_AI_BASE_URL=https://api.openai.com/v1
# PLANFLOW_AI_MODEL=gpt-4o-mini
# DeepSeek 示例：PLANFLOW_AI_BASE_URL=https://api.deepseek.com/v1
# PLANFLOW_AI_MODEL=deepseek-chat
```

5. Deploy。记下 API 地址，例如：`https://ban-api-xxx.vercel.app`  
6. 打开 `https://你的-API/health` 应返回 `"status":"ok"`；若已配 AI key，`ai_schedule.configured` 应为 `true`。
7. 回到**前端** Vercel 项目 → 环境变量，把  
   `NEXT_PUBLIC_PLANFLOW_API_URL` 改成这个 API 地址 → 重新部署前端。

> 数据库表需已在 Neon 执行过迁移（本地/`migrate.py` 跑过即可；含 `014_schedule_ai_analysis.sql`）。

### AI 排期怎么用

1. 项目写好「目标 / 需求」（每行一条）和计划起止日期。  
2. 打开「全周期排期」→ 点 **① AI 分析并生成排期**。  
3. 系统调用大模型分析需求，输出五阶段工作项；页面会显示「AI 分析结论」。  
4. 未配置 key 时按钮禁用，可改用「规则模板生成」。

---

### 备选：Render Docker

Render 免费档可能要求绑卡验证。若你愿意绑卡：用仓库 `render.yaml` 或 Web Service + Root=`backend` + Docker，环境变量同上。

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

1. **Render / API Vercel**：把 `PLANFLOW_CORS_ORIGINS` 改成真实前端 URL，Redeploy。  
2. **Clerk Dashboard** → Domains / Allowed origins：加上前端 URL；Sign-in/Sign-up 指向该域名。  
3. 确认后端是 `PLANFLOW_AUTH_MODE=clerk`（不要用 DEV）。

---

## 4. 给团队开用

1. 负责人用正式网址登录，打开「我的团队」→ 已有「产品一组」或新建团队。  
2. 「邀请成员」生成链接，发给同事（对方需能打开同一前端域名）。  
3. 建议每人先改显示名，避免负责人下拉出现 `user_…`。  
4. 用试用项目「品牌官网改版（试用）」演示：全周期排期（可 AI 分析）→ 每日任务 → 日报。

---

## 5. 上线自检

- [ ] `/health` 正常  
- [ ] 能注册/登录  
- [ ] 能看到团队与项目  
- [ ] 每日任务能填工时  
- [ ] （可选）配置 `OPENAI_API_KEY` 后，排期页可点「AI 分析并生成排期」  
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
  -e OPENAI_API_KEY='sk-…' \
  planflow-api
```

前端仍建议用 Vercel；API 也可挂到任意支持 Docker 的主机。
