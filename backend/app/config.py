"""Application configuration using Pydantic Settings."""

from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Settings
    api_title: str = "PI-Strategist API"
    api_version: str = "1.0.0"
    api_prefix: str = "/api/v1"
    debug: bool = False

    # CORS Settings
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:5173"]

    # File Storage
    upload_dir: Path = Path("uploads")
    max_upload_size_mb: int = 50

    # Session Settings
    session_ttl_hours: int = 24

    # AI Settings
    anthropic_api_key: Optional[str] = None

    # Analysis Defaults
    default_buffer_percentage: float = 0.20
    default_cd_target: float = 0.30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
