from fastapi import APIRouter, Depends, HTTPException, Request, Response, Cookie, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.user import RegisterRequest, LoginRequest, UserResponse, user_to_response
from app.services import auth as auth_service
from app.limiter import limiter
from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _set_tokens(response: Response, access_token: str, refresh_token: str) -> None:
    response.set_cookie(
        "access_token", access_token,
        httponly=True, samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
    )
    response.set_cookie(
        "refresh_token", refresh_token,
        httponly=True, samesite="lax",
        path="/api/auth",
        max_age=settings.refresh_token_expire_days * 24 * 3600,
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(
    request: Request,
    response: Response,
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    user, access_token, refresh_token = await auth_service.register_user(
        db, body.email, body.password, body.username
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "EMAIL_TAKEN", "message": "Email already registered"},
        )
    _set_tokens(response, access_token, refresh_token)
    return user_to_response(user)


@router.post("/login", response_model=UserResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    response: Response,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    user, access_token, refresh_token = await auth_service.login_user(
        db, body.email, body.password
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_CREDENTIALS", "message": "Invalid email or password"},
        )
    _set_tokens(response, access_token, refresh_token)
    return user_to_response(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
):
    if refresh_token:
        await auth_service.logout_user(db, refresh_token)
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token", path="/api/auth")


@router.post("/refresh")
async def refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
):
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "NO_REFRESH_TOKEN", "message": "Refresh token missing"},
        )
    new_access, new_refresh = await auth_service.refresh_tokens(db, refresh_token)
    if new_access is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_REFRESH_TOKEN", "message": "Refresh token invalid or expired"},
        )
    _set_tokens(response, new_access, new_refresh)
    return {"ok": True}
