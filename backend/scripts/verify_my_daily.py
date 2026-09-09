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
    # Fresh identity each run so leftover DB rows from prior smokes don't fail the empty check.
    stamp = int(time.time())
    headers = {
        "Authorization": f"Bearer {mint_token(f'user_dev_myday_{stamp}', f'myday_{stamp}@example.com')}"
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
            json={"name": f"MyDay Team {stamp}"},
        )
        team.raise_for_status()
        team_id = team.json()["id"]

        project = client.post(
            f"/teams/{team_id}/projects",
            headers=headers,
            json={
                "name": f"MyDay Project {stamp}",
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
        if item.get("bucket") != "today":
            print("ERROR: expected bucket=today", item, file=sys.stderr)
            return 1
        if payload.get("today_count") != 1 or payload.get("overdue_count") != 0:
            print("ERROR: expected today_count=1 overdue_count=0", payload, file=sys.stderr)
            return 1
        print("list OK")

        yesterday = today - timedelta(days=1)
        overdue = client.post(
            f"/teams/{team_id}/projects/{project_id}/tasks",
            headers=headers,
            json={
                "title": "昨天该做完的事",
                "assignee_user_id": user_id,
                "due_date": yesterday.isoformat(),
            },
        )
        overdue.raise_for_status()
        overdue_id = overdue.json()["id"]

        later_due = today + timedelta(days=3)
        later = client.post(
            f"/teams/{team_id}/projects/{project_id}/tasks",
            headers=headers,
            json={
                "title": "还在推进的后续事",
                "assignee_user_id": user_id,
                "due_date": later_due.isoformat(),
            },
        )
        later.raise_for_status()
        later_id = later.json()["id"]
        patched_later = client.patch(
            f"/teams/{team_id}/projects/{project_id}/tasks/{later_id}",
            headers=headers,
            json={"status": "doing"},
        )
        patched_later.raise_for_status()

        board = client.get(
            "/my-daily-tasks",
            headers=headers,
            params={"view_date": today.isoformat()},
        )
        board.raise_for_status()
        board_payload = board.json()
        if board_payload.get("overdue_count") != 1:
            print("ERROR: expected overdue_count=1", board_payload, file=sys.stderr)
            return 1
        if board_payload.get("later_count") != 1:
            print("ERROR: expected later_count=1", board_payload, file=sys.stderr)
            return 1
        by_id = {t["task_id"]: t for t in board_payload["tasks"]}
        if by_id.get(overdue_id, {}).get("bucket") != "overdue":
            print("ERROR: overdue bucket", by_id.get(overdue_id), file=sys.stderr)
            return 1
        if by_id.get(later_id, {}).get("bucket") != "later":
            print("ERROR: later bucket", by_id.get(later_id), file=sys.stderr)
            return 1
        print("buckets OK")

        hours = client.put(
            f"/teams/{team_id}/projects/{project_id}/tasks/{task_id}/time-entries/{today.isoformat()}",
            headers=headers,
            json={"hours": 2.5, "note": "推进中", "completion_percent": 40},
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
        if again_payload["doing_count"] < 1:
            print("ERROR: expected doing_count>=1", again_payload, file=sys.stderr)
            return 1
        if again_payload["my_logged_hours"] != 2.5:
            print("ERROR: expected my_logged_hours=2.5", again_payload, file=sys.stderr)
            return 1
        today_item = next(
            t for t in again_payload["tasks"] if t["task_id"] == task_id
        )
        if today_item.get("my_completion_percent") != 40:
            print("ERROR: expected completion 40", today_item, file=sys.stderr)
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
