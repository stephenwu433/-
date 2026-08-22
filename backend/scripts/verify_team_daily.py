#!/usr/bin/env python3
"""Smoke test: team daily board grouped by member.

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
    stamp = int(time.time())
    owner = {
        "Authorization": f"Bearer {mint_token(f'user_dev_tday_o_{stamp}', f'tday_o_{stamp}@example.com')}"
    }
    member = {
        "Authorization": f"Bearer {mint_token(f'user_dev_tday_m_{stamp}', f'tday_m_{stamp}@example.com')}"
    }
    today = date.today()
    end = today + timedelta(days=7)

    with httpx.Client(base_url=BASE, timeout=30.0) as client:
        owner_me = client.get("/me", headers=owner)
        owner_me.raise_for_status()
        owner_id = owner_me.json()["id"]

        member_me = client.get("/me", headers=member)
        member_me.raise_for_status()
        member_id = member_me.json()["id"]

        team = client.post(
            "/teams",
            headers=owner,
            json={"name": f"TeamDay Team {stamp}"},
        )
        team.raise_for_status()
        team_id = team.json()["id"]

        invite = client.post(
            f"/teams/{team_id}/invites",
            headers=owner,
            json={"email": f"tday_m_{stamp}@example.com", "role": "member"},
        )
        invite.raise_for_status()
        client.post(
            f"/invites/{invite.json()['token']}/accept",
            headers=member,
        ).raise_for_status()

        client.patch(
            f"/teams/{team_id}/members/{member_id}",
            headers=owner,
            json={"job_title": "frontend"},
        ).raise_for_status()

        project = client.post(
            f"/teams/{team_id}/projects",
            headers=owner,
            json={
                "name": f"TeamDay Project {stamp}",
                "planned_start": today.isoformat(),
                "planned_end": end.isoformat(),
                "owner_user_id": owner_id,
            },
        )
        project.raise_for_status()
        project_id = project.json()["id"]

        client.post(
            f"/teams/{team_id}/projects/{project_id}/members",
            headers=owner,
            json={"user_id": member_id, "job_title": "frontend"},
        ).raise_for_status()

        empty = client.get(
            f"/teams/{team_id}/team-daily",
            headers=owner,
            params={"view_date": today.isoformat()},
        )
        empty.raise_for_status()
        empty_payload = empty.json()
        if empty_payload["member_count"] != 2:
            print("ERROR: expected 2 members", empty_payload, file=sys.stderr)
            return 1
        if empty_payload["task_count"] != 0:
            print("ERROR: expected empty board", empty_payload, file=sys.stderr)
            return 1
        print("empty board OK")

        t_owner = client.post(
            f"/teams/{team_id}/projects/{project_id}/tasks",
            headers=owner,
            json={
                "title": "负责人今日项",
                "assignee_user_id": owner_id,
                "due_date": today.isoformat(),
            },
        )
        t_owner.raise_for_status()
        owner_task_id = t_owner.json()["id"]

        t_member = client.post(
            f"/teams/{team_id}/projects/{project_id}/tasks",
            headers=owner,
            json={
                "title": "成员今日项",
                "assignee_user_id": member_id,
                "due_date": today.isoformat(),
            },
        )
        t_member.raise_for_status()

        t_unassigned = client.post(
            f"/teams/{team_id}/projects/{project_id}/tasks",
            headers=owner,
            json={"title": "未指派今日项", "due_date": today.isoformat()},
        )
        t_unassigned.raise_for_status()

        client.put(
            f"/teams/{team_id}/projects/{project_id}/tasks/{owner_task_id}/time-entries/{today.isoformat()}",
            headers=owner,
            json={"hours": 1.5, "note": "推进"},
        ).raise_for_status()

        board = client.get(
            f"/teams/{team_id}/team-daily",
            headers=owner,
            params={"view_date": today.isoformat()},
        )
        board.raise_for_status()
        payload = board.json()
        if payload["task_count"] != 3:
            print("ERROR: expected 3 tasks", payload, file=sys.stderr)
            return 1
        if payload["logged_hours"] != 1.5:
            print("ERROR: expected logged_hours=1.5", payload, file=sys.stderr)
            return 1
        if len(payload["unassigned_tasks"]) != 1:
            print("ERROR: expected 1 unassigned", payload, file=sys.stderr)
            return 1

        by_id = {m["user_id"]: m for m in payload["members"]}
        if owner_id not in by_id or member_id not in by_id:
            print("ERROR: missing member columns", payload, file=sys.stderr)
            return 1
        if by_id[owner_id]["task_count"] != 1 or by_id[member_id]["task_count"] != 1:
            print("ERROR: unexpected per-member counts", by_id, file=sys.stderr)
            return 1
        if by_id[member_id].get("job_title") != "frontend":
            print("ERROR: job_title missing", by_id[member_id], file=sys.stderr)
            return 1
        print("grouped board OK")

        filtered = client.get(
            f"/teams/{team_id}/team-daily",
            headers=owner,
            params={
                "view_date": today.isoformat(),
                "project_id": project_id,
            },
        )
        filtered.raise_for_status()
        if filtered.json()["task_count"] != 3:
            print("ERROR: project filter failed", filtered.json(), file=sys.stderr)
            return 1
        print("project filter OK")

        outsider = {
            "Authorization": f"Bearer {mint_token(f'user_dev_tday_x_{stamp}', f'tday_x_{stamp}@example.com')}"
        }
        denied = client.get(
            f"/teams/{team_id}/team-daily",
            headers=outsider,
            params={"view_date": today.isoformat()},
        )
        if denied.status_code not in (403, 404):
            print(f"ERROR: expected 403/404 for outsider, got {denied.status_code}", file=sys.stderr)
            return 1
        print("authz OK")

    print("verify_team_daily.py: ALL OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
