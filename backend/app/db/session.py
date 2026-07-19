"""Async engine and session factory.

The app talks to Postgres asynchronously (psycopg3 async under
`postgresql+psycopg://`). `get_session` is the FastAPI dependency handing each
request its own AsyncSession; tests override it with an in-memory SQLite engine,
so the suite needs no database. Alembic uses a *sync* engine (see migrations/),
which is why the model types stay dialect-neutral.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

_settings = get_settings()

engine = create_async_engine(_settings.database_url, pool_pre_ping=True, future=True)
SessionFactory = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionFactory() as session:
        yield session
