"""Health check endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def health():
    """API health check."""
    return {"status": "ok"}
