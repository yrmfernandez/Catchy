"""Smoke tests for the health endpoint and Celery task wiring."""

from fastapi.testclient import TestClient

from app.main import create_app
from app.workers.tasks import ping


def test_health_ok():
    client = TestClient(create_app())
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["service"] == "Catchy"
    assert "version" in body


def test_ping_task_returns_pong():
    # Call the task function directly (no broker needed) to prove it's importable
    # and does what it claims.
    assert ping() == "pong"
