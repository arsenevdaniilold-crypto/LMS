"""Pure unit tests for security/files/invite helpers — no DB, no app."""
import pytest
from fastapi import HTTPException, UploadFile

from app.utils.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.utils.invite import (
    INVITE_ALPHABET,
    INVITE_CODE_LENGTH,
    generate_invite_code,
)
from app.utils.files import validate_upload


class TestPasswordHashing:
    def test_hash_is_not_plaintext_and_verifies(self):
        hashed = hash_password("s3cret-password")
        assert hashed != "s3cret-password"
        assert verify_password("s3cret-password", hashed) is True

    def test_wrong_password_does_not_verify(self):
        hashed = hash_password("correct horse")
        assert verify_password("battery staple", hashed) is False

    def test_same_password_gets_distinct_salts(self):
        assert hash_password("abc12345") != hash_password("abc12345")


class TestJwt:
    def test_access_token_roundtrip(self):
        token = create_access_token("user-123")
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == "user-123"
        assert payload["type"] == "access"

    def test_refresh_token_roundtrip(self):
        token = create_refresh_token("user-456")
        payload = decode_refresh_token(token)
        assert payload is not None
        assert payload["sub"] == "user-456"
        assert payload["type"] == "refresh"

    def test_access_decoder_rejects_refresh_token(self):
        # type confusion must be caught: a refresh token is not a valid access token
        refresh = create_refresh_token("user-789")
        assert decode_access_token(refresh) is None

    def test_refresh_decoder_rejects_access_token(self):
        access = create_access_token("user-789")
        assert decode_refresh_token(access) is None

    def test_garbage_token_returns_none(self):
        assert decode_access_token("not-a-jwt") is None
        assert decode_refresh_token("") is None


class TestInviteCode:
    def test_length_and_alphabet(self):
        for _ in range(50):
            code = generate_invite_code()
            assert len(code) == INVITE_CODE_LENGTH
            assert all(ch in INVITE_ALPHABET for ch in code)

    def test_excludes_ambiguous_characters(self):
        # 0/O/1/I/L are intentionally excluded to avoid confusion
        for forbidden in ("0", "O", "1", "I", "L"):
            assert forbidden not in INVITE_ALPHABET


def _upload(filename: str, content_type: str | None) -> UploadFile:
    import io

    return UploadFile(file=io.BytesIO(b""), filename=filename, headers=_headers(content_type))


def _headers(content_type: str | None):
    from starlette.datastructures import Headers

    if content_type is None:
        return Headers({})
    return Headers({"content-type": content_type})


class TestValidateUpload:
    def test_accepts_docx(self):
        validate_upload(
            _upload("report.docx",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
            size=1024,
        )

    def test_rejects_unsupported_extension(self):
        with pytest.raises(HTTPException) as exc:
            validate_upload(_upload("malware.exe", "application/octet-stream"), size=10)
        assert exc.value.detail["code"] == "UNSUPPORTED_FILE_TYPE"

    def test_rejects_too_large(self):
        with pytest.raises(HTTPException) as exc:
            validate_upload(_upload("big.png", "image/png"), size=51 * 1024 * 1024)
        assert exc.value.detail["code"] == "FILE_TOO_LARGE"

    def test_xlsx_only_allowed_for_solutions(self):
        # not allowed as content material
        with pytest.raises(HTTPException) as exc:
            validate_upload(
                _upload("grades.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
                size=100,
                allow_xlsx=False,
            )
        assert exc.value.detail["code"] == "UNSUPPORTED_FILE_TYPE"
        # allowed for solution uploads
        validate_upload(
            _upload("grades.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            size=100,
            allow_xlsx=True,
        )

    def test_content_type_mismatch(self):
        with pytest.raises(HTTPException) as exc:
            validate_upload(_upload("photo.png", "image/gif"), size=100)
        assert exc.value.detail["code"] == "CONTENT_TYPE_MISMATCH"
