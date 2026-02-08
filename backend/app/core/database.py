"""Async SQLite database for persisting files and analyses."""

import logging

import aiosqlite
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)

DB_PATH = settings.data_dir / "pi_strategist.db"

_CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    session_token TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    last_active_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS files (
    file_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    path TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    uploaded_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS analyses (
    analysis_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'completed',
    created_at TEXT NOT NULL,
    results TEXT NOT NULL,
    summary TEXT NOT NULL,
    metadata TEXT
);

CREATE TABLE IF NOT EXISTS objectives (
    objective_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    analysis_id TEXT,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    objective_type TEXT NOT NULL DEFAULT 'committed',
    business_value INTEGER NOT NULL DEFAULT 5,
    status TEXT NOT NULL DEFAULT 'planned',
    acceptance_criteria TEXT NOT NULL DEFAULT '',
    linked_stories TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS risks (
    risk_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    analysis_id TEXT,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    category TEXT NOT NULL DEFAULT 'general',
    probability INTEGER NOT NULL DEFAULT 3,
    impact INTEGER NOT NULL DEFAULT 3,
    risk_score INTEGER NOT NULL DEFAULT 9,
    owner TEXT NOT NULL DEFAULT '',
    mitigation_plan TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'open',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_files_session ON files(session_id);
CREATE INDEX IF NOT EXISTS idx_analyses_session ON analyses(session_id);
CREATE INDEX IF NOT EXISTS idx_objectives_session ON objectives(session_id);
CREATE INDEX IF NOT EXISTS idx_risks_session ON risks(session_id);
"""

_initialized = False


async def _migrate_add_session_columns(db: aiosqlite.Connection) -> None:
    """Add session_id column to existing tables if missing."""
    for table in ("files", "analyses"):
        cursor = await db.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in await cursor.fetchall()]
        if "session_id" not in columns:
            logger.info("Migrating table %s: adding session_id column", table)
            await db.execute(
                f"ALTER TABLE {table} ADD COLUMN session_id TEXT NOT NULL DEFAULT ''"
            )


async def init_db() -> None:
    """Called once at app startup to guarantee schema exists."""
    global _initialized
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = await aiosqlite.connect(str(DB_PATH))
    try:
        # Enable WAL mode for better concurrent access
        await db.execute("PRAGMA journal_mode=WAL")

        # Check if tables exist already (migration path)
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='files'"
        )
        existing = await cursor.fetchone()
        if existing:
            await _migrate_add_session_columns(db)
            await db.commit()

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
