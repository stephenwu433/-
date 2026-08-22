#!/usr/bin/env python3
"""Smoke test: project members + day feedback + expanded statuses.

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
        "Authorization": f"Bearer {mint_token(f'user_dev_align_o_{stamp}', f'align_o_{stamp}@example.com')}"
    }
    member = {
        "Authorization": f"Bearer {mint_token(f'user_dev_align_m_{stamp}', f'align_m_{stamp}@example.com')}"
    }
    today = date.today()
    end = today + timedelta(days=7)

    with httpx.Client(base_url=BASE, timeout=30.0) as client:
        owner_id = client.get("/me", headers=owner).json()["id"]
        member_id = client.get("/me", headers=member).json()["id"]

        team = client.post(
            "/teams", headers=owner, json={"name": f"Align Team {stamp}"}
        )
        team.raise_for_status()
        team_id = team.json()["id"]

        invite = client.post(
            f"/teams/{team_id}/invites",
            headers=owner,
            json={"email": f"align_m_{stamp}@example.com", "role": "member"},
        )
        invite.raise_for_status()
        client.post(
            f"/invites/{invite.json()['token']}/accept", headers=member
        ).raise_for_status()

        project = client.post(
            f"/teams/{team_id}/projects",
            headers=owner,
            json={
                "name": f"Align Project {stamp}",
                "planned_start": today.isoformat(),
                "planned_end": end.isoformat(),
                "owner_user_id": owner_id,
                "member_daily_hours": 6,
            },
        )
        project.raise_for_status()
        project_id = project.json()["id"]

        members = client.get(
            f"/teams/{team_id}/projects/{project_id}/members", headers=owner
        )
        members.raise_for_status()
        ids = {m["user_id"] for m in members.json()["members"]}
        if owner_id not in ids:
            print("ERROR: owner missing from project members", members.json(), file=sys.stderr)
            return 1
        print("seeded owner OK")

        added = client.post(
            f"/teams/{team_id}/projects/{project_id}/members",
            headers=owner,
            json={"user_id": member_id, "job_title": "designer"},
        )
        added.raise_for_status()
        if added.json().get("job_title") != "designer":
            print("ERROR: job_title not saved", added.json(), file=sys.stderr)
            return 1
        print("add project member OK")

        task = client.post(
            f"/teams/{team_id}/projects/{project_id}/tasks",
            headers=owner,
            json={
                "title": "对齐任务",
                "assignee_user_id": member_id,
                "due_date": today.isoformat(),
            },
        )
        task.raise_for_status()
        task_id = task.json()["id"]

        status = client.patch(
            f"/teams/{team_id}/projects/{project_id}/tasks/{task_id}",
            headers=owner,
            json={"status": "review"},
        )
        status.raise_for_status()
        if status.json()["status"] != "review":
            print("ERROR: review status not saved", file=sys.stderr)
            return 1
        print("review status OK")

        returned = client.patch(
            f"/teams/{team_id}/projects/{project_id}/tasks/{task_id}",
            headers=owner,
            json={"status": "returned"},
        )
        returned.raise_for_status()

        feedback = client.put(
            f"/teams/{team_id}/projects/{project_id}/daily-tasks/feedback",
            headers=owner,
            params={"view_date": today.isoformat()},
            json={
                "completion_percent": 100,
                "day_note": "今日完成",
                "apply_review_status": True,
            },
        )
        feedback.raise_for_status()
        fb = feedback.json()
        if fb.get("completion_percent") != 100:
            print("ERROR: completion_percent", fb, file=sys.stderr)
            return 1
        day_tasks = client.get(
            f"/teams/{team_id}/projects/{project_id}/daily-tasks",
            headers=owner,
            params={"view_date": today.isoformat()},
        )
        day_tasks.raise_for_status()
        statuses = [c["task"]["status"] for c in day_tasks.json()["tasks"]]
        if "review" not in statuses:
            print("ERROR: expected review after 100% feedback", statuses, file=sys.stderr)
            return 1
        print("day feedback OK")

        # remove member should fail if assigning after remove — remove then assign fails
        # owner cannot remove self if owner — try remove member
        rm = client.delete(
            f"/teams/{team_id}/projects/{project_id}/members/{member_id}",
            headers=owner,
        )
        if rm.status_code != 204:
            print(f"ERROR: remove member expected 204 got {rm.status_code}", file=sys.stderr)
            return 1
        print("remove project member OK")

    print("verify_align_reference.py: ALL OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
