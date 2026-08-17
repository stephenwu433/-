# PlanFlow Backend（FastAPI）

当前是空骨架：只有健康检查接口，方便确认后端能跑起来。

## 启动

```bash
cd backend
python3 -m pip install -r requirements.txt
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

然后打开：

- 健康检查：http://localhost:8000/health
- 接口文档：http://localhost:8000/docs

## 下一步

接入 PostgreSQL，再用 Clerk JWT 校验登录身份。
