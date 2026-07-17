"""Health & readiness endpoints.

Routers stay thin: they validate/shape HTTP concerns and delegate. `/health` is a
cheap liveness probe (used by Docker and CI); `/health/ready` will grow into a
readiness check that pings Postgres and Redis in a later milestone.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app import __version__
from app.core.config import Settings, get_settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    environment: str


@router.get("/health", response_model=HealthResponse, summary="Liveness probe")
def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.project_name,
        version=__version__,
        environment=settings.environment,
    )
