"""Test database wiring.

Overrides the app's `get_session` with a file-backed SQLite engine (NullPool, so
connections aren't reused across the TestClient's event loops) and creates the
schema from the ORM metadata. The whole suite therefore runs with no Postgres —
identical models, dialect-neutral column types.
"""

from __future__ import annotations

import asyncio
import atexit
import os
import tempfile
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.db import models  # noqa: F401 - register tables on the metadata
from app.db.base import Base
from app.db.session import get_session
from app.main import app

_DB_PATH = os.path.join(tempfile.gettempdir(), "catchy_test.db")
if os.path.exists(_DB_PATH):
    try:
        os.remove(_DB_PATH)
    except OSError:
        pass

_URL = "sqlite+aiosqlite:///" + _DB_PATH.replace("\\", "/")
_engine = create_async_engine(_URL, poolclass=NullPool)
_Session = async_sessionmaker(_engine, expire_on_commit=False)


async def _init_models() -> None:
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


asyncio.run(_init_models())


async def _override_get_session() -> AsyncIterator[AsyncSession]:
    async with _Session() as session:
        yield session


app.dependency_overrides[get_session] = _override_get_session


@atexit.register
def _cleanup() -> None:
    try:
        os.remove(_DB_PATH)
    except OSError:
        pass
