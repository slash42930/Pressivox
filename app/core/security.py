from datetime import UTC, datetime, timedelta
import base64
import hashlib
import hmac
import secrets

from jose import JWTError, jwt

from app.core.config import get_settings


class InvalidTokenError(Exception):
    pass


def hash_password(password: str) -> str:
    iterations = 200_000
    salt = secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    salt_b64 = base64.urlsafe_b64encode(salt).decode("utf-8")
    hash_b64 = base64.urlsafe_b64encode(derived).decode("utf-8")
    return f"pbkdf2_sha256${iterations}${salt_b64}${hash_b64}"


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations_raw, salt_b64, expected_b64 = password_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(iterations_raw)
        salt = base64.urlsafe_b64decode(salt_b64.encode("utf-8"))
        expected = base64.urlsafe_b64decode(expected_b64.encode("utf-8"))
    except Exception:
        return False

    actual = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(actual, expected)


def _create_token(subject: str, token_type: str, expires_in: int) -> tuple[str, int]:
    settings = get_settings()
    expire = datetime.now(UTC) + timedelta(seconds=expires_in)
    payload = {"sub": subject, "type": token_type, "exp": expire}
    token = jwt.encode(payload, settings.auth_secret_key, algorithm=settings.auth_algorithm)
    return token, expires_in


def create_access_token(subject: str) -> tuple[str, int]:
    settings = get_settings()
    expires_in = settings.auth_access_token_expire_minutes * 60
    return _create_token(subject, token_type="access", expires_in=expires_in)


def create_refresh_token(subject: str) -> tuple[str, int]:
    settings = get_settings()
    expires_in = settings.auth_refresh_token_expire_days * 24 * 60 * 60
    return _create_token(subject, token_type="refresh", expires_in=expires_in)


def _decode_token(token: str, expected_type: str) -> str:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.auth_secret_key, algorithms=[settings.auth_algorithm])
        subject = payload.get("sub")
        token_type = payload.get("type", "access")
        if token_type != expected_type:
            raise InvalidTokenError("Unexpected token type")
        if not isinstance(subject, str) or not subject:
            raise InvalidTokenError("Invalid token subject")
        return subject
    except JWTError as exc:
        raise InvalidTokenError("Invalid or expired token") from exc


def decode_access_token(token: str) -> str:
    return _decode_token(token, expected_type="access")


def decode_refresh_token(token: str) -> str:
    return _decode_token(token, expected_type="refresh")
