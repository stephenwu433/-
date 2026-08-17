from fastapi import FastAPI

app = FastAPI(
    title="PlanFlow API",
    description="团队版 PlanFlow 后端（起步骨架）",
    version="0.1.0",
)


@app.get("/health")
def health():
    """健康检查：确认后端已启动。"""
    return {"status": "ok", "service": "planflow-api"}
