"""Tests for analysis endpoints."""


def test_analysis_no_files(client):
    """Should reject analysis when no files provided."""
    resp = client.post("/api/v1/analysis/full", json={})
    assert resp.status_code == 400
    assert "At least one file" in resp.json()["detail"]


def test_analysis_missing_file(client):
    """Should return 404 when file ID doesn't exist."""
    resp = client.post(
        "/api/v1/analysis/full",
        json={"ded_file_id": "nonexistent-id"},
    )
    assert resp.status_code == 404


def test_list_analyses(client):
    resp = client.get("/api/v1/analyses")
    assert resp.status_code == 200
    assert "analyses" in resp.json()


def test_get_nonexistent_analysis(client):
    resp = client.get("/api/v1/analyses/nonexistent-id")
    assert resp.status_code == 404


def test_delete_nonexistent_analysis(client):
    resp = client.delete("/api/v1/analyses/nonexistent-id")
    assert resp.status_code == 404
