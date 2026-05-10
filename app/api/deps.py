from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import InvalidTokenError, decode_access_token
from app.models.user import User
from app.services.auth_service import AuthService

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
) -> User:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing authorization token")

    token = credentials.credentials
    try:
        subject = decode_access_token(token)
        user_id = int(subject)
    except (InvalidTokenError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    service = AuthService(db)
    user = service.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user


def get_optional_current_user(
    db: Annotated[Session, Depends(get_db)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
) -> User | None:
    if credentials is None:
        return None

    token = credentials.credentials
    try:
        subject = decode_access_token(token)
        user_id = int(subject)
    except (InvalidTokenError, ValueError):
        return None

    service = AuthService(db)
    return service.get_by_id(user_id)


def require_roles(*roles: str):
    allowed_roles = {role.strip().lower() for role in roles if role.strip()}

    def _require_role(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if current_user.role.lower() not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user

    return _require_role
