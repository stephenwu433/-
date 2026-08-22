#!/usr/bin/env python3
"""Smoke test: generate / edit / confirm project cycle schedule with real tasks.

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

        # Create real tasks first
        task_ids = []
        for title in ("需求访谈", "技术方案", "联调验收"):
            task = client.post(
                f"/teams/{team_id}/projects/{project_id}/tasks",
                headers=headers,
                json={"title": title, "assignee_user_id": user_id},
            )
            task.raise_for_status()
            task_ids.append(task.json()["id"])
        print("tasks:", task_ids)

        generated = client.post(
            f"/teams/{team_id}/projects/{project_id}/cycle-schedule/generate",
            headers=headers,
            json={
                "replace_existing": True,
                "phase_count": 5,
                "seed_mode": "from_tasks",
            },
        )
        generated.raise_for_status()
        payload = generated.json()
        print(
            "generated:",
            json.dumps(
                {
                    "phase_count": payload["phase_count"],
                    "work_item_count": payload["work_item_count"],
                    "linked_task_count": payload.get("linked_task_count"),
                },
                indent=2,
            ),
        )
        if payload["phase_count"] != 5 or payload["work_item_count"] != 3:
            print("ERROR: expected 5 phases and 3 linked work items", file=sys.stderr)
            return 1
        if payload.get("linked_task_count") != 3:
            print("ERROR: expected linked_task_count=3", file=sys.stderr)
            return 1

        # phases_only regenerate
        phases_only = client.post(
            f"/teams/{team_id}/projects/{project_id}/cycle-schedule/generate",
            headers=headers,
            json={
                "replace_existing": True,
                "phase_count": 3,
                "seed_mode": "phases_only",
                "phase_names": ["启动", "开发", "验收"],
            },
        )
        phases_only.raise_for_status()
        po = phases_only.json()
        if po["phase_count"] != 3 or po["work_item_count"] != 0:
            print("ERROR: phases_only should create empty phases", file=sys.stderr)
            return 1
        print("phases_only OK")

        phase_id = po["phases"][1]["id"]

        # create custom work item
        created_item = client.post(
            f"/teams/{team_id}/projects/{project_id}/cycle-schedule/phases/{phase_id}/work-items",
            headers=headers,
            json={"title": "手写工作项", "estimated_hours": 2},
        )
        created_item.raise_for_status()
        item = created_item.json()
        if item.get("task_id"):
            print("ERROR: new work item should not auto-link", file=sys.stderr)
            return 1
        print("create work item OK")

        # sync to task
        synced = client.post(
            f"/teams/{team_id}/projects/{project_id}/cycle-schedule/work-items/{item['id']}/sync-task",
            headers=headers,
        )
        synced.raise_for_status()
        if not synced.json().get("task_id"):
            print("ERROR: sync-task did not set task_id", file=sys.stderr)
            return 1
        print("sync-task OK")

        # import remaining unlinked tasks into first phase
        imported = client.post(
            f"/teams/{team_id}/projects/{project_id}/cycle-schedule/import-tasks",
            headers=headers,
            json={"phase_id": po["phases"][0]["id"], "only_unlinked": True},
        )
        imported.raise_for_status()
        if imported.json()["linked_task_count"] < 3:
            print("ERROR: import-tasks did not link enough tasks", file=sys.stderr)
            return 1
        print("import-tasks OK")

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

        # add + delete phase
        new_phase = client.post(
            f"/teams/{team_id}/projects/{project_id}/cycle-schedule/phases",
            headers=headers,
            json={"name": "临时阶段"},
        )
        new_phase.raise_for_status()
        deleted = client.delete(
            f"/teams/{team_id}/projects/{project_id}/cycle-schedule/phases/{new_phase.json()['id']}",
            headers=headers,
        )
        if deleted.status_code != 204:
            print(f"ERROR: delete phase expected 204, got {deleted.status_code}", file=sys.stderr)
            return 1
        print("phase CRUD OK")

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
