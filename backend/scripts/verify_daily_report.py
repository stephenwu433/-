#!/usr/bin/env python3
"""Smoke test: project daily report generate + save.

Expects a running API with PLANFLOW_AUTH_MODE=dev.
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import date
from pathlib import Path

import httpx
import jwt
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

BASE = os.getenv("PLANFLOW_API_BASE", "http://127.0.0.1:8000")


def mint_token(sub: str, email: str) -> str:
    secret = os.getenv("PLANFLOW_DEV_JWT_SECRET", "dev-only-change-me")
    now = int(time.time())
    return jwt.encode(
        {
            "sub": sub,
            "email": email,
            "name": sub,
            "iat": now,
            "exp": now + 3600,
        },
        secret,
        algorithm="HS256",
    )


def main() -> int:
    headers = {
        "Authorization": f"Bearer {mint_token('user_dev_report', 'report@example.com')}"
    }
    today = date.today().isoformat()

    with httpx.Client(base_url=BASE, timeout=30.0) as client:
        me = client.get("/me", headers=headers)
        me.raise_for_status()
        user_id = me.json()["id"]

        team = client.post(
            "/teams",
            headers=headers,
            json={"name": f"Report Team {int(time.time())}"},
        )
        team.raise_for_status()
        team_id = team.json()["id"]

        project = client.post(
            f"/teams/{team_id}/projects",
            headers=headers,
            json={"name": f"Report Project {int(time.time())}"},
        )
        project.raise_for_status()
        project_id = project.json()["id"]

        task = client.post(
            f"/teams/{team_id}/projects/{project_id}/tasks",
            headers=headers,
            json={
                "title": "Ship report page",
                "due_date": today,
                "assignee_user_id": user_id,
            },
        )
        task.raise_for_status()
        task_id = task.json()["id"]

        client.put(
            f"/teams/{team_id}/projects/{project_id}/tasks/{task_id}/time-entries/{today}",
            headers=headers,
            json={"hours": 1.5, "note": "wrote auto summary"},
        ).raise_for_status()

        report = client.get(
            f"/teams/{team_id}/projects/{project_id}/daily-report",
            headers=headers,
            params={"view_date": today},
        )
        report.raise_for_status()
        payload = report.json()
        print("report:", json.dumps({
            "day_task_count": payload["day_task_count"],
            "day_logged_hours": payload["day_logged_hours"],
            "progress_percent": payload["progress_percent"],
            "auto_summary": payload["auto_summary"],
            "saved": payload["saved"],
        }, indent=2, ensure_ascii=False))
        if payload["day_task_count"] < 1:
            print("ERROR: expected day tasks", file=sys.stderr)
            return 1
        if float(payload["day_logged_hours"]) < 1.5:
            print("ERROR: expected logged hours", file=sys.stderr)
            return 1

        saved = client.put(
            f"/teams/{team_id}/projects/{project_id}/daily-report",
            headers=headers,
            params={"view_date": today},
            json={
                "summary_text": "联调完成，准备提测。",
                "next_actions": "1. 补测试\n2. 同步产品",
            },
        )
        saved.raise_for_status()
        body = saved.json()
        if not body["saved"] or body["summary_text"] != "联调完成，准备提测。":
            print("ERROR: save failed", file=sys.stderr)
            return 1
        print("save OK")

        again = client.get(
            f"/teams/{team_id}/projects/{project_id}/daily-report",
            headers=headers,
            params={"view_date": today},
        )
        again.raise_for_status()
        if again.json()["next_actions"] != "1. 补测试\n2. 同步产品":
            print("ERROR: next_actions not persisted", file=sys.stderr)
            return 1

        unauth = client.get(
            f"/teams/{team_id}/projects/{project_id}/daily-report",
            params={"view_date": today},
        )
        if unauth.status_code != 401:
            print(f"ERROR: expected 401, got {unauth.status_code}", file=sys.stderr)
            return 1

    print("verify_daily_report.py: ALL OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
