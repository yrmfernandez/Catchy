"""Scan persistence + history/compare tests."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
FIXTURES = Path(__file__).parent / "fixtures"
PHISH = (FIXTURES / "phishing.eml").read_text()
BENIGN = (FIXTURES / "benign.eml").read_text()


def _auth(email: str) -> dict:
    resp = client.post("/api/v1/auth/register", json={"email": email, "password": "password123"})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_anonymous_scan_is_not_saved() -> None:
    resp = client.post("/api/v1/scan/analyze", json={"raw_email": PHISH})
    assert resp.status_code == 200
    assert "X-Scan-Id" not in resp.headers


def test_authenticated_scan_saved_listed_and_fetchable() -> None:
    headers = _auth("owner@example.com")

    scan = client.post("/api/v1/scan/analyze", json={"raw_email": PHISH}, headers=headers)
    assert scan.status_code == 200
    scan_id = scan.headers["X-Scan-Id"]

    listing = client.get("/api/v1/scans", headers=headers)
    assert listing.status_code == 200
    assert any(item["id"] == scan_id for item in listing.json())

    detail = client.get(f"/api/v1/scans/{scan_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["result"]["fusion"]["band"] == "critical"


def test_history_requires_auth() -> None:
    assert client.get("/api/v1/scans").status_code == 401


def test_users_cannot_read_each_others_scans() -> None:
    owner = _auth("owner2@example.com")
    other = _auth("intruder@example.com")

    scan = client.post("/api/v1/scan/analyze", json={"raw_email": PHISH}, headers=owner)
    scan_id = scan.headers["X-Scan-Id"]

    # The intruder gets 404 (not 403) — the scan simply doesn't exist for them.
    assert client.get(f"/api/v1/scans/{scan_id}", headers=other).status_code == 404


def test_compare_two_scans() -> None:
    headers = _auth("comparer@example.com")
    a = client.post("/api/v1/scan/analyze", json={"raw_email": BENIGN}, headers=headers)
    b = client.post("/api/v1/scan/analyze", json={"raw_email": PHISH}, headers=headers)
    a_id, b_id = a.headers["X-Scan-Id"], b.headers["X-Scan-Id"]

    resp = client.get(f"/api/v1/scans/compare?a={a_id}&b={b_id}", headers=headers)
    assert resp.status_code == 200
    diff = resp.json()["diff"]
    assert diff["score_delta"] > 0  # benign -> phishing raises the score
    assert diff["band_to"] == "critical"
    assert len(diff["indicators_added"]) >= 1
