from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.models.search import SearchHistory
from app.models.user import User


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def get_by_username(self, username: str) -> User | None:
        return self.db.query(User).filter(User.username == username).first()

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()

    def register_user(self, username: str, password: str, full_name: str | None = None) -> User:
        existing = self.get_by_username(username)
        if existing:
            raise ValueError("Username is already registered")

        role = "admin" if self.db.query(User).count() == 0 else "user"

        user = User(
            username=username,
            password_hash=hash_password(password),
            role=role,
            full_name=full_name,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def authenticate_user(self, username: str, password: str) -> User | None:
        user = self.get_by_username(username)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    def issue_tokens(self, user: User) -> tuple[str, str, int]:
        access_token, expires_in = create_access_token(str(user.id))
        refresh_token, _ = create_refresh_token(str(user.id))
        return access_token, refresh_token, expires_in

    def user_from_refresh_token(self, refresh_token: str) -> User | None:
        subject = decode_refresh_token(refresh_token)
        try:
            user_id = int(subject)
        except ValueError:
            return None
        return self.get_by_id(user_id)

    def attach_search_history_to_user(self, session_id: str | None, user_id: int) -> None:
        if not session_id:
            return

        rows = (
            self.db.query(SearchHistory)
            .filter(SearchHistory.session_id == session_id, SearchHistory.user_id.is_(None))
            .all()
        )
        if not rows:
            return

        for row in rows:
            row.user_id = user_id
        self.db.commit()
