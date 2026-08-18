# PlanFlow（前端）

Next.js + Clerk 登录 +「我的团队」页（调用 FastAPI）。

## 本地启动

开两个终端：

**1) 后端**（详见 `../backend/README.md`）

```bash
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
# .env 里需要：DATABASE_URL、CLERK_PUBLISHABLE_KEY（与前端相同）
# PLANFLOW_AUTH_MODE=clerk
.venv/bin/python scripts/migrate.py
.venv/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**2) 前端**

```bash
cd planflow
cp .env.example .env.local   # 填入 Clerk 密钥；API 地址默认已写好
npm install
npm run dev
```

打开 http://localhost:3000 → 注册/登录 →「我的团队」。

## 这一页在干什么（小白版）

1. 你登录后，Clerk 给你一枚 JWT  
2. 页面用 `getToken()` 拿到它  
3. 请求后端时带上：`Authorization: Bearer <token>`  
4. 后端校验通过后，才能 `创建团队` / `查看我的团队`

## 下一步

项目（projects）的创建/列表页面与接口。
