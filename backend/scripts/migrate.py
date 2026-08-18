#!/usr/bin/env python3
"""Apply SQL files under backend/migrations/ in filename order.

Beginner usage:
  cd backend
  .venv/bin/python scripts/migrate.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.db import get_engine  # noqa: E402


def ensure_migrations_table(conn) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                filename TEXT PRIMARY KEY,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
    )


def already_applied(conn, filename: str) -> bool:
    return (
        conn.execute(
            text("SELECT 1 FROM schema_migrations WHERE filename = :f"),
            {"f": filename},
        ).scalar_one_or_none()
        is not None
    )


def main() -> int:
    migrations_dir = ROOT / "migrations"
    files = sorted(migrations_dir.glob("*.sql"))
    if not files:
        print("No migration files found.")
        return 1

    engine = get_engine()
    applied: list[str] = []
    skipped: list[str] = []

    with engine.begin() as conn:
        ensure_migrations_table(conn)
        for path in files:
            name = path.name
            if already_applied(conn, name):
                skipped.append(name)
                continue
            sql = path.read_text(encoding="utf-8")
            conn.execute(text(sql))
            conn.execute(
                text("INSERT INTO schema_migrations (filename) VALUES (:f)"),
                {"f": name},
            )
            applied.append(name)

    print("Applied:", applied or "(none)")
    print("Skipped (already done):", skipped or "(none)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
