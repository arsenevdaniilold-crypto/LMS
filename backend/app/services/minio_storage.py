import io
import uuid
from datetime import timedelta

from minio import Minio
from minio.error import S3Error

from app.config import settings


class MinioStorage:
    def __init__(self) -> None:
        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        self.public_client = Minio(
            settings.minio_public_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
            region="us-east-1",
        )
        self.bucket = settings.minio_bucket

    def ensure_bucket(self) -> None:
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)

    @staticmethod
    def build_key(class_id: uuid.UUID, entity_type: str, original_name: str) -> str:
        ext = ""
        if "." in original_name:
            ext = "." + original_name.rsplit(".", 1)[1].lower()
        return f"{class_id}/{entity_type}/{uuid.uuid4()}{ext}"

    def upload(self, key: str, data: bytes, content_type: str) -> None:
        self.client.put_object(
            self.bucket,
            key,
            io.BytesIO(data),
            length=len(data),
            content_type=content_type,
        )

    def delete(self, key: str) -> None:
        try:
            self.client.remove_object(self.bucket, key)
        except S3Error:
            pass

    def presigned_get_url(self, key: str, download_name: str | None = None) -> str:
        extra: dict[str, str] = {}
        if download_name:
            extra["response-content-disposition"] = f'attachment; filename="{download_name}"'
        return self.public_client.presigned_get_object(
            self.bucket,
            key,
            expires=timedelta(seconds=settings.presigned_url_ttl_seconds),
            response_headers=extra or None,
        )


minio_storage = MinioStorage()
