"""Server-generated session management with token-based validation."""

import hashlib
import logging
import secrets
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

from app.config import settings
from app.core.database import get_db

logger = logging.getLogger(__name__)

# Paths exempt from session validation
_EXEMPT_PATHS = frozenset({
    "/health",
    f"{settings.api_prefix}/health",
    f"{settings.api_prefix}/docs",
    f"{settings.api_prefix}/openapi.json",
    f"{settings.api_prefix}/redoc",
})


def _hash_token(raw_token: str) -> str:
    """SHA-256 hash of a raw session token."""
    return hashlib.sha256(raw_token.encode()).hexdigest()


async def create_session() -> tuple[str, str]:
    """Create a new session. Returns (session_id, raw_token)."""
    session_id = str(uuid.uuid4())
    raw_token = secrets.token_hex(32)
    hashed = _hash_token(raw_token)
    now = datetime.utcnow().isoformat()

    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO sessions (session_id, session_token, created_at, last_active_at) VALUES (?, ?, ?, ?)",
            (session_id, hashed, now, now),
        )
        await db.commit()
    finally:
        await db.close()

    return session_id, raw_token


async def validate_session(session_id: str, raw_token: str) -> bool:
    """Validate a session by checking hash match. Updates last_active_at on success."""
    hashed = _hash_token(raw_token)

    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT session_token FROM sessions WHERE session_id = ?",
            (session_id,),
        )
        row = await cursor.fetchone()
        if not row or row["session_token"] != hashed:
            return False

        await db.execute(
            "UPDATE sessions SET last_active_at = ? WHERE session_id = ?",
            (datetime.utcnow().isoformat(), session_id),
        )
        await db.commit()
        return True
    finally:
        await db.close()


async def cleanup_expired_sessions(ttl_hours: int | None = None) -> int:
    """Delete expired sessions along with their files and analyses.

    Returns the number of sessions deleted.
    """
    ttl = ttl_hours if ttl_hours is not None else settings.session_ttl_hours
    cutoff = (datetime.utcnow() - timedelta(hours=ttl)).isoformat()

    db = await get_db()
    try:
        # Find expired sessions
        cursor = await db.execute(
            "SELECT session_id FROM sessions WHERE last_active_at < ?", (cutoff,)
        )
        expired = [row["session_id"] for row in await cursor.fetchall()]

        if not expired:
            return 0

        placeholders = ",".join("?" for _ in expired)

        # Delete files from disk
        file_cursor = await db.execute(
            f"SELECT path FROM files WHERE session_id IN ({placeholders})", expired
        )
        for row in await file_cursor.fetchall():
            try:
                p = Path(row["path"])
                if p.exists():
                    p.unlink()
            except OSError:
                pass

        # Delete DB records
        await db.execute(
            f"DELETE FROM files WHERE session_id IN ({placeholders})", expired
        )
        await db.execute(
            f"DELETE FROM analyses WHERE session_id IN ({placeholders})", expired
        )
        await db.execute(
            f"DELETE FROM objectives WHERE session_id IN ({placeholders})", expired
        )
        await db.execute(
            f"DELETE FROM risks WHERE session_id IN ({placeholders})", expired
        )
        await db.execute(
            f"DELETE FROM sessions WHERE session_id IN ({placeholders})", expired
        )
        await db.commit()

        logger.info("Cleaned up %d expired sessions", len(expired))
        return len(expired)
    finally:
        await db.close()


class SessionMiddleware(BaseHTTPMiddleware):
    """Validates or creates sessions on every request."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Skip exempt paths
        if request.url.path in _EXEMPT_PATHS:
            return await call_next(request)

        # Skip OPTIONS (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        session_id = request.headers.get("x-session-id")
        session_token = request.headers.get("x-session-token")

        if not session_id and not session_token:
            # No session — create one
            new_id, raw_token = await create_session()
            request.state.session_id = new_id
            response = await call_next(request)
            response.headers["X-Session-ID"] = new_id
            response.headers["X-Session-Token"] = raw_token
            return response

        if not session_id or not session_token:
            return JSONResponse(
                status_code=401,
                content={"detail": "Both X-Session-ID and X-Session-Token headers are required"},
            )

        valid = await validate_session(session_id, session_token)
        if not valid:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or expired session"},
            )

        request.state.session_id = session_id
        return await call_next(request)


async def get_session_id(request: Request) -> str:
    """FastAPI Depends() that extracts validated session_id from request.state."""
    return request.state.session_id
