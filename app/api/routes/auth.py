from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from app.core.limiter import limiter
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.core.security import InvalidTokenError
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserPublic,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    status_code=201,
    responses={
        400: {"description": "Username already exists"},
        429: {"description": "Too many requests"},
    },
)
@limiter.limit("5/minute")
def register(
    request: Request,
    payload: RegisterRequest,
    db: Annotated[Session, Depends(get_db)],
    session_id: Annotated[str | None, Header(alias="X-Session-Id")] = None,
) -> TokenResponse:
    service = AuthService(db)
    try:
        user = service.register_user(
            username=payload.username.strip().lower(),
            password=payload.password,
            full_name=payload.full_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    service.attach_search_history_to_user(session_id, user.id)

    access_token, refresh_token, expires_in = service.issue_tokens(user)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
        user=UserPublic(
            id=user.id,
            username=user.username,
            role=user.role,
            full_name=user.full_name,
            created_at=user.created_at,
        ),
    )


@router.post(
    "/login",
    responses={
        401: {"description": "Invalid credentials"},
        429: {"description": "Too many requests"},
    },
)
@limiter.limit("10/minute")
def login(
    request: Request,
    payload: LoginRequest,
    db: Annotated[Session, Depends(get_db)],
    session_id: Annotated[str | None, Header(alias="X-Session-Id")] = None,
) -> TokenResponse:
    service = AuthService(db)
    user = service.authenticate_user(payload.username.strip().lower(), payload.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    service.attach_search_history_to_user(session_id, user.id)

    access_token, refresh_token, expires_in = service.issue_tokens(user)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
        user=UserPublic(
            id=user.id,
            username=user.username,
            role=user.role,
            full_name=user.full_name,
            created_at=user.created_at,
        ),
    )


@router.get("/me")
def me(current_user: Annotated[User, Depends(get_current_user)]) -> UserPublic:
    return UserPublic(
        id=current_user.id,
        username=current_user.username,
        role=current_user.role,
        full_name=current_user.full_name,
        created_at=current_user.created_at,
    )


@router.post(
    "/refresh",
    responses={
        401: {"description": "Invalid refresh token"},
        429: {"description": "Too many requests"},
    },
)
@limiter.limit("10/minute")
def refresh_token(request: Request, payload: RefreshTokenRequest, db: Annotated[Session, Depends(get_db)]) -> TokenResponse:
    service = AuthService(db)
    try:
        user = service.user_from_refresh_token(payload.refresh_token)
    except InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from exc

    if user is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    access_token, refresh_token_value, expires_in = service.issue_tokens(user)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_value,
        expires_in=expires_in,
        user=UserPublic(
            id=user.id,
            username=user.username,
            role=user.role,
            full_name=user.full_name,
            created_at=user.created_at,
        ),
    )


@router.get("/admin/check")
def admin_check(current_user: Annotated[User, Depends(require_roles("admin"))]) -> dict[str, str]:
    return {"status": "ok", "role": current_user.role}
