# PlanFlow（前端）

Next.js + Clerk 登录 + 团队 / 项目页（调用 FastAPI）。

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

打开 http://localhost:3000 → 注册/登录 →「我的团队」→「查看项目」。

## 页面怎么串起来（小白版）

1. `/teams`：创建 / 查看你的团队  
2. 点某个团队的「查看项目」→ `/teams/{teamId}`  
3. 在该页创建 / 查看这个团队下的项目  
4. 每次请求都带 `Authorization: Bearer <Clerk token>`

## 下一步

排期、成员邀请，或把项目状态改成可编辑。
