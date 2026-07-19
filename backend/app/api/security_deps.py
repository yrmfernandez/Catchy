"""Authentication dependencies.

Two flavours:
  * get_current_user — required; 401 on missing/invalid token. Guards history.
  * get_current_user_optional — returns None instead of erroring. Lets the scan
    endpoints work logged-out while still saving for signed-in users.
"""

from __future__ import annotations

import uuid

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.security import decode_access_token
from app.db.models import User
from app.db.repositories import UserRepository
from app.db.session import get_session

_bearer = HTTPBearer(auto_error=False)
_UNAUTHORIZED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid or missing credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def _resolve_user(
    creds: HTTPAuthorizationCredentials | None,
    session: AsyncSession,
    settings: Settings,
) -> User | None:
    if creds is None:
        return None
    try:
        payload = decode_access_token(settings, creds.credentials)
        user_id = uuid.UUID(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None
    return await UserRepository(session).get(user_id)


async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> User:
    user = await _resolve_user(creds, session, settings)
    if user is None:
        raise _UNAUTHORIZED
    return user


async def get_current_user_optional(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> User | None:
    return await _resolve_user(creds, session, settings)
