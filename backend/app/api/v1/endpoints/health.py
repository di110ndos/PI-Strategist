"""Health check endpoints."""

import shutil
from pathlib import Path

from fastapi import APIRouter

from app.config import settings
from app.core.database import get_db

router = APIRouter()


@router.get("")
async def health():
    """API health check with subsystem status."""
    checks = {"status": "ok"}

    # Check upload directory
    upload_dir = settings.upload_dir
    checks["upload_dir_exists"] = upload_dir.exists()

    # Check disk space
    try:
        disk = shutil.disk_usage(str(upload_dir.parent))
        checks["disk_free_mb"] = round(disk.free / (1024 * 1024))
    except Exception:
        checks["disk_free_mb"] = None

    # Check database
    try:
        db = await get_db()
        await db.execute("SELECT 1")
        await db.close()
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = f"error: {exc}"
        checks["status"] = "degraded"

    # Check AI API availability
    checks["ai_configured"] = bool(settings.anthropic_api_key)

    return checks
