import asyncio

import httpx
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


BASE_PAYLOAD = {
    "query": "mercury",
    "topic": "general",
    "language": "english",
    "max_results": 5,
    "summarize": True,
    "extract_top_results": True,
}


def _valid_service_result() -> dict:
    return {
        "query": "mercury",
        "topic": "general",
        "provider": "tavily",
        "results": [
            {
                "title": "Mercury planet",
                "url": "https://example.com/planet",
                "snippet": "Mercury is the smallest planet in the solar system.",
                "score": 0.95,
                "source": "example.com",
            },
            {
                "title": "Mercury disambiguation",
                "url": "https://example.com/disambiguation",
                "snippet": "Mercury may refer to many topics.",
                "score": 0.1,
                "source": "example.com",
            },
        ],
        "summary": "Mercury has multiple meanings.",
        "extracted_summary": "Planet: Mercury is the smallest planet.",
        "extracted_count": 1,
        "answer": None,
        "response_time": 0.41,
        "request_id": "req-1",
        "usage": {"credits": 1},
        "selected_sources": [
            {
                "title": "Mercury planet",
                "url": "https://example.com/planet",
                "source": "example.com",
            }
        ],
        "ambiguous": False,
        "meaning_groups": [],
    }


def test_research_endpoint_success_returns_structured_sections(monkeypatch) -> None:
    async def fake_run_search(self, request, session_id=None, user_id=None):
        await asyncio.sleep(0)
        return _valid_service_result()

    monkeypatch.setattr("app.api.routes.research.SearchService.run_search", fake_run_search)

    response = client.post("/api/v1/research", json=BASE_PAYLOAD)

    assert response.status_code == 200
    body = response.json()
    assert body["source_count"] == 1
    assert body["sections"]["concise_summary"]
    assert body["sections"]["key_findings"]
    assert body["sections"]["sources"][0]["url"] == "https://example.com/planet"


def test_research_endpoint_rejects_empty_query() -> None:
    payload = dict(BASE_PAYLOAD)
    payload["query"] = ""

    response = client.post("/api/v1/research", json=payload)

    assert response.status_code == 422


def test_research_endpoint_maps_provider_network_failure(monkeypatch) -> None:
    async def fake_run_search(self, request, session_id=None, user_id=None):
        await asyncio.sleep(0)
        req = httpx.Request("POST", "https://api.tavily.com/search")
        raise httpx.ConnectError("network down", request=req)

    monkeypatch.setattr("app.api.routes.research.SearchService.run_search", fake_run_search)

    response = client.post("/api/v1/research", json=BASE_PAYLOAD)

    assert response.status_code == 502
    assert "network error" in response.json()["detail"].lower()


def test_research_endpoint_maps_provider_timeout(monkeypatch) -> None:
    async def fake_run_search(self, request, session_id=None, user_id=None):
        await asyncio.sleep(0)
        req = httpx.Request("POST", "https://api.tavily.com/search")
        raise httpx.ReadTimeout("timed out", request=req)

    monkeypatch.setattr("app.api.routes.research.SearchService.run_search", fake_run_search)

    response = client.post("/api/v1/research", json=BASE_PAYLOAD)

    assert response.status_code == 504
    assert "timed out" in response.json()["detail"].lower()


def test_research_endpoint_maps_invalid_provider_payload(monkeypatch) -> None:
    async def fake_run_search(self, request, session_id=None, user_id=None):
        await asyncio.sleep(0)
        raise ValueError("Tavily returned invalid JSON.")

    monkeypatch.setattr("app.api.routes.research.SearchService.run_search", fake_run_search)

    response = client.post("/api/v1/research", json=BASE_PAYLOAD)

    assert response.status_code == 502
    assert "invalid response" in response.json()["detail"].lower()


def test_research_endpoint_reports_limitations_for_missing_sources(monkeypatch) -> None:
    async def fake_run_search(self, request, session_id=None, user_id=None):
        await asyncio.sleep(0)
        result = _valid_service_result()
        result["results"] = []
        result["extracted_count"] = 0
        result["summary"] = "No reliable sources found."
        result["extracted_summary"] = None
        return result

    monkeypatch.setattr("app.api.routes.research.SearchService.run_search", fake_run_search)

    response = client.post("/api/v1/research", json=BASE_PAYLOAD)

    assert response.status_code == 200
    body = response.json()
    assert body["source_count"] == 0
    assert body["sections"]["limitations"]


def test_research_endpoint_accepts_missing_or_invalid_auth_token(monkeypatch) -> None:
    async def fake_run_search(self, request, session_id=None, user_id=None):
        await asyncio.sleep(0)
        return _valid_service_result()

    monkeypatch.setattr("app.api.routes.research.SearchService.run_search", fake_run_search)

    response = client.post(
        "/api/v1/research",
        json=BASE_PAYLOAD,
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 200


def test_research_endpoint_is_not_rate_limited_for_normal_burst(monkeypatch) -> None:
    async def fake_run_search(self, request, session_id=None, user_id=None):
        await asyncio.sleep(0)
        return _valid_service_result()

    monkeypatch.setattr("app.api.routes.research.SearchService.run_search", fake_run_search)

    first = client.post("/api/v1/research", json=BASE_PAYLOAD)
    second = client.post("/api/v1/research", json=BASE_PAYLOAD)

    assert first.status_code == 200
    assert second.status_code == 200
