"""File storage management for uploaded files."""

import json
import uuid
import aiofiles
from pathlib import Path
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field

from app.config import settings
from app.core.database import get_db


@dataclass
class StoredFile:
    """Metadata for a stored file."""

    file_id: str
    filename: str
    file_type: str  # "ded" or "excel"
    path: Path
    size_bytes: int
    uploaded_at: datetime = field(default_factory=datetime.utcnow)


class FileStorage:
    """Manages file storage with SQLite-backed metadata."""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or settings.upload_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def store(self, content: bytes, filename: str, file_type: str) -> StoredFile:
        """Store uploaded file and persist metadata to SQLite."""
        file_id = str(uuid.uuid4())
        suffix = Path(filename).suffix
        file_path = self.base_dir / f"{file_id}{suffix}"

        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)

        now = datetime.utcnow()
        stored = StoredFile(
            file_id=file_id,
            filename=filename,
            file_type=file_type,
            path=file_path,
            size_bytes=len(content),
            uploaded_at=now,
        )

        db = await get_db()
        try:
            await db.execute(
                "INSERT INTO files (file_id, filename, file_type, path, size_bytes, uploaded_at) VALUES (?, ?, ?, ?, ?, ?)",
                (file_id, filename, file_type, str(file_path), len(content), now.isoformat()),
            )
            await db.commit()
        finally:
            await db.close()

        return stored

    async def get(self, file_id: str) -> Optional[StoredFile]:
        """Get file metadata by ID from SQLite."""
        db = await get_db()
        try:
            cursor = await db.execute("SELECT * FROM files WHERE file_id = ?", (file_id,))
            row = await cursor.fetchone()
            if not row:
                return None
            return StoredFile(
                file_id=row["file_id"],
                filename=row["filename"],
                file_type=row["file_type"],
                path=Path(row["path"]),
                size_bytes=row["size_bytes"],
                uploaded_at=datetime.fromisoformat(row["uploaded_at"]),
            )
        finally:
            await db.close()

    async def get_path(self, file_id: str) -> Optional[Path]:
        """Get file path by ID."""
        stored = await self.get(file_id)
        return stored.path if stored else None

    async def delete(self, file_id: str) -> bool:
        """Delete file and metadata."""
        stored = await self.get(file_id)
        if not stored:
            return False
        if stored.path.exists():
            stored.path.unlink()
        db = await get_db()
        try:
            await db.execute("DELETE FROM files WHERE file_id = ?", (file_id,))
            await db.commit()
        finally:
            await db.close()
        return True

    async def list_files(self) -> list[StoredFile]:
        """List all stored files."""
        db = await get_db()
        try:
            cursor = await db.execute("SELECT * FROM files ORDER BY uploaded_at DESC")
            rows = await cursor.fetchall()
            return [
                StoredFile(
                    file_id=row["file_id"],
                    filename=row["filename"],
                    file_type=row["file_type"],
                    path=Path(row["path"]),
                    size_bytes=row["size_bytes"],
                    uploaded_at=datetime.fromisoformat(row["uploaded_at"]),
                )
                for row in rows
            ]
        finally:
            await db.close()


# Global file storage instance
file_storage = FileStorage()
