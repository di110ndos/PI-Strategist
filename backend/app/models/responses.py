"""Pydantic response models for API endpoints."""

from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


# ─── Quick Check Response Models ─────────────────────────────────


class RedFlagItem(BaseModel):
    """A single red flag finding."""

    term: str
    category: str
    severity: str  # "critical", "moderate", "low"
    suggested_metric: str
    negotiation_script: str


class LineRedFlags(BaseModel):
    """Red flags found in a single line of text."""

    line: str
    line_number: int
    flags: list[RedFlagItem]


class ObligationItem(BaseModel):
    """An extracted obligation statement."""

    text: str
    obligation_type: str  # "binding", "commitment", "negative"
    keyword: str


class ObligationsResult(BaseModel):
    """Obligations extraction result."""

    total: int
    binding_count: int
    commitment_count: int
    negative_count: int
    obligations: list[ObligationItem]


class SLAFindingItem(BaseModel):
    """An extracted SLA/SLO finding."""

    text: str
    metric_type: str
    value: Optional[str]
    is_valid: bool
    issues: list[str]


class SLAResult(BaseModel):
    """SLA/SLO extraction result."""

    total: int
    valid_count: int
    invalid_count: int
    findings: list[SLAFindingItem]


class QuickCheckResponse(BaseModel):
    """Response model for quick check analysis."""

    red_flags: list[LineRedFlags]
    obligations: ObligationsResult
    sla: SLAResult
    summary: dict[str, Any]


# ─── Analysis Response Models ────────────────────────────────────


class AnalysisSummary(BaseModel):
    """Summary metrics for an analysis."""

    risk: dict[str, int]  # total, critical, moderate, low
    capacity: dict[str, Any]  # total_sprints, passing, failing, utilization
    deployment: dict[str, Any]  # cd_percentage, clusters


class AnalysisResponse(BaseModel):
    """Response model for full analysis."""

    analysis_id: str
    status: str
    created_at: datetime
    results: dict[str, Any]  # Full results object
    summary: AnalysisSummary
