#!/usr/bin/env python3
"""Smoke test: invites + schedule dates."""

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


def mint(sub: str, email: str) -> dict[str, str]:
    secret = os.getenv("PLANFLOW_DEV_JWT_SECRET", "dev-only-change-me")
    now = int(time.time())
    token = jwt.encode(
        {"sub": sub, "email": email, "name": sub, "iat": now, "exp": now + 3600},
        secret,
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


def main() -> int:
    owner = mint("user_dev_invite_owner", "owner-invite@example.com")
    guest = mint("user_dev_invite_guest", "guest-invite@example.com")

    with httpx.Client(base_url=BASE, timeout=30.0) as client:
        team = client.post("/teams", headers=owner, json={"name": f"Invite Team {int(time.time())}"})
        team.raise_for_status()
        team_id = team.json()["id"]

        invite = client.post(
            f"/teams/{team_id}/invites",
            headers=owner,
            json={"email": "guest-invite@example.com", "role": "member"},
        )
        invite.raise_for_status()
        token = invite.json()["token"]
        print("invite:", json.dumps(invite.json(), indent=2))

        preview = client.get(f"/invites/{token}")
        preview.raise_for_status()
        assert preview.json()["expired"] is False

        accepted = client.post(f"/invites/{token}/accept", headers=guest)
        accepted.raise_for_status()
        print("accepted:", json.dumps(accepted.json(), indent=2))

        members = client.get(f"/teams/{team_id}/members", headers=guest)
        members.raise_for_status()
        roles = {m["clerk_user_id"]: m["role"] for m in members.json()["members"]}
        assert "user_dev_invite_guest" in roles
        print("members OK", roles)

        start = date.today()
        end = start + timedelta(days=3)
        project = client.post(
            f"/teams/{team_id}/projects",
            headers=owner,
            json={
                "name": "Scheduled Project",
                "planned_start": start.isoformat(),
                "planned_end": end.isoformat(),
            },
        )
        project.raise_for_status()
        pid = project.json()["id"]

        patched = client.patch(
            f"/teams/{team_id}/projects/{pid}",
            headers=owner,
            json={"status": "active", "planned_start": start.isoformat(), "planned_end": end.isoformat()},
        )
        patched.raise_for_status()

        schedule = client.get(f"/teams/{team_id}/schedule", headers=guest)
        schedule.raise_for_status()
        ids = {p["id"] for p in schedule.json()["projects"]}
        assert pid in ids
        print("schedule OK", schedule.json())

        # member cannot create invite
        forbidden = client.post(
            f"/teams/{team_id}/invites",
            headers=guest,
            json={"role": "member"},
        )
        if forbidden.status_code != 403:
            print(f"ERROR expected 403, got {forbidden.status_code}", file=sys.stderr)
            return 1
        print("member invite → 403 OK")

    print("verify_invites_schedule.py: ALL OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
