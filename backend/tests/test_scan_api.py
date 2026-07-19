"""API tests for the scan/parse endpoints."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_pasted_email() -> None:
    raw = (FIXTURES / "phishing.eml").read_text()
    resp = client.post("/api/v1/scan/parse", json={"raw_email": raw})

    assert resp.status_code == 200
    body = resp.json()
    assert body["reply_to_mismatch"] is True
    assert body["auth"]["spf"] == "fail"
    assert any(u["anchor_mismatch"] for u in body["urls"])


def test_parse_uploaded_file() -> None:
    raw = (FIXTURES / "benign.eml").read_bytes()
    resp = client.post(
        "/api/v1/scan/parse/file",
        files={"file": ("benign.eml", raw, "message/rfc822")},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["subject"] == "Your weekly Acme digest"
    assert body["auth"]["dmarc"] == "pass"


def test_empty_paste_is_rejected() -> None:
    resp = client.post("/api/v1/scan/parse", json={"raw_email": ""})
    assert resp.status_code == 422  # fails min_length validation


def test_empty_file_is_rejected() -> None:
    resp = client.post(
        "/api/v1/scan/parse/file",
        files={"file": ("empty.eml", b"", "message/rfc822")},
    )
    assert resp.status_code == 400


def test_oversized_paste_is_rejected() -> None:
    huge = "X" * (2_000_001)
    resp = client.post("/api/v1/scan/parse", json={"raw_email": huge})
    assert resp.status_code == 413
