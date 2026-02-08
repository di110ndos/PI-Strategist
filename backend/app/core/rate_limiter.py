"""In-memory sliding-window rate limiter per session."""

import time
from collections import defaultdict

from fastapi import HTTPException, Request, Depends

from app.config import settings
from app.core.session import get_session_id

# session_id -> list of request timestamps
_request_log: dict[str, list[float]] = defaultdict(list)


def _cleanup_window(timestamps: list[float], window_seconds: float) -> list[float]:
    """Remove timestamps outside the sliding window."""
    cutoff = time.monotonic() - window_seconds
    return [t for t in timestamps if t > cutoff]


async def rate_limit_ai(
    request: Request,
    session_id: str = Depends(get_session_id),
) -> None:
    """Dependency that enforces per-session rate limiting on AI endpoints."""
    max_requests = settings.rate_limit_ai_per_minute
    window = 60.0  # seconds

    timestamps = _cleanup_window(_request_log[session_id], window)
    if len(timestamps) >= max_requests:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Maximum {max_requests} AI requests per minute.",
        )

    timestamps.append(time.monotonic())
    _request_log[session_id] = timestamps
