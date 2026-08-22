#!/usr/bin/env python3
"""Smoke test: in-app notifications from schedule/report events.

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
    owner = {
        "Authorization": f"Bearer {mint_token('user_dev_notify_owner', 'owner-n@example.com')}"
    }
    member = {
        "Authorization": f"Bearer {mint_token('user_dev_notify_member', 'member-n@example.com')}"
    }
    today = date.today()
    end = today + timedelta(days=10)

    with httpx.Client(base_url=BASE, timeout=30.0) as client:
        owner_me = client.get("/me", headers=owner)
        owner_me.raise_for_status()
        member_me = client.get("/me", headers=member)
        member_me.raise_for_status()
        member_id = member_me.json()["id"]

        team = client.post(
            "/teams",
            headers=owner,
            json={"name": f"Notify Team {int(time.time())}"},
        )
        team.raise_for_status()
        team_id = team.json()["id"]

        # invite + accept so member is on team
        invite = client.post(
            f"/teams/{team_id}/invites",
            headers=owner,
            json={"email": "member-n@example.com", "role": "member"},
        )
        invite.raise_for_status()
        token_path = invite.json()["token"]
        client.post(f"/invites/{token_path}/accept", headers=member).raise_for_status()

        project = client.post(
            f"/teams/{team_id}/projects",
            headers=owner,
            json={
                "name": f"Notify Project {int(time.time())}",
                "planned_start": today.isoformat(),
                "planned_end": end.isoformat(),
            },
        )
        project.raise_for_status()
        project_id = project.json()["id"]

        gen = client.post(
            f"/teams/{team_id}/projects/{project_id}/cycle-schedule/generate",
            headers=owner,
            json={"replace_existing": True, "phase_count": 5},
        )
        gen.raise_for_status()

        conf = client.post(
            f"/teams/{team_id}/projects/{project_id}/cycle-schedule/confirm",
            headers=owner,
        )
        conf.raise_for_status()

        report = client.put(
            f"/teams/{team_id}/projects/{project_id}/daily-report",
            headers=owner,
            params={"view_date": today.isoformat()},
            json={"summary_text": "smoke report", "next_actions": "1. test"},
        )
        report.raise_for_status()

        # assign task to member → notification for member
        task = client.post(
            f"/teams/{team_id}/projects/{project_id}/tasks",
            headers=owner,
            json={
                "title": "Assigned task",
                "assignee_user_id": member_id,
                "due_date": today.isoformat(),
            },
        )
        task.raise_for_status()

        listed = client.get("/notifications", headers=member)
        listed.raise_for_status()
        payload = listed.json()
        print("member notifications:", json.dumps({
            "unread_count": payload["unread_count"],
            "titles": [n["title"] for n in payload["notifications"]],
        }, indent=2, ensure_ascii=False))
        if payload["unread_count"] < 3:
            print("ERROR: expected schedule/report/task notifications", file=sys.stderr)
            return 1

        count = client.get("/notifications/unread-count", headers=member)
        count.raise_for_status()
        if count.json()["unread_count"] != payload["unread_count"]:
            print("ERROR: unread count mismatch", file=sys.stderr)
            return 1

        first_id = payload["notifications"][0]["id"]
        one = client.post(f"/notifications/{first_id}/read", headers=member)
        one.raise_for_status()
        if one.json()["unread"]:
            print("ERROR: notification still unread", file=sys.stderr)
            return 1

        all_read = client.post("/notifications/mark-all-read", headers=member)
        all_read.raise_for_status()
        if all_read.json()["unread_count"] != 0:
            print("ERROR: mark-all-read failed", file=sys.stderr)
            return 1

        project_list = client.get(
            f"/teams/{team_id}/projects/{project_id}/notifications",
            headers=member,
        )
        project_list.raise_for_status()
        if project_list.json()["unread_count"] != 0:
            print("ERROR: project unread should be 0", file=sys.stderr)
            return 1

        unauth = client.get("/notifications")
        if unauth.status_code != 401:
            print(f"ERROR: expected 401, got {unauth.status_code}", file=sys.stderr)
            return 1

    print("verify_notifications.py: ALL OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
