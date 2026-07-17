"""Aggregate router for API v1.

Each feature area gets its own router module; they are mounted here so `main.py`
only ever includes one thing. Scan, auth, history, analytics, etc. routers plug
in at their milestones.
"""

from fastapi import APIRouter

from app.api.v1.routers import health

api_router = APIRouter()
api_router.include_router(health.router)
