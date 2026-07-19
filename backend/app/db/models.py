"""ORM models.

A pragmatic, hybrid shape: `Scan` keeps the columns we actually query on
(owner, time, score, band, sender, subject) indexed and denormalized, plus a JSON
`result` holding the full ScanResult for detail views. This keeps history/compare
queries cheap without exploding the whole ScanResult into a dozen tables — the
normalized breakdown lives inside the JSON and can be promoted later if needed.

`Scan.user_id` is nullable: per the product decision, scanning works logged-out
(those runs simply aren't persisted), while a signed-in user's scans are saved.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _now() -> datetime:
    return datetime.now(UTC)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    scans: Mapped[list[Scan]] = relationship(back_populates="user")


class Scan(Base):
    __tablename__ = "scans"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, index=True
    )

    # Denormalized, queryable summary columns.
    score: Mapped[int] = mapped_column(index=True)
    band: Mapped[str] = mapped_column(String(16), index=True)
    method: Mapped[str] = mapped_column(String(16))
    subject: Mapped[str | None] = mapped_column(String(512), nullable=True)
    sender_domain: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    # Full ScanResult for the detail view.
    result: Mapped[dict] = mapped_column(JSON)

    user: Mapped[User | None] = relationship(back_populates="scans")
