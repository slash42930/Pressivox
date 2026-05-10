"""Best-effort startup schema patch helpers for local/dev databases."""

import logging

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


def ensure_search_history_columns(engine: Engine) -> None:
    """Add search_history columns for existing databases if missing."""
    try:
        inspector = inspect(engine)
        if "search_history" not in inspector.get_table_names():
            return

        columns = {column["name"] for column in inspector.get_columns("search_history")}
        column_patches = {
            "user_id": "ALTER TABLE search_history ADD COLUMN user_id INTEGER",
            "session_id": "ALTER TABLE search_history ADD COLUMN session_id VARCHAR(128)",
            "ambiguous": "ALTER TABLE search_history ADD COLUMN ambiguous BOOLEAN DEFAULT 0",
            "selected_source_count": "ALTER TABLE search_history ADD COLUMN selected_source_count INTEGER DEFAULT 0",
            "meaning_group_count": "ALTER TABLE search_history ADD COLUMN meaning_group_count INTEGER DEFAULT 0",
            "has_summary": "ALTER TABLE search_history ADD COLUMN has_summary BOOLEAN DEFAULT 0",
        }

        missing = [statement for name, statement in column_patches.items() if name not in columns]
        if not missing:
            return

        with engine.begin() as connection:
            for statement in missing:
                connection.execute(text(statement))
    except Exception:
        # Non-fatal schema upgrade path for local dev databases.
        logger.exception("Best-effort schema patch failed for search_history.")


def ensure_user_columns(engine: Engine) -> None:
    """Add users table columns for existing databases if missing."""
    try:
        inspector = inspect(engine)
        if "users" not in inspector.get_table_names():
            return

        columns = {column["name"] for column in inspector.get_columns("users")}
        missing: list[str] = []
        if "role" not in columns:
            missing.append("ALTER TABLE users ADD COLUMN role VARCHAR(32) DEFAULT 'user'")

        with engine.begin() as connection:
            for statement in missing:
                connection.execute(text(statement))
            connection.execute(text("UPDATE users SET role='user' WHERE role IS NULL"))
            connection.execute(
                text(
                    "UPDATE users SET role='admin' "
                    "WHERE id=(SELECT MIN(id) FROM users) AND role='user'"
                )
            )
    except Exception:
        logger.exception("Best-effort schema patch failed for users.")


def ensure_extracted_document_columns(engine: Engine) -> None:
    """Add extracted_documents columns for existing databases if missing."""
    try:
        inspector = inspect(engine)
        if "extracted_documents" not in inspector.get_table_names():
            return

        columns = {column["name"] for column in inspector.get_columns("extracted_documents")}
        missing: list[str] = []
        if "user_id" not in columns:
            missing.append("ALTER TABLE extracted_documents ADD COLUMN user_id INTEGER")

        if not missing:
            return

        with engine.begin() as connection:
            for statement in missing:
                connection.execute(text(statement))
    except Exception:
        logger.exception("Best-effort schema patch failed for extracted_documents.")


def backfill_history_user_ids(engine: Engine) -> None:
    """Associate legacy history rows to the first user if exactly one user exists."""
    try:
        with engine.begin() as connection:
            user_count = connection.execute(text("SELECT COUNT(*) FROM users")).scalar()
            if user_count != 1:
                return

            first_user_id = connection.execute(text("SELECT MIN(id) FROM users")).scalar()
            if first_user_id is None:
                return

            connection.execute(
                text("UPDATE search_history SET user_id=:uid WHERE user_id IS NULL"),
                {"uid": first_user_id},
            )
            connection.execute(
                text("UPDATE extracted_documents SET user_id=:uid WHERE user_id IS NULL"),
                {"uid": first_user_id},
            )
    except Exception:
        logger.exception("Best-effort user_id backfill failed.")


def run_startup_schema_patches(engine: Engine) -> None:
    """Run all best-effort startup schema patch routines."""
    ensure_search_history_columns(engine)
    ensure_user_columns(engine)
    ensure_extracted_document_columns(engine)
    backfill_history_user_ids(engine)
