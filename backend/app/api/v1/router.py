"""API v1 router - aggregates all endpoint routers."""

from fastapi import APIRouter

from app.api.v1.endpoints import files, analysis, quick_check, health, ai_insights, objectives, risks

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(files.router, prefix="/files", tags=["files"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
api_router.include_router(analysis.saved_router, prefix="/analyses", tags=["saved-analyses"])
api_router.include_router(quick_check.router, prefix="/quick-check", tags=["quick-check"])
api_router.include_router(ai_insights.router, prefix="/ai", tags=["ai-insights"])
api_router.include_router(objectives.router, prefix="/objectives", tags=["objectives"])
api_router.include_router(risks.router, prefix="/risks", tags=["risks"])
