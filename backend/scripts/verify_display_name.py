#!/usr/bin/env python3
"""Smoke test: PATCH /me and member display_name rename."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import jwt
from dotenv import load_dotenv
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
os.environ["PLANFLOW_AUTH_MODE"] = "dev"
os.environ.setdefault("PLANFLOW_DEV_JWT_SECRET", "dev-only-change-me")

sys.path.insert(0, str(ROOT))
from app.main import app  # noqa: E402


def mint(sub: str, email: str | None = None, name: str | None = None) -> dict[str, str]:
    secret = os.environ["PLANFLOW_DEV_JWT_SECRET"]
    now = int(time.time())
    payload: dict = {"sub": sub, "iat": now, "exp": now + 3600}
    if email:
        payload["email"] = email
    if name:
        payload["name"] = name
    token = jwt.encode(payload, secret, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


def main() -> int:
    client = TestClient(app)
    owner = mint(f"user_dev_rename_owner_{int(time.time())}")
    member = mint(f"user_dev_rename_member_{int(time.time())}")

    me0 = client.get("/me", headers=owner)
    me0.raise_for_status()
    assert me0.json().get("display_name") in (None, "")

    patched = client.patch("/me", headers=owner, json={"display_name": "  小明  "})
    patched.raise_for_status()
    assert patched.json()["display_name"] == "小明"
    print("PATCH /me OK", patched.json()["display_name"])

    team = client.post("/teams", headers=owner, json={"name": f"Rename Team {int(time.time())}"})
    team.raise_for_status()
    team_id = team.json()["id"]

    invite = client.post(
        f"/teams/{team_id}/invites",
        headers=owner,
        json={"role": "member"},
    )
    invite.raise_for_status()
    token = invite.json()["token"]
    client.post(f"/invites/{token}/accept", headers=member).raise_for_status()

    member_me = client.get("/me", headers=member)
    member_me.raise_for_status()
    member_id = member_me.json()["id"]

    renamed = client.patch(
        f"/teams/{team_id}/members/{member_id}",
        headers=owner,
        json={"display_name": "同事甲"},
    )
    renamed.raise_for_status()
    if renamed.json().get("display_name") != "同事甲":
        print("ERROR: member rename failed", renamed.json(), file=sys.stderr)
        return 1
    print("member display_name OK", renamed.json()["display_name"])

    # Manual name must stick even if JWT later has a different name
    member2 = mint(member_me.json()["clerk_user_id"], name="JWT Name Should Not Win")
    again = client.get("/me", headers=member2)
    again.raise_for_status()
    if again.json().get("display_name") != "同事甲":
        print("ERROR: JWT overwrote display_name", again.json(), file=sys.stderr)
        return 1
    print("JWT does not overwrite renamed display_name OK")

    print("verify_display_name.py: ALL OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
