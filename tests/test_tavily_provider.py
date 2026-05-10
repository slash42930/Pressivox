import asyncio

import httpx
import pytest

from app.providers.tavily_provider import TavilySearchProvider


def test_tavily_provider_drops_malformed_result_urls(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('TAVILY_API_KEY', 'test-key')

    class _FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url: str, headers: dict, json: dict) -> httpx.Response:
            await asyncio.sleep(0)
            request = httpx.Request('POST', url)
            return httpx.Response(
                200,
                request=request,
                json={
                    'results': [
                        {
                            'title': 'Bad URL entry',
                            'url': 'javascript:alert(1)',
                            'content': 'This should never be returned as source result.',
                        },
                        {
                            'title': 'Valid URL entry',
                            'url': 'https://example.com/article',
                            'content': 'Valid content from trusted source with enough detail.',
                        },
                    ]
                },
            )

    monkeypatch.setattr('app.providers.tavily_provider.httpx.AsyncClient', lambda **kwargs: _FakeClient())

    provider = TavilySearchProvider()
    payload = asyncio.run(
        provider.search(
            query='mercury',
            topic='general',
            max_results=5,
            include_domains=[],
            exclude_domains=[],
        )
    )

    assert len(payload['results']) == 1
    assert payload['results'][0]['url'] == 'https://example.com/article'
