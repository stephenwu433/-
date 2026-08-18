from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.auth import auth_status, get_current_user
from app.db import get_database_url, ping_database, run_smoke_test
from app.models import User
from app.routers import teams
from app.schemas import MeResponse

app = FastAPI(
    title="PlanFlow API",
    description="团队版 PlanFlow 后端（Neon + Clerk JWT + Teams MVP）",
    version="0.2.0",
)

app.include_router(teams.router)


class SmokeTestRequest(BaseModel):
    message: str = Field(default="hello from planflow", min_length=1, max_length=200)


@app.get("/health")
def health():
    """健康检查：确认后端已启动（不依赖数据库）。"""
    return {
        "status": "ok",
        "service": "planflow-api",
        "database_configured": get_database_url() is not None,
        "auth": auth_status(),
    }


@app.get("/db/ping")
def db_ping():
    """确认能连上 Neon PostgreSQL（SELECT 1）。"""
    if get_database_url() is None:
        raise HTTPException(
            status_code=503,
            detail="DATABASE_URL is not set. Run scripts/neon_bootstrap.sh first.",
        )
    try:
        return ping_database()
    except Exception as exc:  # noqa: BLE001 - surface connection errors to caller
        raise HTTPException(status_code=503, detail=f"database ping failed: {exc}") from exc


@app.post("/db/smoke-test")
def db_smoke_test(body: SmokeTestRequest | None = None):
    """创建测试表、写入一行、读回，证明读写正常。"""
    if get_database_url() is None:
        raise HTTPException(
            status_code=503,
            detail="DATABASE_URL is not set. Run scripts/neon_bootstrap.sh first.",
        )
    message = body.message if body else "hello from planflow"
    try:
        return run_smoke_test(message=message)
    except Exception as exc:  # noqa: BLE001 - surface connection errors to caller
        raise HTTPException(status_code=503, detail=f"smoke test failed: {exc}") from exc


@app.get("/me", response_model=MeResponse)
def me(current_user: User = Depends(get_current_user)) -> MeResponse:
    """返回当前登录用户在我们库里的镜像记录（需要 Bearer JWT）。"""
    return MeResponse(
        id=current_user.id,
        clerk_user_id=current_user.clerk_user_id,
        email=current_user.email,
        display_name=current_user.display_name,
    )
