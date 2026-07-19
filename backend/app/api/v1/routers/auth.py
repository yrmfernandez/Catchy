"""Auth endpoints: register, login, me."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.security_deps import get_current_user
from app.core.config import Settings, get_settings
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models import User
from app.db.repositories import UserRepository
from app.db.session import get_session
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


def _token_response(settings: Settings, user: User) -> TokenResponse:
    token = create_access_token(settings, str(user.id))
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an account",
)
async def register(
    payload: RegisterRequest,
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    repo = UserRepository(session)
    email = payload.email.lower()
    if await repo.get_by_email(email) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email is already registered."
        )
    user = await repo.create(email, hash_password(payload.password))
    return _token_response(settings, user)


@router.post("/login", response_model=TokenResponse, summary="Log in")
async def login(
    payload: LoginRequest,
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    user = await UserRepository(session).get_by_email(payload.email.lower())
    # Verify even when the user is missing to avoid leaking which emails exist.
    known_hash = user.password_hash if user else "$2b$12$" + "x" * 53
    if not verify_password(payload.password, known_hash) or user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password."
        )
    return _token_response(settings, user)


@router.get("/me", response_model=UserOut, summary="Current user")
async def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(user)
