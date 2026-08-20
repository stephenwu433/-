#!/usr/bin/env python3
"""Smoke test: richer project setup + /portfolio overview.

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
        "Authorization": f"Bearer {mint_token('user_dev_portfolio', 'portfolio@example.com')}"
    }
    today = date.today().isoformat()

    with httpx.Client(base_url=BASE, timeout=30.0) as client:
        me = client.get("/me", headers=headers)
        me.raise_for_status()
        user_id = me.json()["id"]
        print("me:", user_id)

        team = client.post(
            "/teams",
            headers=headers,
            json={"name": f"Portfolio Team {int(time.time())}"},
        )
        team.raise_for_status()
        team_id = team.json()["id"]
        print("team:", team_id)

        created = client.post(
            f"/teams/{team_id}/projects",
            headers=headers,
            json={
                "name": f"Portfolio Project {int(time.time())}",
                "description": "brief",
                "objective": "ship overview MVP",
                "planned_start": today,
                "planned_end": today,
                "owner_user_id": user_id,
                "member_daily_hours": 7.5,
            },
        )
        created.raise_for_status()
        project = created.json()
        print("created:", json.dumps(project, indent=2, default=str))
        if project.get("objective") != "ship overview MVP":
            print("ERROR: objective missing on create", file=sys.stderr)
            return 1
        if float(project.get("member_daily_hours", 0)) != 7.5:
            print("ERROR: member_daily_hours not saved", file=sys.stderr)
            return 1
        if project.get("owner_user_id") != user_id:
            print("ERROR: owner_user_id not saved", file=sys.stderr)
            return 1

        project_id = project["id"]
        patched = client.patch(
            f"/teams/{team_id}/projects/{project_id}",
            headers=headers,
            json={
                "plan_confirmed": True,
                "objective": "updated objective",
                "status": "active",
            },
        )
        patched.raise_for_status()
        if not patched.json().get("plan_confirmed"):
            print("ERROR: plan_confirmed not updated", file=sys.stderr)
            return 1
        print("patch settings OK")

        task = client.post(
            f"/teams/{team_id}/projects/{project_id}/tasks",
            headers=headers,
            json={
                "title": "Day task",
                "assignee_user_id": user_id,
                "due_date": today,
            },
        )
        task.raise_for_status()
        print("task:", task.json()["id"])

        portfolio = client.get(f"/portfolio?view_date={today}", headers=headers)
        portfolio.raise_for_status()
        payload = portfolio.json()
        print("portfolio stats:", json.dumps(payload["stats"], indent=2))
        ids = {p["id"] for p in payload["projects"]}
        if project_id not in ids:
            print("ERROR: project missing from portfolio", file=sys.stderr)
            return 1
        card = next(p for p in payload["projects"] if p["id"] == project_id)
        if card["progress_percent"] != 0:
            print("ERROR: unexpected progress", file=sys.stderr)
            return 1
        if payload["stats"]["day_tasks"] < 1:
            print("ERROR: day_tasks should include new task", file=sys.stderr)
            return 1
        if payload["stats"]["active_projects"] < 1:
            print("ERROR: active_projects should be >= 1", file=sys.stderr)
            return 1
        print("portfolio card:", json.dumps(card, indent=2, default=str))

        unauth = client.get("/portfolio")
        if unauth.status_code != 401:
            print(f"ERROR: expected 401, got {unauth.status_code}", file=sys.stderr)
            return 1
        print("unauthenticated → 401 OK")

    print("verify_portfolio.py: ALL OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
