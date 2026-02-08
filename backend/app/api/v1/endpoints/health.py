"""Health check endpoints."""

from fastapi import APIRouter

from app.core.database import get_db

router = APIRouter()


@router.get("")
async def health():
    """API health check — only reports status and database connectivity."""
    checks = {"status": "ok"}

    try:
        db = await get_db()
        await db.execute("SELECT 1")
        await db.close()
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = f"error: {exc}"
        checks["status"] = "degraded"

    return checks
