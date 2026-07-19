"""Repositories: the only place that talks to the ORM.

Services and routers depend on these, not on SQLAlchemy directly (repository
pattern), which keeps persistence swappable and the query surface in one place.
Each repository is constructed with a request-scoped AsyncSession.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Scan, User
from app.schemas.scan import ScanResult


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, user_id: uuid.UUID) -> User | None:
        return await self._session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create(self, email: str, password_hash: str) -> User:
        user = User(email=email, password_hash=password_hash)
        self._session.add(user)
        await self._session.commit()
        await self._session.refresh(user)
        return user


class ScanRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, user_id: uuid.UUID, result: ScanResult) -> Scan:
        sender = result.parsed.from_address
        scan = Scan(
            user_id=user_id,
            score=result.fusion.score,
            band=str(result.fusion.band),
            method=result.fusion.method,
            subject=(result.parsed.subject or None),
            sender_domain=(sender.domain if sender else None),
            result=result.model_dump(mode="json"),
        )
        self._session.add(scan)
        await self._session.commit()
        await self._session.refresh(scan)
        return scan

    async def list_for_user(
        self, user_id: uuid.UUID, *, limit: int = 50, offset: int = 0
    ) -> list[Scan]:
        result = await self._session.execute(
            select(Scan)
            .where(Scan.user_id == user_id)
            .order_by(Scan.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_for_user(self, scan_id: uuid.UUID, user_id: uuid.UUID) -> Scan | None:
        result = await self._session.execute(
            select(Scan).where(Scan.id == scan_id, Scan.user_id == user_id)
        )
        return result.scalar_one_or_none()
