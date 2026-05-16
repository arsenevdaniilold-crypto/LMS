import hashlib
import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User, RefreshToken
from app.utils.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.config import settings


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def register_user(
    db: AsyncSession, email: str, password: str, username: str
) -> tuple[User, str, str] | tuple[None, None, None]:
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        return None, None, None

    user = User(
        email=email,
        password_hash=hash_password(password),
        username=username,
    )
    db.add(user)
    await db.flush()

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    db.add(RefreshToken(
        user_id=user.id,
        token_hash=_hash_token(refresh_token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days),
    ))
    await db.commit()
    await db.refresh(user)
    return user, access_token, refresh_token


async def login_user(
    db: AsyncSession, email: str, password: str
) -> tuple[User, str, str] | tuple[None, None, None]:
    result = await db.execute(
        select(User).where(User.email == email, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.password_hash):
        return None, None, None

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    db.add(RefreshToken(
        user_id=user.id,
        token_hash=_hash_token(refresh_token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days),
    ))
    await db.commit()
    return user, access_token, refresh_token


async def logout_user(db: AsyncSession, refresh_token: str) -> None:
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == _hash_token(refresh_token))
    )
    rt = result.scalar_one_or_none()
    if rt:
        await db.delete(rt)
        await db.commit()


async def refresh_tokens(
    db: AsyncSession, refresh_token: str
) -> tuple[str, str] | tuple[None, None]:
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == _hash_token(refresh_token))
    )
    rt = result.scalar_one_or_none()
    if not rt:
        return None, None

    if rt.expires_at < datetime.now(timezone.utc):
        await db.delete(rt)
        await db.commit()
        return None, None

    await db.delete(rt)

    new_access = create_access_token(str(rt.user_id))
    new_refresh = create_refresh_token(str(rt.user_id))

    db.add(RefreshToken(
        user_id=rt.user_id,
        token_hash=_hash_token(new_refresh),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days),
    ))
    await db.commit()
    return new_access, new_refresh
