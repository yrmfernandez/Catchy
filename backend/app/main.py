"""FastAPI application entrypoint.

Thin composition root: configure logging, build the app, wire middleware and the
v1 router. Business logic lives in services (added from M1 onward), never here.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.middleware import SecurityHeadersMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.project_name,
        version=__version__,
        summary="Explainable phishing detection: forensics + ML + LLM analyst.",
        lifespan=lifespan,
    )

    is_dev = settings.environment == "development"

    # Security headers on every response (HSTS only under TLS, i.e. not in dev).
    app.add_middleware(SecurityHeadersMiddleware, hsts=not is_dev)

    # CORS: local frontend origins in dev; the configured origin(s) in prod. When
    # nothing is configured in prod, only same-origin requests are allowed (the
    # intended setup behind the Vercel rewrite). X-Scan-Id is exposed so the
    # browser can read the saved-scan id from a cross-origin response.
    origins = (
        ["http://localhost:3000", "http://127.0.0.1:3000"]
        if is_dev
        else settings.cors_origin_list
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Scan-Id"],
    )

    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
