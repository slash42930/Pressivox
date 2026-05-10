import pytest

from app.core.config import Settings


def test_cors_origins_list_from_csv() -> None:
    settings = Settings(cors_allow_origins="https://a.example, https://b.example")

    assert settings.cors_origins_list == ["https://a.example", "https://b.example"]


def test_cors_origins_list_defaults_to_wildcard_when_empty() -> None:
    settings = Settings(cors_allow_origins="")

    assert settings.cors_origins_list == ["*"]


def test_validate_security_rejects_sqlite_on_vercel(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VERCEL", "1")
    settings = Settings(database_url="sqlite:///./web_search.db")

    with pytest.raises(RuntimeError, match="persistent database"):
        settings.validate_security()
