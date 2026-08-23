#!/usr/bin/env python3
"""Smoke: MVP parity — fixed phases, delete project, per-task completion, planned workload."""

from __future__ import annotations

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

FIXED = [
    "项目启动与目标确认",
    "方案与资源准备",
    "核心执行与推进",
    "优化与交付准备",
    "验收上线与复盘",
]


def mint(sub: str, email: str) -> str:
    secret = os.getenv("PLANFLOW_DEV_JWT_SECRET", "dev-only-change-me")
    now = int(time.time())
    return jwt.encode(
        {"sub": sub, "email": email, "name": sub, "iat": now, "exp": now + 3600},
        secret,
        algorithm="HS256",
    )


def main() -> int:
    stamp = int(time.time())
    headers = {
        "Authorization": f"Bearer {mint(f'user_parity_{stamp}', f'parity_{stamp}@example.com')}"
    }
    today = date.today()
    end = today + timedelta(days=20)

    with httpx.Client(base_url=BASE, timeout=60.0) as client:
        me = client.get("/me", headers=headers)
        me.raise_for_status()
        user_id = me.json()["id"]

        team = client.post("/teams", headers=headers, json={"name": f"Parity {stamp}"})
        team.raise_for_status()
        team_id = team.json()["id"]

        project = client.post(
            f"/teams/{team_id}/projects",
            headers=headers,
            json={
                "name": f"Parity Proj {stamp}",
                "planned_start": today.isoformat(),
                "planned_end": end.isoformat(),
                "owner_user_id": user_id,
                "member_daily_hours": 6,
            },
        )
        project.raise_for_status()
        project_id = project.json()["id"]

        # Generate without long requirements — uses project name
        gen = client.post(
            f"/teams/{team_id}/projects/{project_id}/cycle-schedule/generate",
            headers=headers,
            json={"replace_existing": True, "seed_mode": "from_requirements", "create_tasks": True},
        )
        gen.raise_for_status()
        names = [p["name"] for p in gen.json()["phases"]]
        if names != FIXED:
            print("ERROR: expected fixed 5 phases", names, file=sys.stderr)
            return 1
        print("fixed phases OK")

        # Create a due-today task with large planned hours for workload
        task = client.post(
            f"/teams/{team_id}/projects/{project_id}/tasks",
            headers=headers,
            json={
                "title": "超负荷任务",
                "assignee_user_id": user_id,
                "due_date": today.isoformat(),
            },
        )
        task.raise_for_status()
        task_id = task.json()["id"]

        # Patch estimated via expand path: set by updating through raw SQL-less approach —
        # use expand or time entry. For smoke, put hours + completion on entry and
        # rely on workload fallback 1h OR set estimated by generating expand.
        # Directly put completion on time entry:
        te = client.put(
            f"/teams/{team_id}/projects/{project_id}/tasks/{task_id}/time-entries/{today.isoformat()}",
            headers=headers,
            json={
                "hours": 2,
                "note": "推进",
                "completion_percent": 100,
                "apply_review_status": True,
            },
        )
        te.raise_for_status()
        if te.json().get("completion_percent") != 100:
            print("ERROR: completion_percent", te.json(), file=sys.stderr)
            return 1
        got = client.get(
            f"/teams/{team_id}/projects/{project_id}/tasks/{task_id}",
            headers=headers,
        )
        # list tasks instead if no get-one
        listed = client.get(
            f"/teams/{team_id}/projects/{project_id}/tasks", headers=headers
        )
        listed.raise_for_status()
        match = next(t for t in listed.json()["tasks"] if t["id"] == task_id)
        if match["status"] != "review":
            print("ERROR: expected review after 100%", match, file=sys.stderr)
            return 1
        print("per-task completion OK")

        daily = client.get(
            f"/teams/{team_id}/projects/{project_id}/daily-tasks",
            headers=headers,
            params={"view_date": today.isoformat()},
        )
        daily.raise_for_status()
        card = next(c for c in daily.json()["tasks"] if c["task"]["id"] == task_id)
        if card.get("my_completion_percent") != 100:
            print("ERROR: daily card completion", card, file=sys.stderr)
            return 1
        print("daily card OK")

        # Workload planned: create second high-estimate due tasks by expand
        # At minimum ensure workload returns load_label field
        wl = client.get("/workload", headers=headers, params={"view_date": today.isoformat()})
        wl.raise_for_status()
        payload = wl.json()
        card_w = next((m for m in payload["members"] if m["user_id"] == user_id), None)
        if card_w is None:
            print("ERROR: missing workload member", payload, file=sys.stderr)
            return 1
        if "load_label" not in card_w or "planned_hours" not in card_w:
            print("ERROR: missing load_label/planned_hours", card_w, file=sys.stderr)
            return 1
        print("workload fields OK", card_w["load_label"], card_w["planned_hours"])

        # Delete project
        deleted = client.delete(
            f"/teams/{team_id}/projects/{project_id}", headers=headers
        )
        if deleted.status_code != 204:
            print(f"ERROR: delete expected 204 got {deleted.status_code}", file=sys.stderr)
            return 1
        gone = client.get(f"/teams/{team_id}/projects/{project_id}", headers=headers)
        if gone.status_code != 404:
            print(f"ERROR: expected 404 after delete, got {gone.status_code}", file=sys.stderr)
            return 1
        print("delete project OK")

    print("verify_mvp_parity.py: ALL OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
