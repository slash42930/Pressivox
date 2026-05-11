import asyncio
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)

# Module-level cache so register+login only happens once per test session,
# preventing the 5/minute rate limit on /auth/register from tripping.
_cached_auth_headers: dict[str, str] | None = None


def _auth_headers() -> dict[str, str]:
    global _cached_auth_headers
    if _cached_auth_headers is not None:
        return _cached_auth_headers

    credentials = {
        "username": "test-user",
        "password": "test-pass-123",
    }

    login = client.post("/api/v1/auth/login", json=credentials)
    if login.status_code != 200:
        client.post("/api/v1/auth/register", json=credentials)
        login = client.post("/api/v1/auth/login", json=credentials)

    assert login.status_code == 200
    token = login.json()["access_token"]
    _cached_auth_headers = {
        "Authorization": f"Bearer {token}",
        "X-Session-Id": "test-session",
    }
    return _cached_auth_headers


def test_search_endpoint_returns_rich_ui_metadata(monkeypatch) -> None:
    async def fake_run_search(self, request, session_id=None, user_id=None):
        await asyncio.sleep(0)
        return {
            "query": request.query,
            "topic": request.topic,
            "provider": "stub-provider",
            "results": [
                {
                    "title": "Mercury overview",
                    "url": "https://example.com/mercury",
                    "snippet": "Mercury can refer to multiple concepts.",
                    "source": "example.com",
                    "rerank_score": 0.91,
                }
            ],
            "summary": "A short search summary.",
            "extracted_summary": None,
            "extraction_attempted": False,
            "extracted_count": 0,
            "answer": "A short search summary.",
            "response_time": 0.42,
            "request_id": "req-search-123",
            "auto_parameters": {"topic": request.topic},
            "usage": {"credits": 1},
            "selected_sources": [
                {
                    "meaning": "planet",
                    "title": "Mercury the planet",
                    "url": "https://example.com/planet",
                    "source": "example.com",
                    "rerank_score": 0.97,
                }
            ],
            "ambiguous": True,
            "meaning_groups": [
                {
                    "meaning": "planet",
                    "results": [
                        {
                            "title": "Mercury the planet",
                            "url": "https://example.com/planet",
                            "snippet": "A planet in the solar system.",
                            "source": "example.com",
                        }
                    ],
                }
            ],
        }

    monkeypatch.setattr("app.api.routes.search.SearchService.run_search", fake_run_search)

    response = client.post(
        "/api/v1/search",
        json={
            "query": "Mercury",
            "topic": "general",
            "language": "english",
            "max_results": 5,
            "summarize": True,
        },
        headers=_auth_headers(),
    )

    assert response.status_code == 200

    body = response.json()
    assert body["ambiguous"] is True
    assert body["selected_sources"][0]["meaning"] == "planet"
    assert body["meaning_groups"][0]["meaning"] == "planet"
    assert body["request_id"] == "req-search-123"


def test_search_analyze_endpoint_returns_guidance(monkeypatch) -> None:
    def fake_analyze_query(self, query, topic="general"):
        return {
            "query": query,
            "topic": topic,
            "token_count": 1,
            "is_short_query": True,
            "ambiguous_likely": True,
            "recommended_topic": "general",
            "suggested_queries": ["Mercury meaning", "Mercury overview"],
        }

    monkeypatch.setattr("app.api.routes.search.SearchService.analyze_query", fake_analyze_query)

    response = client.get(
        "/api/v1/search/analyze",
        params={"q": "Mercury", "topic": "general"},
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ambiguous_likely"] is True
    assert body["token_count"] == 1
    assert body["suggested_queries"][0] == "Mercury meaning"


def test_search_history_includes_ux_metadata(monkeypatch) -> None:
    class Row:
        id = 1
        query = "Mercury"
        topic = "general"
        provider = "stub-provider"
        result_count = 6
        answer = "summary"
        ambiguous = True
        selected_source_count = 3
        meaning_group_count = 2
        has_summary = True
        created_at = datetime.now(timezone.utc)

    def fake_list_history(self, limit=20, session_id=None, user_id=None):
        return [Row()]

    monkeypatch.setattr("app.api.routes.search.SearchService.list_history", fake_list_history)

    response = client.get("/api/v1/search/history", headers=_auth_headers())

    assert response.status_code == 200
    body = response.json()
    assert body[0]["ambiguous"] is True
    assert body[0]["selected_source_count"] == 3
    assert body[0]["meaning_group_count"] == 2
    assert body[0]["has_summary"] is True