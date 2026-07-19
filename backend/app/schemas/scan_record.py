"""Schemas for stored scans (history + compare)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.scan import ScanResult


class ScanSummary(BaseModel):
    """Lightweight row for the history list."""

    id: uuid.UUID
    created_at: datetime
    score: int
    band: str
    method: str
    subject: str | None = None
    sender_domain: str | None = None

    model_config = {"from_attributes": True}


class ScanRecord(BaseModel):
    """A stored scan with its full result."""

    id: uuid.UUID
    created_at: datetime
    result: ScanResult

    model_config = {"from_attributes": True}


class ScanDiff(BaseModel):
    score_delta: int
    band_from: str
    band_to: str
    indicators_added: list[str]
    indicators_removed: list[str]


class CompareResult(BaseModel):
    a: ScanRecord
    b: ScanRecord
    diff: ScanDiff
