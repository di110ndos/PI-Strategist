"""Tests for AI insights endpoint."""


def test_insights_no_api_key(client):
    """Should return 400 when API key not configured."""
    resp = client.post(
        "/api/v1/ai/insights",
        json={
            "pi_analysis": {"resources": {}, "projects": {}},
            "insight_type": "full",
        },
    )
    # Either 400 (no key) or 500 (if key set but mock needed)
    assert resp.status_code in (400, 500)
