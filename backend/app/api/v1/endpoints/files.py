"""File upload and management endpoints."""

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime
from typing import Literal

from app.core.file_storage import file_storage
from app.config import settings

router = APIRouter()


class FileUploadResponse(BaseModel):
    """Response model for file upload."""

    file_id: str
    filename: str
    file_type: str
    size_bytes: int
    uploaded_at: datetime


class FileListResponse(BaseModel):
    """Response model for file list."""

    files: list[FileUploadResponse]


MAGIC_BYTES = {
    "xlsx": b"\x50\x4b\x03\x04",  # ZIP (OOXML)
    "xls": b"\xd0\xcf\x11\xe0",   # OLE2
    "docx": b"\x50\x4b\x03\x04",  # ZIP (OOXML)
    "pdf": b"%PDF",
}


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    file_type: Literal["ded", "excel"] = Query(..., description="Type of file being uploaded"),
):
    """Upload a DED document or Excel capacity planner."""
    # Validate file size
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)

    if size_mb > settings.max_upload_size_mb:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.max_upload_size_mb}MB",
        )

    # Validate file extension
    filename = file.filename or "unknown"
    suffix = filename.lower().split(".")[-1] if "." in filename else ""

    if file_type == "ded" and suffix not in ["docx", "doc", "md", "txt", "pdf"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid DED file type. Supported: docx, doc, md, txt, pdf",
        )

    if file_type == "excel" and suffix not in ["xlsx", "xls"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid Excel file type. Supported: xlsx, xls",
        )

    # Validate magic bytes for binary formats
    expected_magic = MAGIC_BYTES.get(suffix)
    if expected_magic and not content[:len(expected_magic)].startswith(expected_magic):
        raise HTTPException(
            status_code=400,
            detail=f"File content does not match expected {suffix.upper()} format",
        )

    # Store file
    stored = await file_storage.store(content, filename, file_type)

    return FileUploadResponse(
        file_id=stored.file_id,
        filename=stored.filename,
        file_type=stored.file_type,
        size_bytes=stored.size_bytes,
        uploaded_at=stored.uploaded_at,
    )


@router.get("", response_model=FileListResponse)
async def list_files():
    """List all uploaded files."""
    files = await file_storage.list_files()
    return FileListResponse(
        files=[
            FileUploadResponse(
                file_id=f.file_id,
                filename=f.filename,
                file_type=f.file_type,
                size_bytes=f.size_bytes,
                uploaded_at=f.uploaded_at,
            )
            for f in files
        ]
    )


@router.delete("/{file_id}")
async def delete_file(file_id: str):
    """Delete an uploaded file."""
    if not await file_storage.delete(file_id):
        raise HTTPException(status_code=404, detail="File not found")
    return {"status": "deleted", "file_id": file_id}
