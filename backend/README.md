# PlanFlow Backend（FastAPI + Neon + Clerk JWT）

当前能力：

1. `GET /health` — 后端是否启动 + 鉴权配置状态
2. `GET /db/ping` — 能否连上 Neon
3. `POST /db/smoke-test` — 旧的读写冒烟
4. `GET /me` — 当前登录用户（需要 Bearer JWT）
5. `POST /teams` / `GET /teams` — 创建 / 查看**自己的**团队（需要 Bearer JWT）

数据库表（`migrations/001_init_teams.sql`）：`users`、`teams`、`team_members`、`projects`。

---

## 0. 一次性：Neon 连接串

```bash
cd backend
chmod +x scripts/neon_bootstrap.sh
export NEON_API_KEY=你的密钥
./scripts/neon_bootstrap.sh
```

会把 `DATABASE_URL` 写进 `backend/.env`（已 gitignore）。

## 1. 安装依赖（用虚拟环境）

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## 2. 执行迁移（建业务表）

```bash
.venv/bin/python scripts/migrate.py
```

## 3. 配置登录校验

### 方式 A：真实 Clerk（推荐你本机联调前端时用）

在 `backend/.env` 里加上与前端相同的 Publishable Key：

```bash
CLERK_PUBLISHABLE_KEY=pk_test_...
# 或 NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
PLANFLOW_AUTH_MODE=clerk
```

前端调用 API 时带上：

```http
Authorization: Bearer <Clerk session JWT>
```

### 方式 B：DEV 模式（没有 Clerk 密钥时测后端）

```bash
PLANFLOW_AUTH_MODE=dev
PLANFLOW_DEV_JWT_SECRET=dev-only-change-me
```

发一枚测试 JWT：

```bash
export PLANFLOW_DEV_JWT_SECRET=dev-only-change-me
TOKEN=$(.venv/bin/python scripts/mint_dev_token.py)
echo "$TOKEN"
```

## 4. 启动 API

```bash
cd backend
# 若用 DEV 模式，先 export 上面两个变量，或写进 .env
.venv/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 5. 试一下（DEV）

另开一个终端：

```bash
cd backend
export PLANFLOW_DEV_JWT_SECRET=dev-only-change-me
TOKEN=$(.venv/bin/python scripts/mint_dev_token.py)

curl -s http://127.0.0.1:8000/me -H "Authorization: Bearer $TOKEN"
curl -s -X POST http://127.0.0.1:8000/teams \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"我的第一个团队"}'
curl -s http://127.0.0.1:8000/teams -H "Authorization: Bearer $TOKEN"
```

或一键：

```bash
.venv/bin/python scripts/verify_teams.py
```

浏览器文档：http://localhost:8000/docs

## 表关系（心智模型）

```
Clerk 登录 → JWT.sub = user_xxx
         ↓
      users（我们库的镜像）
         ↓
 team_members ←→ teams
                    ↓
                projects（表已建，接口下一步）
```

## 下一步

- 前端登录后把 Clerk token 传给 `/teams`
- 再做项目（projects）的创建/列表接口
