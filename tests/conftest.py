from pathlib import Path
import sys
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True, scope="session")
def disable_rate_limiting():
    """Patch slowapi at the class level so no rate limit fires during tests.

    _enabled=False is version-sensitive; patching _check_request_limit on the
    class is version-agnostic and affects every Limiter instance immediately.
    """
    with patch("slowapi.extension.Limiter._check_request_limit"):
        yield


@pytest.fixture(autouse=True, scope="session")
def pre_create_test_user(disable_rate_limiting):
    """Create the shared test-user directly in the DB before any test runs.

    test_search.py calls _auth_headers() which tries login first and only
    falls back to /register if login fails.  By pre-creating the user here
    the first login succeeds and /register is never called, so the 5/minute
    rate limit on that endpoint is never relevant.
    """
    from app.core.database import SessionLocal
    from app.services.auth_service import AuthService

    db = SessionLocal()
    try:
        svc = AuthService(db)
        try:
            svc.register_user("test-user", "test-pass-123")
        except Exception:
            pass  # already exists — that's fine
    finally:
        db.close()

