"""Clerk JWT authentication for FastAPI.

How it works (beginner view):
1. Frontend (Clerk) gives the browser a session JWT after login.
2. Browser calls our API with: Authorization: Bearer <token>
3. We verify the token signature using Clerk's public JWKS keys.
4. The token's `sub` claim is the Clerk user id (user_xxx).

Env vars:
  CLERK_PUBLISHABLE_KEY / NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
      → used to derive the Clerk issuer host (preferred)
  CLERK_ISSUER
      → e.g. https://xxx.clerk.accounts.dev (optional override)
  CLERK_JWKS_URL
      → optional override of JWKS endpoint
  PLANFLOW_AUTH_MODE=dev
      → local smoke tests: accept HS256 tokens signed with PLANFLOW_DEV_JWT_SECRET
  PLANFLOW_DEV_JWT_SECRET
      → shared secret for DEV mode only (never use in production)
"""

from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from functools import lru_cache

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User

load_dotenv()

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthClaims:
    clerk_user_id: str
    email: str | None = None
    display_name: str | None = None


def _auth_mode() -> str:
    return (os.getenv("PLANFLOW_AUTH_MODE") or "clerk").strip().lower()


def _publishable_key() -> str | None:
    return (
        os.getenv("CLERK_PUBLISHABLE_KEY")
        or os.getenv("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY")
        or None
    )


def issuer_from_publishable_key(publishable_key: str) -> str:
    """Decode Clerk publishable key → Frontend API host → issuer URL."""
    parts = publishable_key.split("_", 2)
    if len(parts) < 3 or parts[0] != "pk":
        raise ValueError("CLERK publishable key must look like pk_test_... or pk_live_...")
    raw = parts[2]
    padded = raw + "=" * (-len(raw) % 4)
    decoded = base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8")
    host = decoded.rstrip("$").strip()
    if not host:
        raise ValueError("Could not decode issuer host from publishable key")
    return f"https://{host}"


def get_clerk_issuer() -> str:
    explicit = os.getenv("CLERK_ISSUER")
    if explicit and explicit.strip():
        return explicit.strip().rstrip("/")
    pk = _publishable_key()
    if not pk:
        raise RuntimeError(
            "Set CLERK_ISSUER or CLERK_PUBLISHABLE_KEY "
            "(or NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY) for Clerk JWT verification."
        )
    return issuer_from_publishable_key(pk.strip())


def get_jwks_url() -> str:
    explicit = os.getenv("CLERK_JWKS_URL")
    if explicit and explicit.strip():
        return explicit.strip()
    return f"{get_clerk_issuer()}/.well-known/jwks.json"


@lru_cache(maxsize=1)
def _jwks_client() -> PyJWKClient:
    return PyJWKClient(get_jwks_url(), cache_keys=True)


def verify_clerk_token(token: str) -> AuthClaims:
    issuer = get_clerk_issuer()
    try:
        signing_key = _jwks_client().get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=issuer,
            options={
                "verify_aud": False,  # Clerk session tokens often omit / vary aud
                "require": ["exp", "iat", "sub", "iss"],
            },
        )
    except Exception as exc:  # noqa: BLE001 - map all JWT failures to 401
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Clerk token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    clerk_user_id = payload.get("sub")
    if not clerk_user_id or not isinstance(clerk_user_id, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject (sub)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    email = payload.get("email")
    if isinstance(email, list) and email:
        email = email[0]
    if email is not None and not isinstance(email, str):
        email = None

    display_name = payload.get("name") or payload.get("full_name")
    if display_name is not None and not isinstance(display_name, str):
        display_name = None

    return AuthClaims(
        clerk_user_id=clerk_user_id,
        email=email,
        display_name=display_name,
    )


def verify_dev_token(token: str) -> AuthClaims:
    secret = os.getenv("PLANFLOW_DEV_JWT_SECRET")
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PLANFLOW_AUTH_MODE=dev but PLANFLOW_DEV_JWT_SECRET is not set",
        )
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            options={"require": ["exp", "iat", "sub"]},
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid DEV token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    clerk_user_id = payload["sub"]
    if not isinstance(clerk_user_id, str) or not clerk_user_id:
        raise HTTPException(status_code=401, detail="DEV token missing sub")

    email = payload.get("email") if isinstance(payload.get("email"), str) else None
    display_name = (
        payload.get("name") if isinstance(payload.get("name"), str) else None
    )
    return AuthClaims(
        clerk_user_id=clerk_user_id,
        email=email,
        display_name=display_name,
    )


def verify_bearer_token(token: str) -> AuthClaims:
    if _auth_mode() == "dev":
        return verify_dev_token(token)
    return verify_clerk_token(token)


def upsert_user_from_claims(db: Session, claims: AuthClaims) -> User:
    user = (
        db.query(User)
        .filter(User.clerk_user_id == claims.clerk_user_id)
        .one_or_none()
    )
    if user is None:
        user = User(
            clerk_user_id=claims.clerk_user_id,
            email=claims.email,
            display_name=claims.display_name,
        )
        db.add(user)
        db.flush()
        return user

    changed = False
    if claims.email and claims.email != user.email:
        user.email = claims.email
        changed = True
    # Only fill empty display_name from JWT — never overwrite a user-set name.
    if claims.display_name and not user.display_name:
        user.display_name = claims.display_name
        changed = True
    if changed:
        db.flush()
    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer token. Log in with Clerk, then send Authorization: Bearer <jwt>",
            headers={"WWW-Authenticate": "Bearer"},
        )
    claims = verify_bearer_token(credentials.credentials)
    user = upsert_user_from_claims(db, claims)
    db.commit()
    db.refresh(user)
    return user


def auth_status() -> dict:
    mode = _auth_mode()
    info: dict = {
        "mode": mode,
        "clerk_publishable_key_configured": bool(_publishable_key()),
        "clerk_issuer_configured": bool(os.getenv("CLERK_ISSUER")),
        "dev_secret_configured": bool(os.getenv("PLANFLOW_DEV_JWT_SECRET")),
    }
    if mode == "clerk":
        try:
            info["issuer"] = get_clerk_issuer()
            info["jwks_url"] = get_jwks_url()
            info["ready"] = True
        except Exception as exc:  # noqa: BLE001
            info["ready"] = False
            info["error"] = str(exc)
    else:
        info["ready"] = bool(os.getenv("PLANFLOW_DEV_JWT_SECRET"))
    return info
