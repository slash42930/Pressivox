import asyncio
from collections.abc import Callable
from collections.abc import Generator

import httpx
import pytest

from app.core.config import get_settings
from app.services.tavily_service import ProviderResponseError, TavilyService


def _client_factory_from_transport(
    transport: httpx.MockTransport,
) -> Callable[..., httpx.AsyncClient]:
    def _factory(**kwargs) -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=transport, **kwargs)

    return _factory


@pytest.fixture(autouse=True)
def _reset_settings_cache() -> Generator[None, None, None]:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_submit_research_task_falls_back_to_legacy_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/research"):
            return httpx.Response(404, request=request, json={"detail": "not found"})
        if request.url.path.endswith("/research/tasks"):
            return httpx.Response(
                200,
                request=request,
                json={
                    "task_id": "task-123",
                    "status": "queued",
                    "created_at": "2026-01-01T00:00:00Z",
                },
            )
        return httpx.Response(500, request=request)

    service = TavilyService(
        client_factory=_client_factory_from_transport(httpx.MockTransport(handler)),
    )

    result = asyncio.run(service.submit_research_task("climate change"))

    assert result["task_id"] == "task-123"
    assert result["status"] == "queued"


def test_submit_research_task_raises_on_invalid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, request=request, text="not-json")

    service = TavilyService(
        client_factory=_client_factory_from_transport(httpx.MockTransport(handler)),
    )

    with pytest.raises(ProviderResponseError, match="invalid JSON"):
        asyncio.run(service.submit_research_task("ai"))


def test_get_research_task_normalizes_status_and_sources(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            request=request,
            json={
                "id": "task-7",
                "state": "in_progress",
                "result": {
                    "results": [
                        {
                            "title": "Example source",
                            "url": "https://example.com/source",
                            "source": "example.com",
                            "content": "useful content",
                        }
                    ]
                },
            },
        )

    service = TavilyService(
        client_factory=_client_factory_from_transport(httpx.MockTransport(handler)),
    )

    result = asyncio.run(service.get_research_task("task-7"))

    assert result["task_id"] == "task-7"
    assert result["status"] == "running"
    assert result["is_terminal"] is False
    assert result["result_count"] == 1
    assert result["result_sources"][0]["url"] == "https://example.com/source"


def test_get_research_task_raises_on_invalid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, request=request, text="broken")

    service = TavilyService(
        client_factory=_client_factory_from_transport(httpx.MockTransport(handler)),
    )

    with pytest.raises(ProviderResponseError, match="invalid JSON"):
        asyncio.run(service.get_research_task("task-x"))
