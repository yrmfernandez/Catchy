"""Scan endpoints — M1 exposes the parsing stage.

Two ways in, one service: paste raw text (JSON) or upload an .eml file
(multipart). Both return the same `ParsedEmail`. Later milestones add the
feature/ML/LLM stages behind a fuller `POST /scan` that persists a result; for
now these `/scan/parse*` routes let the parser be exercised and demoed on its
own.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from app.api.deps import get_email_parser, get_scan_service
from app.core.config import Settings, get_settings
from app.schemas.email import ParsedEmail
from app.schemas.scan import ScanResult
from app.services.analysis import ScanService
from app.services.parsing import EmailParserService

router = APIRouter(prefix="/scan", tags=["scan"])


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
    service: ScanService = Depends(get_scan_service),
    settings: Settings = Depends(get_settings),
) -> ScanResult:
    _guard_size(len(payload.raw_email.encode("utf-8", "replace")), settings)
    return await service.analyze_async(payload.raw_email)


@router.post("/analyze/file", response_model=ScanResult, summary="Analyze an uploaded .eml")
async def analyze_uploaded(
    file: UploadFile = File(..., description="An .eml / RFC 5322 message file"),
    service: ScanService = Depends(get_scan_service),
    settings: Settings = Depends(get_settings),
) -> ScanResult:
    raw = await file.read()
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty."
        )
    _guard_size(len(raw), settings)
    return await service.analyze_async(raw)
