"""Tests for analysis endpoints."""


def test_analysis_no_files(client, session_headers):
    """Should reject analysis when no files provided."""
    resp = client.post("/api/v1/analysis/full", json={}, headers=session_headers)
    assert resp.status_code == 400
    assert "At least one file" in resp.json()["detail"]


def test_analysis_missing_file(client, session_headers):
    """Should return 404 when file ID doesn't exist."""
    resp = client.post(
        "/api/v1/analysis/full",
        json={"ded_file_id": "nonexistent-id"},
        headers=session_headers,
    )
    assert resp.status_code == 404


def test_list_analyses(client, session_headers):
    resp = client.get("/api/v1/analyses", headers=session_headers)
    assert resp.status_code == 200
    assert "analyses" in resp.json()


def test_get_nonexistent_analysis(client, session_headers):
    resp = client.get("/api/v1/analyses/nonexistent-id", headers=session_headers)
    assert resp.status_code == 404


def test_delete_nonexistent_analysis(client, session_headers):
    resp = client.delete("/api/v1/analyses/nonexistent-id", headers=session_headers)
    assert resp.status_code == 404
