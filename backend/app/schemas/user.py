import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    username: str

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    @field_validator("username")
    @classmethod
    def username_length(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2 or len(v) > 100:
            raise ValueError("Username must be 2-100 characters")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    username: str
    avatar_url: str | None
    is_admin: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdateRequest(BaseModel):
    username: str | None = None
    avatar_url: str | None = None

    @field_validator("username")
    @classmethod
    def username_length(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if len(v) < 2 or len(v) > 100:
            raise ValueError("Username must be 2-100 characters")
        return v


def user_to_response(user) -> "UserResponse":
    """
    Serialize User model to UserResponse.
    If avatar_url is a MinIO key (does not start with http), resolve it to a fresh presigned URL.
    External URLs (http://, https://) are returned as-is.
    """
    from app.services.minio_storage import minio_storage  # local import to avoid cycle

    avatar = user.avatar_url
    if avatar and not avatar.startswith("http"):
        try:
            avatar = minio_storage.presigned_get_url(avatar)
        except Exception:
            avatar = None
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        avatar_url=avatar,
        is_admin=user.is_admin,
        created_at=user.created_at,
    )
