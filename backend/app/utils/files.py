from fastapi import HTTPException, UploadFile, status

from app.config import settings


ALLOWED_CONTENT_EXTENSIONS = {".docx", ".pptx", ".jpg", ".jpeg", ".png"}
ALLOWED_SOLUTION_EXTENSIONS = ALLOWED_CONTENT_EXTENSIONS | {".xlsx"}

ALLOWED_CONTENT_TYPES = {
    ".docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/octet-stream"},
    ".pptx": {"application/vnd.openxmlformats-officedocument.presentationml.presentation", "application/octet-stream"},
    ".xlsx": {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/octet-stream"},
    ".jpg": {"image/jpeg"},
    ".jpeg": {"image/jpeg"},
    ".png": {"image/png"},
}


def _extension(filename: str) -> str:
    if "." not in filename:
        return ""
    return "." + filename.rsplit(".", 1)[1].lower()


def validate_upload(file: UploadFile, size: int, *, allow_xlsx: bool = False) -> None:
    if size > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={"code": "FILE_TOO_LARGE", "message": f"File exceeds {settings.max_file_size_bytes // 1024 // 1024} MB limit"},
        )

    allowed = ALLOWED_SOLUTION_EXTENSIONS if allow_xlsx else ALLOWED_CONTENT_EXTENSIONS
    ext = _extension(file.filename or "")
    if ext not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "UNSUPPORTED_FILE_TYPE", "message": f"Extension '{ext}' is not allowed"},
        )

    expected_types = ALLOWED_CONTENT_TYPES.get(ext, set())
    if file.content_type and expected_types and file.content_type not in expected_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "CONTENT_TYPE_MISMATCH",
                "message": f"Content-type '{file.content_type}' does not match extension '{ext}'",
            },
        )
