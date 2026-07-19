# syntax=docker/dockerfile:1
# ------------------------------------------------------------------
# Catchy backend image.
# Security posture (see docs/architecture.md §Security): slim base,
# pinned Python, non-root runtime user, deps installed as a cached layer.
# The same image serves both the API and the Celery worker — the compose
# file just overrides the command.
# ------------------------------------------------------------------
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Copy metadata + code, then install the project (runtime deps only).
COPY pyproject.toml ./
COPY app ./app
# Alembic config + migrations, so the container can run `alembic upgrade head`.
COPY alembic.ini ./
COPY migrations ./migrations
RUN pip install --upgrade pip && pip install .

# Run as a non-root user.
RUN useradd --create-home --uid 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
