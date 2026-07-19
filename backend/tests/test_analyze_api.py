"""API tests for the /scan/analyze endpoints."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
FIXTURES = Path(__file__).parent / "fixtures"


def test_analyze_pasted_phishing() -> None:
    raw = (FIXTURES / "phishing.eml").read_text()
    resp = client.post("/api/v1/scan/analyze", json={"raw_email": raw})

    assert resp.status_code == 200
    body = resp.json()
    assert body["assessment"]["band"] == "critical"
    assert body["assessment"]["score"] >= 75
    assert body["features"]["link_mismatch_count"] == 1
    # The layers travel together: evidence, numbers, rule verdict, ML, fusion.
    assert body["parsed"]["reply_to_mismatch"] is True
    assert any(i["id"] == "risky_attachment" for i in body["assessment"]["indicators"])

    # ML + fusion present and well-formed regardless of whether a model is loaded.
    assert isinstance(body["ml"]["available"], bool)
    fusion = body["fusion"]
    assert 0 <= fusion["score"] <= 100
    assert fusion["method"] in {"fused", "rules_only"}
    # A confirmed-malicious executable attachment must floor the final score.
    assert fusion["critical_override"] is True
    assert fusion["score"] >= 90


def test_analyze_uploaded_benign() -> None:
    raw = (FIXTURES / "benign.eml").read_bytes()
    resp = client.post(
        "/api/v1/scan/analyze/file",
        files={"file": ("benign.eml", raw, "message/rfc822")},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["assessment"]["band"] == "low"
    assert body["assessment"]["score"] < 25


def test_analyze_oversized_rejected() -> None:
    resp = client.post("/api/v1/scan/analyze", json={"raw_email": "X" * 2_000_001})
    assert resp.status_code == 413
