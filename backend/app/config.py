from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    database_url: str = Field(..., validation_alias="DATABASE_URL")
    jwt_secret: str = Field(..., validation_alias="JWT_SECRET")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    minio_endpoint: str = Field(..., validation_alias="MINIO_ENDPOINT")
    minio_public_endpoint: str = Field(..., validation_alias="MINIO_PUBLIC_ENDPOINT")
    minio_access_key: str = Field(..., validation_alias="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(..., validation_alias="MINIO_SECRET_KEY")
    minio_bucket: str = Field("lms-files", validation_alias="MINIO_BUCKET")
    minio_secure: bool = Field(False, validation_alias="MINIO_SECURE")
    presigned_url_ttl_seconds: int = 3600
    max_file_size_bytes: int = 50 * 1024 * 1024

    cors_origins: str = Field(
        default="http://localhost:5173",
        validation_alias="CORS_ORIGINS",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]
    debug: bool = Field(False, validation_alias="DEBUG")

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()