"""Quick check endpoint for text analysis."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.quick_check_service import quick_check_service
from app.models.responses import QuickCheckResponse

router = APIRouter()


class QuickCheckRequest(BaseModel):
    """Request model for quick check."""

    text: str


@router.post("", response_model=QuickCheckResponse)
async def quick_check(request: QuickCheckRequest):
    """Analyze text for red flags, obligations, and SLA metrics."""
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    if len(request.text) > 100000:  # ~100KB limit
        raise HTTPException(status_code=400, detail="Text too long. Maximum 100,000 characters.")

    try:
        result = quick_check_service.analyze_text(request.text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
