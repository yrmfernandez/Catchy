"""Scan history endpoints (auth required): list, detail, compare.

Every route is scoped to the current user — a user can only ever see their own
scans (the repository filters by user_id, so there is no way to read another
user's scan even by guessing its id).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.security_deps import get_current_user
from app.db.models import Scan, User
from app.db.repositories import ScanRepository
from app.db.session import get_session
from app.schemas.scan_record import CompareResult, ScanDiff, ScanRecord, ScanSummary

router = APIRouter(prefix="/scans", tags=["history"])


@router.get("", response_model=list[ScanSummary], summary="List your scans")
async def list_scans(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[ScanSummary]:
    scans = await ScanRepository(session).list_for_user(user.id, limit=limit, offset=offset)
    return [ScanSummary.model_validate(s) for s in scans]


async def _load(scan_id: uuid.UUID, user: User, session: AsyncSession) -> Scan:
    scan = await ScanRepository(session).get_for_user(scan_id, user.id)
    if scan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found.")
    return scan


@router.get("/compare", response_model=CompareResult, summary="Compare two of your scans")
async def compare_scans(
    a: uuid.UUID,
    b: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> CompareResult:
    scan_a = await _load(a, user, session)
    scan_b = await _load(b, user, session)

    ind_a = {i["id"] for i in scan_a.result["assessment"]["indicators"]}
    ind_b = {i["id"] for i in scan_b.result["assessment"]["indicators"]}
    diff = ScanDiff(
        score_delta=scan_b.score - scan_a.score,
        band_from=scan_a.band,
        band_to=scan_b.band,
        indicators_added=sorted(ind_b - ind_a),
        indicators_removed=sorted(ind_a - ind_b),
    )
    return CompareResult(
        a=ScanRecord.model_validate(scan_a),
        b=ScanRecord.model_validate(scan_b),
        diff=diff,
    )


@router.get("/{scan_id}", response_model=ScanRecord, summary="Get one scan")
async def get_scan(
    scan_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ScanRecord:
    return ScanRecord.model_validate(await _load(scan_id, user, session))
