"""Async SQLite database for persisting files and analyses."""

import aiosqlite
from pathlib import Path

from app.config import settings

DB_PATH = settings.upload_dir / "pi_strategist.db"

_CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS files (
    file_id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    path TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    uploaded_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS analyses (
    analysis_id TEXT PRIMARY KEY,
    status TEXT NOT NULL DEFAULT 'completed',
    created_at TEXT NOT NULL,
    results TEXT NOT NULL,
    summary TEXT NOT NULL,
    metadata TEXT
);
"""

_initialized = False


async def init_db() -> None:
    """Called once at app startup to guarantee schema exists."""
    global _initialized
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = await aiosqlite.connect(str(DB_PATH))
    try:
        await db.executescript(_CREATE_TABLES)
        await db.commit()
    finally:
        await db.close()
    _initialized = True


async def get_db() -> aiosqlite.Connection:
    """Open a database connection. Tables must already exist via init_db()."""
    if not _initialized:
        await init_db()
    db = await aiosqlite.connect(str(DB_PATH))
    db.row_factory = aiosqlite.Row
    return db
