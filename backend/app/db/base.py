"""Declarative base for all ORM models.

A single Base whose metadata Alembic autogenerates migrations from. Models import
this and are imported by app.db.models so `Base.metadata` sees every table.
"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
