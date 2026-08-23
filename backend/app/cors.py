"""CORS helpers — allow the Next.js frontend to call this API from the browser.

Beginner note:
- Frontend runs at http://localhost:3000
- Backend runs at http://localhost:8000
- Browsers block cross-origin calls unless the API sends CORS headers.
"""

from __future__ import annotations

import os


DEFAULT_ORIGINS = (
    "http://localhost:3000",
    "http://127.0.0.1:3000",
)


def cors_allow_origins() -> list[str]:
    """Read PLANFLOW_CORS_ORIGINS (comma-separated) or use local Next.js defaults."""
    raw = os.getenv("PLANFLOW_CORS_ORIGINS", "").strip()
    if not raw:
        return list(DEFAULT_ORIGINS)
    origins = [part.strip() for part in raw.split(",") if part.strip()]
    return origins or list(DEFAULT_ORIGINS)
