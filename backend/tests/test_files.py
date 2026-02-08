"""Tests for file upload endpoints."""

import io


def test_upload_text_ded(client):
    """Upload a plain-text DED file."""
    content = b"The system shall be fast and user-friendly."
    resp = client.post(
        "/api/v1/files/upload?file_type=ded",
        files={"file": ("test.txt", io.BytesIO(content), "text/plain")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["filename"] == "test.txt"
    assert data["file_type"] == "ded"
    assert data["size_bytes"] == len(content)
    return data["file_id"]


def test_upload_invalid_extension(client):
    """Reject file with unsupported extension."""
    resp = client.post(
        "/api/v1/files/upload?file_type=excel",
        files={"file": ("data.csv", io.BytesIO(b"a,b,c"), "text/csv")},
    )
    assert resp.status_code == 400


def test_list_files(client):
    # Upload a file first
    client.post(
        "/api/v1/files/upload?file_type=ded",
        files={"file": ("list_test.txt", io.BytesIO(b"hello"), "text/plain")},
    )
    resp = client.get("/api/v1/files")
    assert resp.status_code == 200
    assert len(resp.json()["files"]) >= 1


def test_delete_file(client):
    # Upload then delete
    upload = client.post(
        "/api/v1/files/upload?file_type=ded",
        files={"file": ("del.txt", io.BytesIO(b"bye"), "text/plain")},
    )
    fid = upload.json()["file_id"]
    resp = client.delete(f"/api/v1/files/{fid}")
    assert resp.status_code == 200


def test_delete_nonexistent(client):
    resp = client.delete("/api/v1/files/nonexistent-id")
    assert resp.status_code == 404
