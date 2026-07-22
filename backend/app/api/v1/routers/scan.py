"""Scan endpoints — M1 exposes the parsing stage.

Two ways in, one service: paste raw text (JSON) or upload an .eml file
(multipart). Both return the same `ParsedEmail`. Later milestones add the
feature/ML/LLM stages behind a fuller `POST /scan` that persists a result; for
now these `/scan/parse*` routes let the parser be exercised and demoed on its
own.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_email_parser, get_scan_service
from app.api.security_deps import get_current_user_optional
from app.core.config import Settings, get_settings
from app.core.ratelimit import scan_rate_limiter
from app.db.models import User
from app.db.repositories import ScanRepository
from app.db.session import get_session
from app.schemas.email import ParsedEmail
from app.schemas.scan import ScanResult
from app.services.analysis import ScanService
from app.services.parsing import EmailParserService

logger = logging.getLogger("catchy.scan")
# Scanning runs the full (potentially LLM-backed) pipeline, so rate-limit it.
router = APIRouter(prefix="/scan", tags=["scan"], dependencies=[Depends(scan_rate_limiter)])


async def _maybe_save(
    result: ScanResult, user: User | None, session: AsyncSession, response: Response
) -> None:
    """Persist the scan for signed-in users. Best-effort: a DB hiccup must not
    fail the scan itself — the caller already has their result."""
    if user is None:
        return
    try:
        scan = await ScanRepository(session).create(user.id, result)
        response.headers["X-Scan-Id"] = str(scan.id)
    except Exception:  # noqa: BLE001
        logger.exception("failed to persist scan for user %s", user.id)


class ParseRequest(BaseModel):
    raw_email: str = Field(
        min_length=1,
        description="Raw RFC 5322 message (headers + body), as pasted by the user.",
    )


def _guard_size(size: int, settings: Settings) -> None:
    if size > settings.max_email_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"Email exceeds the {settings.max_email_bytes} byte limit.",
        )


@router.post("/parse", response_model=ParsedEmail, summary="Parse a pasted email")
def parse_pasted(
    payload: ParseRequest,
    parser: EmailParserService = Depends(get_email_parser),
    settings: Settings = Depends(get_settings),
) -> ParsedEmail:
    _guard_size(len(payload.raw_email.encode("utf-8", "replace")), settings)
    return parser.parse(payload.raw_email)


@router.post("/parse/file", response_model=ParsedEmail, summary="Parse an uploaded .eml")
async def parse_uploaded(
    file: UploadFile = File(..., description="An .eml / RFC 5322 message file"),
    parser: EmailParserService = Depends(get_email_parser),
    settings: Settings = Depends(get_settings),
) -> ParsedEmail:
    raw = await file.read()
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty."
        )
    _guard_size(len(raw), settings)
    return parser.parse(raw)


@router.post("/analyze", response_model=ScanResult, summary="Analyze a pasted email")
async def analyze_pasted(
    payload: ParseRequest,
    response: Response,
    service: ScanService = Depends(get_scan_service),
    settings: Settings = Depends(get_settings),
    user: User | None = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_session),
) -> ScanResult:
    _guard_size(len(payload.raw_email.encode("utf-8", "replace")), settings)
    result = await service.analyze_async(payload.raw_email)
    await _maybe_save(result, user, session, response)
    return result


@router.post("/analyze/file", response_model=ScanResult, summary="Analyze an uploaded .eml")
async def analyze_uploaded(
    response: Response,
    file: UploadFile = File(..., description="An .eml / RFC 5322 message file"),
    service: ScanService = Depends(get_scan_service),
    settings: Settings = Depends(get_settings),
    user: User | None = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_session),
) -> ScanResult:
    raw = await file.read()
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty."
        )
    _guard_size(len(raw), settings)
    result = await service.analyze_async(raw)
    await _maybe_save(result, user, session, response)
    return result
