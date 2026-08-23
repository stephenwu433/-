#!/usr/bin/env python3
"""End-to-end smoke test: auth + create team + list teams.

Expects a running API (see README). Uses DEV JWT by default.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import httpx
import jwt
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

BASE = os.getenv("PLANFLOW_API_BASE", "http://127.0.0.1:8000")


def mint_token() -> str:
    secret = os.getenv("PLANFLOW_DEV_JWT_SECRET", "dev-only-change-me")
    now = int(time.time())
    return jwt.encode(
        {
            "sub": os.getenv("PLANFLOW_TEST_SUB", "user_dev_verify_teams"),
            "email": "verify@example.com",
            "name": "Verify Teams",
            "iat": now,
            "exp": now + 3600,
        },
        secret,
        algorithm="HS256",
    )


def main() -> int:
    token = mint_token()
    headers = {"Authorization": f"Bearer {token}"}

    with httpx.Client(base_url=BASE, timeout=30.0) as client:
        health = client.get("/health")
        health.raise_for_status()
        print("health:", json.dumps(health.json(), indent=2))

        me = client.get("/me", headers=headers)
        me.raise_for_status()
        print("me:", json.dumps(me.json(), indent=2))

        created = client.post(
            "/teams",
            headers=headers,
            json={"name": f"Verify Team {int(time.time())}"},
        )
        created.raise_for_status()
        print("created:", json.dumps(created.json(), indent=2))

        listed = client.get("/teams", headers=headers)
        listed.raise_for_status()
        payload = listed.json()
        print("listed:", json.dumps(payload, indent=2))

        ids = {t["id"] for t in payload["teams"]}
        if created.json()["id"] not in ids:
            print("ERROR: created team not found in list", file=sys.stderr)
            return 1

        # Unauthenticated should fail
        denied = client.get("/teams")
        if denied.status_code != 401:
            print(f"ERROR: expected 401 without token, got {denied.status_code}", file=sys.stderr)
            return 1
        print("unauthenticated /teams → 401 OK")

    print("verify_teams.py: ALL OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
