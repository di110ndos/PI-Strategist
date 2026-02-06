"""Full analysis endpoint."""

import sys
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Add the src directory to the path
src_path = Path(__file__).parent.parent.parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from app.core.file_storage import file_storage
from app.models.responses import AnalysisResponse, AnalysisSummary

router = APIRouter()


class AnalysisRequest(BaseModel):
    """Request model for full analysis."""

    ded_file_id: Optional[str] = None
    excel_file_id: Optional[str] = None
    buffer_percentage: float = 0.20
    cd_target_percentage: float = 0.30


@router.post("/full", response_model=AnalysisResponse)
async def run_full_analysis(request: AnalysisRequest):
    """Run full DED and capacity analysis."""
    # Validate at least one file is provided
    if not request.ded_file_id and not request.excel_file_id:
        raise HTTPException(
            status_code=400,
            detail="At least one file (DED or Excel) must be provided",
        )

    # Get file paths
    ded_path = None
    excel_path = None

    if request.ded_file_id:
        ded_path = file_storage.get_path(request.ded_file_id)
        if not ded_path:
            raise HTTPException(status_code=404, detail="DED file not found")

    if request.excel_file_id:
        excel_path = file_storage.get_path(request.excel_file_id)
        if not excel_path:
            raise HTTPException(status_code=404, detail="Excel file not found")

    try:
        # Import analyzers and parsers
        from pi_strategist.parsers.ded_parser import DEDParser
        from pi_strategist.parsers.pi_planner_parser import PIPlannerParser
        from pi_strategist.analyzers.risk_analyzer import RiskAnalyzer
        from pi_strategist.analyzers.capacity_analyzer import CapacityAnalyzer
        from pi_strategist.analyzers.deployment_analyzer import DeploymentAnalyzer

        # Initialize
        ded_parser = DEDParser()
        pi_parser = PIPlannerParser()
        risk_analyzer = RiskAnalyzer()
        capacity_analyzer = CapacityAnalyzer()
        deployment_analyzer = DeploymentAnalyzer()

        # Parse files
        ded = None
        if ded_path:
            ded = ded_parser.parse(ded_path)

        capacity_plan = None
        pi_analysis = None
        if excel_path:
            pi_parser.default_buffer = request.buffer_percentage
            capacity_plan = pi_parser.parse(excel_path)
            pi_analysis = pi_parser.last_pi_analysis

        # Run analyzers
        red_flags = []
        if ded:
            red_flags = risk_analyzer.analyze(ded)

        capacity_analysis = []
        if capacity_plan:
            capacity_analyzer.default_buffer = request.buffer_percentage
            capacity_analysis = capacity_analyzer.analyze(capacity_plan, red_flags)

        deployment_clusters = []
        if capacity_plan:
            deployment_analyzer.cd_target_percentage = request.cd_target_percentage
            deployment_clusters = deployment_analyzer.analyze(capacity_plan, ded)

        # Build response
        analysis_id = str(uuid.uuid4())

        # Serialize results (convert dataclasses to dicts)
        def serialize(obj):
            if hasattr(obj, "__dict__"):
                return {k: serialize(v) for k, v in obj.__dict__.items()}
            elif isinstance(obj, list):
                return [serialize(item) for item in obj]
            elif isinstance(obj, dict):
                return {k: serialize(v) for k, v in obj.items()}
            elif hasattr(obj, "value"):  # Enum
                return obj.value
            else:
                return obj

        results = {
            "ded": serialize(ded) if ded else None,
            "capacity_plan": serialize(capacity_plan) if capacity_plan else None,
            "pi_analysis": serialize(pi_analysis) if pi_analysis else None,
            "red_flags": serialize(red_flags),
            "capacity_analysis": serialize(capacity_analysis),
            "deployment_clusters": serialize(deployment_clusters),
        }

        # Build summary
        critical_count = len([rf for rf in red_flags if rf.severity.value == "critical"])
        moderate_count = len([rf for rf in red_flags if rf.severity.value == "moderate"])
        low_count = len([rf for rf in red_flags if rf.severity.value == "low"])

        passing_sprints = len([ca for ca in capacity_analysis if ca.status.value == "pass"])
        failing_sprints = len([ca for ca in capacity_analysis if ca.status.value == "fail"])

        summary = AnalysisSummary(
            risk={
                "total": len(red_flags),
                "critical": critical_count,
                "moderate": moderate_count,
                "low": low_count,
            },
            capacity={
                "total_sprints": len(capacity_analysis),
                "passing": passing_sprints,
                "failing": failing_sprints,
            },
            deployment={
                "clusters": len(deployment_clusters),
            },
        )

        return AnalysisResponse(
            analysis_id=analysis_id,
            status="completed",
            created_at=datetime.utcnow(),
            results=results,
            summary=summary,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
