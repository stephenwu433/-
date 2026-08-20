#!/usr/bin/env python3
"""Smoke test for project tasks."""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import date, timedelta
from pathlib import Path

import httpx
import jwt
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
BASE = os.getenv("PLANFLOW_API_BASE", "http://127.0.0.1:8000")


def mint(sub: str) -> dict[str, str]:
    secret = os.getenv("PLANFLOW_DEV_JWT_SECRET", "dev-only-change-me")
    now = int(time.time())
    token = jwt.encode(
        {"sub": sub, "email": f"{sub}@example.com", "name": sub, "iat": now, "exp": now + 3600},
        secret,
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


def main() -> int:
    # Use DEV mode for this script
    headers = mint("user_dev_tasks")
    with httpx.Client(base_url=BASE, timeout=30.0) as client:
        team = client.post("/teams", headers=headers, json={"name": f"Task Team {int(time.time())}"})
        team.raise_for_status()
        team_id = team.json()["id"]
        project = client.post(
            f"/teams/{team_id}/projects",
            headers=headers,
            json={"name": "Has Tasks"},
        )
        project.raise_for_status()
        project_id = project.json()["id"]

        created = client.post(
            f"/teams/{team_id}/projects/{project_id}/tasks",
            headers=headers,
            json={
                "title": "写需求文档",
                "description": "第一版",
                "due_date": (date.today() + timedelta(days=2)).isoformat(),
            },
        )
        created.raise_for_status()
        task_id = created.json()["id"]
        print("created", json.dumps(created.json(), indent=2, ensure_ascii=False))

        listed = client.get(
            f"/teams/{team_id}/projects/{project_id}/tasks",
            headers=headers,
        )
        listed.raise_for_status()
        assert any(t["id"] == task_id for t in listed.json()["tasks"])

        patched = client.patch(
            f"/teams/{team_id}/projects/{project_id}/tasks/{task_id}",
            headers=headers,
            json={"status": "doing"},
        )
        patched.raise_for_status()
        assert patched.json()["status"] == "doing"
        print("status doing OK")

        deleted = client.delete(
            f"/teams/{team_id}/projects/{project_id}/tasks/{task_id}",
            headers=headers,
        )
        if deleted.status_code != 204:
            print("ERROR delete", deleted.status_code, file=sys.stderr)
            return 1
        print("delete OK")

    print("verify_tasks.py: ALL OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
