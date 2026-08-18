#!/usr/bin/env python3
"""Smoke test: create team → create project → list projects (membership checks).

Expects a running API with PLANFLOW_AUTH_MODE=dev.
"""

from __future__ import annotations

import json
import os
import sys
import time
import uuid
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
    owner_headers = {
        "Authorization": f"Bearer {mint_token('user_dev_projects_owner', 'owner@example.com')}"
    }
    other_headers = {
        "Authorization": f"Bearer {mint_token('user_dev_projects_other', 'other@example.com')}"
    }

    with httpx.Client(base_url=BASE, timeout=30.0) as client:
        team = client.post(
            "/teams",
            headers=owner_headers,
            json={"name": f"Projects Team {int(time.time())}"},
        )
        team.raise_for_status()
        team_id = team.json()["id"]
        print("team:", team_id)

        created = client.post(
            f"/teams/{team_id}/projects",
            headers=owner_headers,
            json={
                "name": f"Demo Project {int(time.time())}",
                "description": "created by verify_projects.py",
            },
        )
        created.raise_for_status()
        print("created:", json.dumps(created.json(), indent=2))

        listed = client.get(f"/teams/{team_id}/projects", headers=owner_headers)
        listed.raise_for_status()
        payload = listed.json()
        print("listed:", json.dumps(payload, indent=2))
        if created.json()["id"] not in {p["id"] for p in payload["projects"]}:
            print("ERROR: created project missing from list", file=sys.stderr)
            return 1

        # Non-member should not see the team/projects
        denied = client.get(f"/teams/{team_id}/projects", headers=other_headers)
        if denied.status_code != 404:
            print(
                f"ERROR: expected 404 for non-member, got {denied.status_code}",
                file=sys.stderr,
            )
            return 1
        print("non-member list → 404 OK")

        # Fake team id
        missing = client.get(
            f"/teams/{uuid.uuid4()}/projects",
            headers=owner_headers,
        )
        if missing.status_code != 404:
            print(
                f"ERROR: expected 404 for missing team, got {missing.status_code}",
                file=sys.stderr,
            )
            return 1
        print("missing team → 404 OK")

        unauth = client.get(f"/teams/{team_id}/projects")
        if unauth.status_code != 401:
            print(
                f"ERROR: expected 401 without token, got {unauth.status_code}",
                file=sys.stderr,
            )
            return 1
        print("unauthenticated → 401 OK")

    print("verify_projects.py: ALL OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
