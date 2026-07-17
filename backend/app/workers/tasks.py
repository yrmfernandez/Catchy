"""Celery tasks.

M0 placeholder: a `ping` task that proves the API can enqueue work and a worker can
consume it via Redis. The scan-pipeline tasks replace/join this at M4.
"""

from app.workers.celery_app import celery_app


@celery_app.task(name="catchy.ping")
def ping() -> str:
    """Health task — returns 'pong' so we can verify the broker round-trip."""
    return "pong"
