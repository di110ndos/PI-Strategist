"""Tests for health endpoints."""


def test_root_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"


def test_api_health(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("ok", "degraded")
    assert "database" in data


def test_health_no_system_info(client):
    """Health endpoint should not expose system details."""
    resp = client.get("/api/v1/health")
    data = resp.json()
    assert "upload_dir_exists" not in data
    assert "disk_free_mb" not in data
    assert "ai_configured" not in data
