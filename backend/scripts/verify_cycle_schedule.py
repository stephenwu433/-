#!/usr/bin/env python3
"""Smoke test: generate / edit / confirm project cycle schedule.

Expects a running API with PLANFLOW_AUTH_MODE=dev.
"""

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
        "Authorization": f"Bearer {mint_token('user_dev_cycle', 'cycle@example.com')}"
    }
    start = date.today()
    end = start + timedelta(days=14)

    with httpx.Client(base_url=BASE, timeout=30.0) as client:
        me = client.get("/me", headers=headers)
        me.raise_for_status()
        user_id = me.json()["id"]

        team = client.post(
            "/teams",
            headers=headers,
            json={"name": f"Cycle Team {int(time.time())}"},
        )
        team.raise_for_status()
        team_id = team.json()["id"]

        created = client.post(
            f"/teams/{team_id}/projects",
            headers=headers,
            json={
                "name": f"Cycle Project {int(time.time())}",
                "objective": "cycle schedule smoke",
                "planned_start": start.isoformat(),
                "planned_end": end.isoformat(),
                "owner_user_id": user_id,
                "member_daily_hours": 6,
            },
        )
        created.raise_for_status()
        project_id = created.json()["id"]
        print("project:", project_id)

        empty = client.get(
            f"/teams/{team_id}/projects/{project_id}/cycle-schedule",
            headers=headers,
        )
        empty.raise_for_status()
        if empty.json()["phase_count"] != 0:
            print("ERROR: expected empty schedule", file=sys.stderr)
            return 1
        print("empty schedule OK")

        generated = client.post(
            f"/teams/{team_id}/projects/{project_id}/cycle-schedule/generate",
            headers=headers,
            json={"replace_existing": True, "phase_count": 5},
        )
        generated.raise_for_status()
        payload = generated.json()
        print("generated:", json.dumps({
            "phase_count": payload["phase_count"],
            "work_item_count": payload["work_item_count"],
            "total_estimated_hours": payload["total_estimated_hours"],
        }, indent=2))
        if payload["phase_count"] != 5 or payload["work_item_count"] != 5:
            print("ERROR: expected 5 phases and 5 work items", file=sys.stderr)
            return 1

        item = payload["phases"][0]["work_items"][0]
        patched = client.patch(
            f"/teams/{team_id}/projects/{project_id}/cycle-schedule/work-items/{item['id']}",
            headers=headers,
            json={
                "title": "Kickoff workshop",
                "estimated_hours": 3.5,
                "status": "doing",
                "assignee_user_id": user_id,
            },
        )
        patched.raise_for_status()
        if patched.json()["title"] != "Kickoff workshop":
            print("ERROR: work item title not updated", file=sys.stderr)
            return 1
        print("patch work item OK")

        confirmed = client.post(
            f"/teams/{team_id}/projects/{project_id}/cycle-schedule/confirm",
            headers=headers,
        )
        confirmed.raise_for_status()
        if not confirmed.json()["plan_confirmed"]:
            print("ERROR: plan not confirmed", file=sys.stderr)
            return 1
        print("confirm OK")

        unauth = client.get(
            f"/teams/{team_id}/projects/{project_id}/cycle-schedule",
        )
        if unauth.status_code != 401:
            print(f"ERROR: expected 401, got {unauth.status_code}", file=sys.stderr)
            return 1

    print("verify_cycle_schedule.py: ALL OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
