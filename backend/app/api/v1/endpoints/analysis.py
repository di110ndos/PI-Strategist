"""Full analysis endpoint."""

import json
import sys
import uuid
from dataclasses import fields
from pathlib import Path
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

# Ensure src/ is importable (editable install preferred: `pip install -e .`)
src_path = str(Path(__file__).parent.parent.parent.parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from app.core.file_storage import file_storage
from app.core.database import get_db
from app.core.session import get_session_id
from app.models.responses import AnalysisResponse, AnalysisSummary

router = APIRouter()
saved_router = APIRouter()


def serialize(obj):
    """Recursively serialize dataclasses, enums, and other types to JSON-safe dicts."""
    if obj is None:
        return None
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, (Path,)):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, tuple):
        return [serialize(item) for item in obj]
    if isinstance(obj, list):
        return [serialize(item) for item in obj]
    if isinstance(obj, dict):
        return {str(k): serialize(v) for k, v in obj.items()}
    if hasattr(obj, "__dataclass_fields__"):
        # Dataclass: serialize declared fields + @property values
        result = {f.name: serialize(getattr(obj, f.name)) for f in fields(obj)}
        for attr_name in dir(obj.__class__):
            if isinstance(getattr(obj.__class__, attr_name, None), property):
                try:
                    result[attr_name] = serialize(getattr(obj, attr_name))
                except Exception:
                    pass
        return result
    if hasattr(obj, "__dict__"):
        return {k: serialize(v) for k, v in obj.__dict__.items()}
    return str(obj)


class AnalysisRequest(BaseModel):
    """Request model for full analysis."""

    ded_file_id: Optional[str] = None
    excel_file_id: Optional[str] = None
    buffer_percentage: float = 0.20
    cd_target_percentage: float = 0.30


@router.post("/full", response_model=AnalysisResponse)
async def run_full_analysis(
    request: AnalysisRequest,
    session_id: str = Depends(get_session_id),
):
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
        ded_path = await file_storage.get_path(request.ded_file_id, session_id)
        if not ded_path:
            raise HTTPException(status_code=404, detail="DED file not found")

    if request.excel_file_id:
        excel_path = await file_storage.get_path(request.excel_file_id, session_id)
        if not excel_path:
            raise HTTPException(status_code=404, detail="Excel file not found")

    try:
        # Import analyzers and parsers
        from pi_strategist.parsers.ded_parser import DEDParser
        from pi_strategist.parsers.pi_planner_parser import PIPlannerParser
        from pi_strategist.analyzers.risk_analyzer import RiskAnalyzer
        from pi_strategist.analyzers.capacity_analyzer import CapacityAnalyzer
        from pi_strategist.analyzers.deployment_analyzer import DeploymentAnalyzer
        from pi_strategist.models import DeploymentStrategy

        # Initialize
        ded_parser = DEDParser()
        pi_parser = PIPlannerParser(default_buffer=request.buffer_percentage)
        risk_analyzer = RiskAnalyzer()
        capacity_analyzer = CapacityAnalyzer(default_buffer=request.buffer_percentage)
        deployment_analyzer = DeploymentAnalyzer()

        # Parse files
        ded = None
        if ded_path:
            ded = ded_parser.parse(ded_path)

        capacity_plan = None
        pi_analysis = None
        if excel_path:
            capacity_plan, pi_analysis = pi_parser.parse_with_analysis(excel_path)

        # Run analyzers
        red_flags = []
        if ded:
            red_flags = risk_analyzer.analyze(ded)

        capacity_analysis = []
        if capacity_plan:
            capacity_analysis = capacity_analyzer.analyze(capacity_plan, red_flags)

        deployment_clusters = []
        if capacity_plan:
            deployment_analyzer.cd_target_percentage = request.cd_target_percentage
            deployment_clusters = deployment_analyzer.analyze(capacity_plan, ded)

        # Build response
        analysis_id = str(uuid.uuid4())

        results = {
            "ded": serialize(ded),
            "capacity_plan": serialize(capacity_plan),
            "pi_analysis": serialize(pi_analysis),
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

        # Calculate average utilization
        avg_utilization = 0.0
        if capacity_analysis:
            utilizations = [ca.utilization_percent for ca in capacity_analysis]
            if utilizations:
                avg_utilization = sum(utilizations) / len(utilizations)

        # Calculate CD eligible percentage
        cd_eligible_percentage = 0.0
        if deployment_clusters:
            feature_flag_count = sum(
                1 for dc in deployment_clusters
                if dc.strategy == DeploymentStrategy.FEATURE_FLAG
            )
            total_clusters = len(deployment_clusters)
            if total_clusters > 0:
                cd_eligible_percentage = (feature_flag_count / total_clusters) * 100

        summary_data = {
            "risk": {
                "total": len(red_flags),
                "high": critical_count,
                "medium": moderate_count,
                "low": low_count,
            },
            "capacity": {
                "total_sprints": len(capacity_analysis),
                "passing": passing_sprints,
                "failing": failing_sprints,
                "average_utilization": avg_utilization,
            },
            "deployment": {
                "total_clusters": len(deployment_clusters),
                "cd_eligible_percentage": cd_eligible_percentage,
            },
        }

        summary = AnalysisSummary(**summary_data)

        # Persist to SQLite
        now = datetime.utcnow()
        db = await get_db()
        try:
            await db.execute(
                "INSERT INTO analyses (analysis_id, session_id, status, created_at, results, summary) VALUES (?, ?, ?, ?, ?, ?)",
                (analysis_id, session_id, "completed", now.isoformat(), json.dumps(results), json.dumps(summary_data)),
            )
            await db.commit()
        finally:
            await db.close()

        return AnalysisResponse(
            analysis_id=analysis_id,
            status="completed",
            created_at=now,
            results=results,
            summary=summary,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


class SaveAnalysisRequest(BaseModel):
    """Request to save an analysis."""

    name: str
    year: str
    quarter: str


class SavedAnalysisMetadata(BaseModel):
    """Metadata for a saved analysis."""

    id: str
    name: str
    year: str
    quarter: str
    saved_at: str
    source_file: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    summary: Optional[Dict[str, Any]] = None
    resources: Optional[Dict[str, Any]] = None
    projects: Optional[Dict[str, Any]] = None


@saved_router.get("", response_model=Dict[str, List[SavedAnalysisMetadata]])
async def list_saved_analyses(session_id: str = Depends(get_session_id)):
    """List all saved analyses for the current session."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT analysis_id, status, created_at, summary, metadata FROM analyses WHERE session_id = ? ORDER BY created_at DESC",
            (session_id,),
        )
        rows = await cursor.fetchall()
    finally:
        await db.close()

    analyses = []
    for row in rows:
        meta = json.loads(row["metadata"]) if row["metadata"] else {}
        summary = json.loads(row["summary"]) if row["summary"] else {}
        analyses.append(
            SavedAnalysisMetadata(
                id=row["analysis_id"],
                name=meta.get("name", "Unnamed"),
                year=meta.get("year", ""),
                quarter=meta.get("quarter", ""),
                saved_at=row["created_at"],
                source_file=meta.get("source_file"),
                metadata=meta or None,
                summary=summary or None,
            )
        )

    return {"analyses": analyses}


@saved_router.get("/{analysis_id}")
async def get_saved_analysis(analysis_id: str, session_id: str = Depends(get_session_id)):
    """Get a saved analysis by ID, scoped to session."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM analyses WHERE analysis_id = ? AND session_id = ?",
            (analysis_id, session_id),
        )
        row = await cursor.fetchone()
    finally:
        await db.close()

    if not row:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return {
        "analysis_id": row["analysis_id"],
        "status": row["status"],
        "created_at": row["created_at"],
        "results": json.loads(row["results"]),
        "summary": json.loads(row["summary"]),
        "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
    }


@saved_router.post("/{analysis_id}/save")
async def save_analysis(
    analysis_id: str,
    request: SaveAnalysisRequest,
    session_id: str = Depends(get_session_id),
):
    """Save an analysis with metadata."""
    meta = json.dumps({
        "name": request.name,
        "year": request.year,
        "quarter": request.quarter,
        "saved_at": datetime.utcnow().isoformat(),
    })

    db = await get_db()
    try:
        # Check if this analysis already exists for this session
        cursor = await db.execute(
            "SELECT analysis_id FROM analyses WHERE analysis_id = ? AND session_id = ?",
            (analysis_id, session_id),
        )
        row = await cursor.fetchone()
        if row:
            await db.execute(
                "UPDATE analyses SET metadata = ? WHERE analysis_id = ? AND session_id = ?",
                (meta, analysis_id, session_id),
            )
        else:
            # Create a new saved entry
            saved_id = str(uuid.uuid4())
            await db.execute(
                "INSERT INTO analyses (analysis_id, session_id, status, created_at, results, summary, metadata) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (saved_id, session_id, "saved", datetime.utcnow().isoformat(), "{}", "{}", meta),
            )
            analysis_id = saved_id
        await db.commit()
    finally:
        await db.close()

    return {"id": analysis_id, "status": "saved", "metadata": json.loads(meta)}


@saved_router.delete("/{analysis_id}")
async def delete_saved_analysis(analysis_id: str, session_id: str = Depends(get_session_id)):
    """Delete a saved analysis, scoped to session."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT analysis_id FROM analyses WHERE analysis_id = ? AND session_id = ?",
            (analysis_id, session_id),
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Analysis not found")
        await db.execute(
            "DELETE FROM analyses WHERE analysis_id = ? AND session_id = ?",
            (analysis_id, session_id),
        )
        await db.commit()
    finally:
        await db.close()

    return {"status": "deleted"}
