"""PostgreSQL connection helpers for PlanFlow.

Beginner notes:
- DATABASE_URL comes from the environment (or backend/.env).
- We use SQLAlchemy + psycopg (v3) to talk to Neon PostgreSQL.
- Neon requires SSL; keep ?sslmode=require on the connection string.
"""

from __future__ import annotations

import os
from collections.abc import Generator
from functools import lru_cache

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

# Load backend/.env if present (local / agent convenience). Secrets in the
# process environment always win over file values.
load_dotenv()


def normalize_database_url(url: str) -> str:
    """Accept common Postgres URLs and force the psycopg driver."""
    url = url.strip()
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    if url.startswith("postgresql://") and not url.startswith("postgresql+psycopg://"):
        url = "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


def get_database_url() -> str | None:
    raw = os.getenv("DATABASE_URL")
    if not raw or not raw.strip():
        return None
    return normalize_database_url(raw)


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    database_url = get_database_url()
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is not set. "
            "Create a Neon project, then export DATABASE_URL "
            "(or put it in backend/.env)."
        )
    return create_engine(
        database_url,
        pool_pre_ping=True,
        pool_size=3,
        max_overflow=2,
    )


def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: yield one DB session per request."""
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


def ping_database() -> dict:
    """Run SELECT 1 to prove the connection works."""
    with get_engine().connect() as conn:
        value = conn.execute(text("SELECT 1")).scalar_one()
        version = conn.execute(text("SHOW server_version")).scalar_one()
    return {"ok": True, "select_1": value, "server_version": version}


SMOKE_TABLE = "planflow_db_smoke_test"


def run_smoke_test(message: str = "hello from planflow") -> dict:
    """Create a tiny test table, write one row, read it back."""
    with get_engine().begin() as conn:
        conn.execute(
            text(
                f"""
                CREATE TABLE IF NOT EXISTS {SMOKE_TABLE} (
                    id BIGSERIAL PRIMARY KEY,
                    message TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
        )
        row = conn.execute(
            text(
                f"""
                INSERT INTO {SMOKE_TABLE} (message)
                VALUES (:message)
                RETURNING id, message, created_at
                """
            ),
            {"message": message},
        ).mappings().one()
        count = conn.execute(
            text(f"SELECT COUNT(*) FROM {SMOKE_TABLE}")
        ).scalar_one()

    return {
        "ok": True,
        "table": SMOKE_TABLE,
        "inserted": {
            "id": row["id"],
            "message": row["message"],
            "created_at": row["created_at"].isoformat(),
        },
        "row_count": count,
    }
