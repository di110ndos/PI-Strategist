"""File storage management for uploaded files."""

import uuid
import aiofiles
from pathlib import Path
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field

from app.config import settings


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
    """Manages temporary file storage for uploaded files."""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or settings.upload_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._files: dict[str, StoredFile] = {}

    async def store(self, content: bytes, filename: str, file_type: str) -> StoredFile:
        """Store uploaded file and return metadata."""
        file_id = str(uuid.uuid4())
        suffix = Path(filename).suffix
        file_path = self.base_dir / f"{file_id}{suffix}"

        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)

        stored = StoredFile(
            file_id=file_id,
            filename=filename,
            file_type=file_type,
            path=file_path,
            size_bytes=len(content),
        )

        self._files[file_id] = stored
        return stored

    def get(self, file_id: str) -> Optional[StoredFile]:
        """Get file metadata by ID."""
        return self._files.get(file_id)

    def get_path(self, file_id: str) -> Optional[Path]:
        """Get file path by ID."""
        stored = self._files.get(file_id)
        return stored.path if stored else None

    def delete(self, file_id: str) -> bool:
        """Delete file and metadata."""
        stored = self._files.pop(file_id, None)
        if stored and stored.path.exists():
            stored.path.unlink()
            return True
        return False

    def list_files(self) -> list[StoredFile]:
        """List all stored files."""
        return list(self._files.values())


# Global file storage instance
file_storage = FileStorage()
