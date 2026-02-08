"""Risk Register CRUD endpoints."""

import uuid
from datetime import datetime
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.session import get_session_id

router = APIRouter()


# --- Pydantic models ---

RiskCategory = Literal[
    "technical", "resource", "schedule", "scope", "external", "general"
]
RiskStatus = Literal["open", "mitigating", "mitigated", "accepted", "closed"]


class RiskCreate(BaseModel):
    """Request body for creating a risk."""

    title: str
    description: str = ""
    category: RiskCategory = "general"
    probability: int = Field(default=3, ge=1, le=5)
    impact: int = Field(default=3, ge=1, le=5)
    owner: str = ""
    mitigation_plan: str = ""
    status: RiskStatus = "open"
    analysis_id: Optional[str] = None


class RiskUpdate(BaseModel):
    """Request body for updating a risk."""

    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[RiskCategory] = None
    probability: Optional[int] = Field(default=None, ge=1, le=5)
    impact: Optional[int] = Field(default=None, ge=1, le=5)
    owner: Optional[str] = None
    mitigation_plan: Optional[str] = None
    status: Optional[RiskStatus] = None
    analysis_id: Optional[str] = None


class RiskResponse(BaseModel):
    """Response model for a single risk."""

    risk_id: str
    session_id: str
    analysis_id: Optional[str] = None
    title: str
    description: str
    category: RiskCategory
    probability: int
    impact: int
    risk_score: int
    owner: str
    mitigation_plan: str
    status: RiskStatus
    created_at: str
    updated_at: str


class RiskListResponse(BaseModel):
    """Response model for listing risks."""

    risks: list[RiskResponse]


class RiskSummaryResponse(BaseModel):
    """Response model for risk summary."""

    total: int
    by_status: dict[str, int]
    average_score: float
    heat_map: list[list[int]]


# --- Helpers ---

def _row_to_response(row) -> RiskResponse:
    """Convert a database row to a RiskResponse."""
    return RiskResponse(
        risk_id=row["risk_id"],
        session_id=row["session_id"],
        analysis_id=row["analysis_id"],
        title=row["title"],
        description=row["description"],
        category=row["category"],
        probability=row["probability"],
        impact=row["impact"],
        risk_score=row["risk_score"],
        owner=row["owner"],
        mitigation_plan=row["mitigation_plan"],
        status=row["status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _build_heat_map(rows) -> list[list[int]]:
    """Build a 5x5 heat map grid (probability x impact).

    Returns a 5x5 list where grid[prob-1][impact-1] = count of risks.
    Rows represent probability (1-5), columns represent impact (1-5).
    """
    grid = [[0 for _ in range(5)] for _ in range(5)]
    for row in rows:
        p = row["probability"]
        i = row["impact"]
        if 1 <= p <= 5 and 1 <= i <= 5:
            grid[p - 1][i - 1] += 1
    return grid


# --- Endpoints ---

@router.get("/summary", response_model=RiskSummaryResponse)
async def get_risk_summary(session_id: str = Depends(get_session_id)):
    """Return risk summary: counts by status, average score, and heat map data."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM risks WHERE session_id = ?",
            (session_id,),
        )
        rows = await cursor.fetchall()
    finally:
        await db.close()

    if not rows:
        return RiskSummaryResponse(
            total=0,
            by_status={},
            average_score=0.0,
            heat_map=[[0] * 5 for _ in range(5)],
        )

    # Count by status
    by_status: dict[str, int] = {}
    total_score = 0
    for row in rows:
        status = row["status"]
        by_status[status] = by_status.get(status, 0) + 1
        total_score += row["risk_score"]

    average_score = round(total_score / len(rows), 2)
    heat_map = _build_heat_map(rows)

    return RiskSummaryResponse(
        total=len(rows),
        by_status=by_status,
        average_score=average_score,
        heat_map=heat_map,
    )


@router.post("", response_model=RiskResponse, status_code=201)
async def create_risk(
    body: RiskCreate,
    session_id: str = Depends(get_session_id),
):
    """Create a new risk entry."""
    risk_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    risk_score = body.probability * body.impact

    db = await get_db()
    try:
        await db.execute(
            """INSERT INTO risks
               (risk_id, session_id, analysis_id, title, description,
                category, probability, impact, risk_score, owner,
                mitigation_plan, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                risk_id,
                session_id,
                body.analysis_id,
                body.title,
                body.description,
                body.category,
                body.probability,
                body.impact,
                risk_score,
                body.owner,
                body.mitigation_plan,
                body.status,
                now,
                now,
            ),
        )
        await db.commit()

        cursor = await db.execute(
            "SELECT * FROM risks WHERE risk_id = ? AND session_id = ?",
            (risk_id, session_id),
        )
        row = await cursor.fetchone()
    finally:
        await db.close()

    return _row_to_response(row)


@router.get("", response_model=RiskListResponse)
async def list_risks(
    session_id: str = Depends(get_session_id),
    status: Optional[RiskStatus] = Query(default=None, description="Filter by risk status"),
):
    """List all risks for the current session, with optional status filter."""
    db = await get_db()
    try:
        if status:
            cursor = await db.execute(
                "SELECT * FROM risks WHERE session_id = ? AND status = ? ORDER BY risk_score DESC",
                (session_id, status),
            )
        else:
            cursor = await db.execute(
                "SELECT * FROM risks WHERE session_id = ? ORDER BY risk_score DESC",
                (session_id,),
            )
        rows = await cursor.fetchall()
    finally:
        await db.close()

    return RiskListResponse(risks=[_row_to_response(row) for row in rows])


@router.get("/{risk_id}", response_model=RiskResponse)
async def get_risk(
    risk_id: str,
    session_id: str = Depends(get_session_id),
):
    """Get a single risk by ID."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM risks WHERE risk_id = ? AND session_id = ?",
            (risk_id, session_id),
        )
        row = await cursor.fetchone()
    finally:
        await db.close()

    if not row:
        raise HTTPException(status_code=404, detail="Risk not found")

    return _row_to_response(row)


@router.put("/{risk_id}", response_model=RiskResponse)
async def update_risk(
    risk_id: str,
    body: RiskUpdate,
    session_id: str = Depends(get_session_id),
):
    """Update an existing risk. Recalculates risk_score if probability or impact changes."""
    db = await get_db()
    try:
        # Fetch existing
        cursor = await db.execute(
            "SELECT * FROM risks WHERE risk_id = ? AND session_id = ?",
            (risk_id, session_id),
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Risk not found")

        # Build update fields
        updates = body.model_dump(exclude_unset=True)
        if not updates:
            return _row_to_response(row)

        # Recalculate risk_score if probability or impact changed
        probability = updates.get("probability", row["probability"])
        impact = updates.get("impact", row["impact"])
        if "probability" in updates or "impact" in updates:
            updates["risk_score"] = probability * impact

        updates["updated_at"] = datetime.utcnow().isoformat()

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [risk_id, session_id]

        await db.execute(
            f"UPDATE risks SET {set_clause} WHERE risk_id = ? AND session_id = ?",
            values,
        )
        await db.commit()

        # Re-fetch
        cursor = await db.execute(
            "SELECT * FROM risks WHERE risk_id = ? AND session_id = ?",
            (risk_id, session_id),
        )
        row = await cursor.fetchone()
    finally:
        await db.close()

    return _row_to_response(row)


@router.delete("/{risk_id}")
async def delete_risk(
    risk_id: str,
    session_id: str = Depends(get_session_id),
):
    """Delete a risk."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT risk_id FROM risks WHERE risk_id = ? AND session_id = ?",
            (risk_id, session_id),
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Risk not found")

        await db.execute(
            "DELETE FROM risks WHERE risk_id = ? AND session_id = ?",
            (risk_id, session_id),
        )
        await db.commit()
    finally:
        await db.close()

    return {"status": "deleted", "risk_id": risk_id}
