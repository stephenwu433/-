#!/usr/bin/env python3
"""Mint a DEV-mode JWT for local API smoke tests.

Only works when the API runs with:
  PLANFLOW_AUTH_MODE=dev
  PLANFLOW_DEV_JWT_SECRET=...same secret...

Usage:
  cd backend
  export PLANFLOW_DEV_JWT_SECRET=dev-only-change-me
  .venv/bin/python scripts/mint_dev_token.py
  .venv/bin/python scripts/mint_dev_token.py --sub user_dev_alice --email alice@example.com
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import jwt
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


def main() -> int:
    parser = argparse.ArgumentParser(description="Mint a PlanFlow DEV JWT")
    parser.add_argument("--sub", default="user_dev_demo", help="Fake Clerk user id")
    parser.add_argument("--email", default="demo@example.com")
    parser.add_argument("--name", default="Demo User")
    parser.add_argument("--ttl", type=int, default=3600, help="Seconds until expiry")
    args = parser.parse_args()

    secret = os.getenv("PLANFLOW_DEV_JWT_SECRET")
    if not secret:
        print("ERROR: set PLANFLOW_DEV_JWT_SECRET", file=sys.stderr)
        return 1

    now = int(time.time())
    token = jwt.encode(
        {
            "sub": args.sub,
            "email": args.email,
            "name": args.name,
            "iat": now,
            "exp": now + args.ttl,
        },
        secret,
        algorithm="HS256",
    )
    print(token)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
