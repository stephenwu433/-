#!/usr/bin/env python3
"""Smoke test: cross-project workload aggregation.

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
        "Authorization": f"Bearer {mint_token('user_dev_workload', 'load@example.com')}"
    }
    today = date.today().isoformat()

    with httpx.Client(base_url=BASE, timeout=30.0) as client:
        me = client.get("/me", headers=headers)
        me.raise_for_status()
        user_id = me.json()["id"]

        team = client.post(
            "/teams",
            headers=headers,
            json={"name": f"Load Team {int(time.time())}"},
        )
        team.raise_for_status()
        team_id = team.json()["id"]

        p1 = client.post(
            f"/teams/{team_id}/projects",
            headers=headers,
            json={"name": f"Load A {int(time.time())}", "member_daily_hours": 6},
        )
        p1.raise_for_status()
        p1_id = p1.json()["id"]

        p2 = client.post(
            f"/teams/{team_id}/projects",
            headers=headers,
            json={"name": f"Load B {int(time.time())}", "member_daily_hours": 6},
        )
        p2.raise_for_status()
        p2_id = p2.json()["id"]

        for project_id, title in ((p1_id, "A task"), (p2_id, "B task")):
            task = client.post(
                f"/teams/{team_id}/projects/{project_id}/tasks",
                headers=headers,
                json={
                    "title": title,
                    "due_date": today,
                    "assignee_user_id": user_id,
                },
            )
            task.raise_for_status()
            task_id = task.json()["id"]
            entry = client.put(
                f"/teams/{team_id}/projects/{project_id}/tasks/{task_id}/time-entries/{today}",
                headers=headers,
                json={"hours": 4.0, "note": "load smoke"},
            )
            entry.raise_for_status()

        workload = client.get("/workload", headers=headers, params={"view_date": today})
        workload.raise_for_status()
        payload = workload.json()
        print("workload:", json.dumps({
            "member_count": payload["member_count"],
            "overloaded_count": payload["overloaded_count"],
            "weekday_count": payload["weekday_count"],
            "first": payload["members"][0] if payload["members"] else None,
        }, indent=2, default=str))

        if payload["member_count"] < 1:
            print("ERROR: expected at least one member", file=sys.stderr)
            return 1
        card = next((m for m in payload["members"] if m["user_id"] == user_id), None)
        if card is None:
            print("ERROR: current user missing from workload", file=sys.stderr)
            return 1
        if card["project_count"] < 2:
            print("ERROR: expected cross-project involvement", file=sys.stderr)
            return 1
        if float(card["logged_hours"]) < 8:
            print("ERROR: expected logged hours from both projects", file=sys.stderr)
            return 1
        # Day scope with planned fallback: two due tasks → planned >= 2
        if float(card.get("planned_hours", 0)) < 2:
            print("ERROR: expected planned_hours >= 2", card, file=sys.stderr)
            return 1
        if "load_label" not in card:
            print("ERROR: missing load_label", card, file=sys.stderr)
            return 1
        if payload.get("scope") and payload["scope"] != "day":
            print("ERROR: expected day scope", payload, file=sys.stderr)
            return 1

        unauth = client.get("/workload")
        if unauth.status_code != 401:
            print(f"ERROR: expected 401, got {unauth.status_code}", file=sys.stderr)
            return 1

    print("verify_workload.py: ALL OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
