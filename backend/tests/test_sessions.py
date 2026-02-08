"""Tests for session isolation and security."""

import io


def _get_session(client) -> dict[str, str]:
    """Helper: make a request and extract session headers."""
    resp = client.get("/api/v1/files")
    return {
        "X-Session-ID": resp.headers["x-session-id"],
        "X-Session-Token": resp.headers["x-session-token"],
    }


def test_auto_session_creation(client):
    """First request without headers should create a session."""
    resp = client.get("/api/v1/files")
    assert resp.status_code == 200
    assert resp.headers.get("x-session-id")
    assert resp.headers.get("x-session-token")


def test_session_reuse(client):
    """Subsequent requests with valid headers should work without new tokens."""
    headers = _get_session(client)
    resp = client.get("/api/v1/files", headers=headers)
    assert resp.status_code == 200
    # No new token should be issued when reusing valid session
    assert not resp.headers.get("x-session-token")


def test_invalid_token_returns_401(client):
    """Fabricated session credentials should return 401."""
    headers = {
        "X-Session-ID": "fake-session-id",
        "X-Session-Token": "fake-token",
    }
    resp = client.get("/api/v1/files", headers=headers)
    assert resp.status_code == 401


def test_partial_headers_returns_401(client):
    """Sending only session ID without token should return 401."""
    headers = {"X-Session-ID": "some-id"}
    resp = client.get("/api/v1/files", headers=headers)
    assert resp.status_code == 401


def test_health_exempt_from_session(client):
    """Health endpoints should work without session headers."""
    resp = client.get("/health")
    assert resp.status_code == 200

    resp = client.get("/api/v1/health")
    assert resp.status_code == 200


def test_session_isolation_files(client):
    """Session A's files should not be visible to Session B."""
    # Session A uploads a file
    session_a = _get_session(client)
    upload_resp = client.post(
        "/api/v1/files/upload?file_type=ded",
        files={"file": ("secret.txt", io.BytesIO(b"secret data"), "text/plain")},
        headers=session_a,
    )
    assert upload_resp.status_code == 200
    file_id = upload_resp.json()["file_id"]

    # Session A can see its file
    list_a = client.get("/api/v1/files", headers=session_a)
    assert any(f["file_id"] == file_id for f in list_a.json()["files"])

    # Session B gets a fresh session
    session_b = _get_session(client)
    assert session_b["X-Session-ID"] != session_a["X-Session-ID"]

    # Session B cannot see Session A's files
    list_b = client.get("/api/v1/files", headers=session_b)
    assert not any(f["file_id"] == file_id for f in list_b.json()["files"])


def test_cross_session_delete_blocked(client):
    """Session B cannot delete Session A's files."""
    # Session A uploads a file
    session_a = _get_session(client)
    upload_resp = client.post(
        "/api/v1/files/upload?file_type=ded",
        files={"file": ("owned.txt", io.BytesIO(b"mine"), "text/plain")},
        headers=session_a,
    )
    file_id = upload_resp.json()["file_id"]

    # Session B tries to delete it
    session_b = _get_session(client)
    resp = client.delete(f"/api/v1/files/{file_id}", headers=session_b)
    assert resp.status_code == 404

    # File still exists for Session A
    list_a = client.get("/api/v1/files", headers=session_a)
    assert any(f["file_id"] == file_id for f in list_a.json()["files"])


def test_security_headers_present(client):
    """All responses should include security headers."""
    resp = client.get("/health")
    assert resp.headers.get("x-content-type-options") == "nosniff"
    assert resp.headers.get("x-frame-options") == "DENY"
    assert resp.headers.get("referrer-policy") == "strict-origin-when-cross-origin"
