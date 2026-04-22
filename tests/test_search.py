import asyncio

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_search_endpoint_returns_rich_ui_metadata(monkeypatch) -> None:
    async def fake_run_search(self, request, session_id=None):
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
        headers={"X-Session-Id": "test-session"},
    )

    assert response.status_code == 200

    body = response.json()
    assert body["ambiguous"] is True
    assert body["selected_sources"][0]["meaning"] == "planet"
    assert body["meaning_groups"][0]["meaning"] == "planet"
    assert body["request_id"] == "req-search-123"