"""FastAPI application entry point."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.api.v1.router import api_router
from app.core.database import init_db
from app.core.logging import setup_logging
from app.core.session import SessionMiddleware, cleanup_expired_sessions

logger = logging.getLogger(__name__)

_cleanup_task: asyncio.Task | None = None


async def _periodic_session_cleanup() -> None:
    """Background task that cleans up expired sessions every hour."""
    while True:
        try:
            await asyncio.sleep(3600)
            deleted = await cleanup_expired_sessions()
            if deleted:
                logger.info("Session cleanup: removed %d expired sessions", deleted)
        except asyncio.CancelledError:
            break
        except Exception:
            logger.exception("Session cleanup failed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    global _cleanup_task
    setup_logging(json_format=not settings.debug, level="DEBUG" if settings.debug else "INFO")
    await init_db()
    _cleanup_task = asyncio.create_task(_periodic_session_cleanup())
    yield
    if _cleanup_task:
        _cleanup_task.cancel()
        try:
            await _cleanup_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    openapi_url=f"{settings.api_prefix}/openapi.json",
    docs_url=f"{settings.api_prefix}/docs",
    redoc_url=f"{settings.api_prefix}/redoc",
    lifespan=lifespan,
)

# CORS middleware — tightened methods and headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-Session-ID", "X-Session-Token", "Authorization"],
    expose_headers=["X-Session-ID", "X-Session-Token"],
)

# Session middleware — validates/creates sessions
app.add_middleware(SessionMiddleware)


@app.middleware("http")
async def security_headers(request: Request, call_next) -> Response:
    """Add security headers to every response."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Return generic error in production, detail when DEBUG=true."""
    if settings.debug:
        detail = str(exc)
    else:
        detail = "An internal error occurred. Please try again later."
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": detail})


# Include API router
app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.api_version}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
