from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True, scope="session")
def disable_rate_limiting():
    """Disable slowapi rate limiting for the entire test session.

    test_auth.py alone makes 5 calls to /auth/register, exhausting the
    5/minute limit before test_search.py can register its test user.
    Rate limiting is an operational concern; correctness tests should not
    depend on or be broken by it.
    """
    from app.api.routes.auth import limiter as auth_limiter
    from app.main import limiter as main_limiter

    auth_limiter._enabled = False
    main_limiter._enabled = False
    yield
    auth_limiter._enabled = True
    main_limiter._enabled = True
