"""Shared test fixtures."""

import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Override upload dir and data dir before importing app
_tmp = tempfile.mkdtemp(prefix="pi_strategist_test_")
os.environ["UPLOAD_DIR"] = _tmp
os.environ["DATA_DIR"] = _tmp

from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    """FastAPI TestClient for synchronous tests."""
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def tmp_upload_dir() -> Path:
    """Return the temporary upload directory for this test session."""
    return Path(_tmp)


@pytest.fixture()
def session_headers(client) -> dict[str, str]:
    """Make an initial request to get session credentials, return headers dict."""
    resp = client.get("/api/v1/files")
    sid = resp.headers.get("x-session-id")
    token = resp.headers.get("x-session-token")
    assert sid, "Expected X-Session-ID in response"
    assert token, "Expected X-Session-Token in response"
    return {"X-Session-ID": sid, "X-Session-Token": token}
