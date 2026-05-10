import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


def _resolve_database_url(raw_url: str) -> str:
    """Normalize database URL values for SQLAlchemy."""
    if raw_url.startswith("postgres://"):
        # SQLAlchemy expects the postgresql scheme.
        return "postgresql+psycopg2://" + raw_url[len("postgres://") :]

    return raw_url

settings = get_settings()
database_url = _resolve_database_url(settings.database_url)
connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
engine = create_engine(database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
