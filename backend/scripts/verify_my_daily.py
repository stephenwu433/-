#!/usr/bin/env python3
"""Smoke test: personal my-daily-tasks across projects.

Expects a running API with PLANFLOW_AUTH_MODE=dev.
"""

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
        "Authorization": f"Bearer {mint_token('user_dev_myday', 'myday@example.com')}"
    }
    today = date.today()
    end = today + timedelta(days=7)

    with httpx.Client(base_url=BASE, timeout=30.0) as client:
        me = client.get("/me", headers=headers)
        me.raise_for_status()
        user_id = me.json()["id"]

        team = client.post(
            "/teams",
            headers=headers,
            json={"name": f"MyDay Team {int(time.time())}"},
        )
        team.raise_for_status()
        team_id = team.json()["id"]

        project = client.post(
            f"/teams/{team_id}/projects",
            headers=headers,
            json={
                "name": f"MyDay Project {int(time.time())}",
                "planned_start": today.isoformat(),
                "planned_end": end.isoformat(),
                "owner_user_id": user_id,
            },
        )
        project.raise_for_status()
        project_id = project.json()["id"]

        empty = client.get("/my-daily-tasks", headers=headers, params={"view_date": today.isoformat()})
        empty.raise_for_status()
        if empty.json()["task_count"] != 0:
            print("ERROR: expected empty my-daily initially", file=sys.stderr)
            return 1
        print("empty OK")

        task = client.post(
            f"/teams/{team_id}/projects/{project_id}/tasks",
            headers=headers,
            json={
                "title": "今日亲自做的事",
                "assignee_user_id": user_id,
                "due_date": today.isoformat(),
            },
        )
        task.raise_for_status()
        task_id = task.json()["id"]

        listed = client.get(
            "/my-daily-tasks",
            headers=headers,
            params={"view_date": today.isoformat()},
        )
        listed.raise_for_status()
        payload = listed.json()
        if payload["task_count"] != 1:
            print("ERROR: expected 1 my daily task", payload, file=sys.stderr)
            return 1
        item = payload["tasks"][0]
        if item["task_id"] != task_id or item["title"] != "今日亲自做的事":
            print("ERROR: unexpected task payload", item, file=sys.stderr)
            return 1
        print("list OK")

        hours = client.put(
            f"/teams/{team_id}/projects/{project_id}/tasks/{task_id}/time-entries/{today.isoformat()}",
            headers=headers,
            json={"hours": 2.5, "note": "推进中"},
        )
        hours.raise_for_status()

        status = client.patch(
            f"/teams/{team_id}/projects/{project_id}/tasks/{task_id}",
            headers=headers,
            json={"status": "doing"},
        )
        status.raise_for_status()

        again = client.get(
            "/my-daily-tasks",
            headers=headers,
            params={"view_date": today.isoformat()},
        )
        again.raise_for_status()
        again_payload = again.json()
        if again_payload["doing_count"] != 1:
            print("ERROR: expected doing_count=1", again_payload, file=sys.stderr)
            return 1
        if again_payload["my_logged_hours"] != 2.5:
            print("ERROR: expected my_logged_hours=2.5", again_payload, file=sys.stderr)
            return 1
        print("status+hours OK")

        unauth = client.get("/my-daily-tasks")
        if unauth.status_code != 401:
            print(f"ERROR: expected 401, got {unauth.status_code}", file=sys.stderr)
            return 1

    print("verify_my_daily.py: ALL OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
