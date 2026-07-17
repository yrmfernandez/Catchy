"""Celery application.

The scan pipeline (parse → features → enrich → ML → LLM → fuse) runs here, off the
HTTP request path, so the API can accept a scan and return immediately. Redis is
both broker and result backend. M0 ships only a `ping` task to prove the wiring;
real tasks land at M4.
"""

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "phishguard",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)
