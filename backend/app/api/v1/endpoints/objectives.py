"""PI Objectives CRUD endpoints."""

import json
import uuid
from datetime import datetime
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.session import get_session_id

router = APIRouter()


# --- Pydantic models ---

ObjectiveType = Literal["committed", "stretch"]
ObjectiveStatus = Literal["planned", "in_progress", "completed", "at_risk"]


class ObjectiveCreate(BaseModel):
    """Request body for creating an objective."""

    name: str
    description: str = ""
    objective_type: ObjectiveType = "committed"
    business_value: int = Field(default=5, ge=1, le=10)
    status: ObjectiveStatus = "planned"
    acceptance_criteria: str = ""
    linked_stories: list[str] = []
    analysis_id: Optional[str] = None


class ObjectiveUpdate(BaseModel):
    """Request body for updating an objective."""

    name: Optional[str] = None
    description: Optional[str] = None
    objective_type: Optional[ObjectiveType] = None
    business_value: Optional[int] = Field(default=None, ge=1, le=10)
    status: Optional[ObjectiveStatus] = None
    acceptance_criteria: Optional[str] = None
    linked_stories: Optional[list[str]] = None
    analysis_id: Optional[str] = None


class ObjectiveResponse(BaseModel):
    """Response model for a single objective."""

    objective_id: str
    session_id: str
    analysis_id: Optional[str] = None
    name: str
    description: str
    objective_type: ObjectiveType
    business_value: int
    status: ObjectiveStatus
    acceptance_criteria: str
    linked_stories: list[str]
    created_at: str
    updated_at: str


class ObjectiveListResponse(BaseModel):
    """Response model for listing objectives."""

    objectives: list[ObjectiveResponse]


# --- Helpers ---

def _row_to_response(row) -> ObjectiveResponse:
    """Convert a database row to an ObjectiveResponse."""
    return ObjectiveResponse(
        objective_id=row["objective_id"],
        session_id=row["session_id"],
        analysis_id=row["analysis_id"],
        name=row["name"],
        description=row["description"],
        objective_type=row["objective_type"],
        business_value=row["business_value"],
        status=row["status"],
        acceptance_criteria=row["acceptance_criteria"],
        linked_stories=json.loads(row["linked_stories"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


# --- Endpoints ---

@router.post("", response_model=ObjectiveResponse, status_code=201)
async def create_objective(
    body: ObjectiveCreate,
    session_id: str = Depends(get_session_id),
):
    """Create a new PI objective."""
    objective_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    db = await get_db()
    try:
        await db.execute(
            """INSERT INTO objectives
               (objective_id, session_id, analysis_id, name, description,
                objective_type, business_value, status, acceptance_criteria,
                linked_stories, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                objective_id,
                session_id,
                body.analysis_id,
                body.name,
                body.description,
                body.objective_type,
                body.business_value,
                body.status,
                body.acceptance_criteria,
                json.dumps(body.linked_stories),
                now,
                now,
            ),
        )
        await db.commit()

        cursor = await db.execute(
            "SELECT * FROM objectives WHERE objective_id = ? AND session_id = ?",
            (objective_id, session_id),
        )
        row = await cursor.fetchone()
    finally:
        await db.close()

    return _row_to_response(row)


@router.get("", response_model=ObjectiveListResponse)
async def list_objectives(session_id: str = Depends(get_session_id)):
    """List all objectives for the current session."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM objectives WHERE session_id = ? ORDER BY created_at DESC",
            (session_id,),
        )
        rows = await cursor.fetchall()
    finally:
        await db.close()

    return ObjectiveListResponse(
        objectives=[_row_to_response(row) for row in rows]
    )


@router.get("/{objective_id}", response_model=ObjectiveResponse)
async def get_objective(
    objective_id: str,
    session_id: str = Depends(get_session_id),
):
    """Get a single objective by ID."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM objectives WHERE objective_id = ? AND session_id = ?",
            (objective_id, session_id),
        )
        row = await cursor.fetchone()
    finally:
        await db.close()

    if not row:
        raise HTTPException(status_code=404, detail="Objective not found")

    return _row_to_response(row)


@router.put("/{objective_id}", response_model=ObjectiveResponse)
async def update_objective(
    objective_id: str,
    body: ObjectiveUpdate,
    session_id: str = Depends(get_session_id),
):
    """Update an existing objective."""
    db = await get_db()
    try:
        # Fetch existing
        cursor = await db.execute(
            "SELECT * FROM objectives WHERE objective_id = ? AND session_id = ?",
            (objective_id, session_id),
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Objective not found")

        # Build update fields
        updates = body.model_dump(exclude_unset=True)
        if not updates:
            return _row_to_response(row)

        # Serialize linked_stories if present
        if "linked_stories" in updates:
            updates["linked_stories"] = json.dumps(updates["linked_stories"])

        updates["updated_at"] = datetime.utcnow().isoformat()

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [objective_id, session_id]

        await db.execute(
            f"UPDATE objectives SET {set_clause} WHERE objective_id = ? AND session_id = ?",
            values,
        )
        await db.commit()

        # Re-fetch
        cursor = await db.execute(
            "SELECT * FROM objectives WHERE objective_id = ? AND session_id = ?",
            (objective_id, session_id),
        )
        row = await cursor.fetchone()
    finally:
        await db.close()

    return _row_to_response(row)


@router.delete("/{objective_id}")
async def delete_objective(
    objective_id: str,
    session_id: str = Depends(get_session_id),
):
    """Delete an objective."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT objective_id FROM objectives WHERE objective_id = ? AND session_id = ?",
            (objective_id, session_id),
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Objective not found")

        await db.execute(
            "DELETE FROM objectives WHERE objective_id = ? AND session_id = ?",
            (objective_id, session_id),
        )
        await db.commit()
    finally:
        await db.close()

    return {"status": "deleted", "objective_id": objective_id}
