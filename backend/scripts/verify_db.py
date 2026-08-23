#!/usr/bin/env python3
"""Quick offline check: ping DB + smoke test without starting uvicorn."""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Allow `python scripts/verify_db.py` from backend/
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db import get_database_url, ping_database, run_smoke_test  # noqa: E402


def main() -> int:
    if get_database_url() is None:
        print("DATABASE_URL is not set. Run: ./scripts/neon_bootstrap.sh")
        return 1
    ping = ping_database()
    smoke = run_smoke_test(message="verify_db.py")
    print(json.dumps({"ping": ping, "smoke": smoke}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
