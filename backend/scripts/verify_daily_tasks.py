#!/usr/bin/env python3
"""Smoke test: daily tasks list + hours upsert.

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
        "Authorization": f"Bearer {mint_token('user_dev_daily', 'daily@example.com')}"
    }
    today = date.today().isoformat()

    with httpx.Client(base_url=BASE, timeout=30.0) as client:
        team = client.post(
            "/teams",
            headers=headers,
            json={"name": f"Daily Team {int(time.time())}"},
        )
        team.raise_for_status()
        team_id = team.json()["id"]

        project = client.post(
            f"/teams/{team_id}/projects",
            headers=headers,
            json={"name": f"Daily Project {int(time.time())}"},
        )
        project.raise_for_status()
        project_id = project.json()["id"]

        task = client.post(
            f"/teams/{team_id}/projects/{project_id}/tasks",
            headers=headers,
            json={"title": "Write daily report", "due_date": today},
        )
        task.raise_for_status()
        task_id = task.json()["id"]
        print("task:", task_id)

        daily = client.get(
            f"/teams/{team_id}/projects/{project_id}/daily-tasks",
            headers=headers,
            params={"view_date": today},
        )
        daily.raise_for_status()
        payload = daily.json()
        print("daily:", json.dumps({
            "task_count": payload["task_count"],
            "my_logged_hours": payload["my_logged_hours"],
        }, indent=2))
        if payload["task_count"] < 1:
            print("ERROR: expected at least one daily task", file=sys.stderr)
            return 1

        entry = client.put(
            f"/teams/{team_id}/projects/{project_id}/tasks/{task_id}/time-entries/{today}",
            headers=headers,
            json={"hours": 2.5, "note": "drafted outline"},
        )
        entry.raise_for_status()
        if float(entry.json()["hours"]) != 2.5:
            print("ERROR: hours not saved", file=sys.stderr)
            return 1
        print("upsert entry OK")

        entry2 = client.put(
            f"/teams/{team_id}/projects/{project_id}/tasks/{task_id}/time-entries/{today}",
            headers=headers,
            json={"hours": 3.0, "note": "updated"},
        )
        entry2.raise_for_status()
        if float(entry2.json()["hours"]) != 3.0:
            print("ERROR: hours not updated", file=sys.stderr)
            return 1
        if entry2.json()["id"] != entry.json()["id"]:
            print("ERROR: upsert should keep same entry id", file=sys.stderr)
            return 1

        daily2 = client.get(
            f"/teams/{team_id}/projects/{project_id}/daily-tasks",
            headers=headers,
            params={"view_date": today},
        )
        daily2.raise_for_status()
        if float(daily2.json()["my_logged_hours"]) != 3.0:
            print("ERROR: my_logged_hours mismatch", file=sys.stderr)
            return 1
        print("daily hours aggregate OK")

        unauth = client.get(
            f"/teams/{team_id}/projects/{project_id}/daily-tasks",
            params={"view_date": today},
        )
        if unauth.status_code != 401:
            print(f"ERROR: expected 401, got {unauth.status_code}", file=sys.stderr)
            return 1

    print("verify_daily_tasks.py: ALL OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
