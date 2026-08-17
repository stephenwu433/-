# PlanFlow Backend（FastAPI + Neon PostgreSQL）

当前能力：

1. `GET /health` — 后端是否启动
2. `GET /db/ping` — 能否连上 Neon（`SELECT 1`）
3. `POST /db/smoke-test` — 建测试表、写入、读回

## 0. 一次性：拿到 Neon 连接串

需要环境变量 `NEON_API_KEY`（Neon Console → Account settings → API keys）。

```bash
cd backend
chmod +x scripts/neon_bootstrap.sh
export NEON_API_KEY=你的密钥
./scripts/neon_bootstrap.sh
```

脚本会：

- 复用或创建名为 `planflow` 的 Neon 项目
- 把 `DATABASE_URL` 写到 `backend/.env`（已在 `.gitignore`，不会提交）

如果你已经有连接串，也可以直接：

```bash
cp .env.example .env
# 编辑 .env，填入 DATABASE_URL=postgresql://...
```

## 1. 安装依赖并启动

```bash
cd backend
python3 -m pip install -r requirements.txt
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 2. 验证读写

不启动服务，直接测库：

```bash
python3 scripts/verify_db.py
```

或启动后用 HTTP：

```bash
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8000/db/ping
curl -s -X POST http://127.0.0.1:8000/db/smoke-test \
  -H 'Content-Type: application/json' \
  -d '{"message":"hello neon"}'
```

浏览器也可打开：http://localhost:8000/docs

## 下一步

用 Clerk JWT 校验登录身份，再做团队/项目相关表结构。
