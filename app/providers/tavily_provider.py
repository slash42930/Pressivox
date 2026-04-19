from __future__ import annotations

from datetime import date
import re
from urllib.parse import urlparse

import httpx

from app.core.config import get_settings
from app.providers.base import SearchProvider


class TavilySearchProvider(SearchProvider):
    name = "tavily"

    def __init__(self) -> None:
        self.settings = get_settings()

    def _clean_provider_snippet(self, snippet: str | None) -> str | None:
        if not snippet:
            return None

        value = snippet
        value = value.replace("[...]", "")
        value = re.sub(r"\s*##\s*[A-Za-z][^\n]*", " ", value)
        value = re.sub(r"\bWikipedia\s+The\s+Free\s+Encyclopedia\b", "", value, flags=re.IGNORECASE)
        value = re.sub(r"\bWikimedia\s+Foundation\b", "", value, flags=re.IGNORECASE)
        value = re.sub(r"\bPowered\s+by\s+MediaWiki\b", "", value, flags=re.IGNORECASE)
        value = re.sub(r"\s+", " ", value).strip()

        return value if len(value) >= 20 else None

    async def search(
        self,
        query: str,
        topic: str,
        max_results: int,
        include_domains: list[str] | None = None,
        exclude_domains: list[str] | None = None,
        **kwargs,
    ) -> dict:
        search_depth = kwargs.get("search_depth", "advanced")
        include_answer = kwargs.get("include_answer", False)
        include_raw_content = kwargs.get("include_raw_content", True)
        include_images = kwargs.get("include_images", False)
        include_image_descriptions = kwargs.get("include_image_descriptions", False)
        include_favicon = kwargs.get("include_favicon", False)
        exact_match = kwargs.get("exact_match", False)
        time_range = kwargs.get("time_range")
        start_date: date | None = kwargs.get("start_date")
        end_date: date | None = kwargs.get("end_date")
        auto_parameters = kwargs.get("auto_parameters", True)

        if not self.settings.tavily_api_key or self.settings.tavily_api_key == "replace_me":
            raise ValueError("TAVILY_API_KEY is missing. Set it in your .env file.")

        url = f"{self.settings.tavily_base_url}/search"
        headers = {
            "Authorization": f"Bearer {self.settings.tavily_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "query": query,
            "topic": topic,
            "search_depth": search_depth,
            "max_results": max_results,
            "include_answer": include_answer,
            "include_raw_content": include_raw_content,
            "include_images": include_images,
            "include_image_descriptions": include_image_descriptions,
            "include_favicon": include_favicon,
            "exact_match": exact_match,
            "auto_parameters": auto_parameters,
        }

        if include_domains:
            payload["include_domains"] = include_domains
        if exclude_domains:
            payload["exclude_domains"] = exclude_domains
        if time_range:
            payload["time_range"] = time_range
        if start_date:
            payload["start_date"] = start_date.isoformat()
        if end_date:
            payload["end_date"] = end_date.isoformat()

        async with httpx.AsyncClient(
            timeout=self.settings.http_timeout_seconds,
            trust_env=False,
        ) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        raw_results = data.get("results", [])
        normalized_results: list[dict] = []

        for item in raw_results:
            item_url = item.get("url")
            if not item_url:
                continue

            hostname = urlparse(item_url).hostname
            normalized_results.append(
                {
                    "title": item.get("title", "Untitled"),
                    "url": item_url,
                    "snippet": self._clean_provider_snippet(item.get("content")),
                    "score": item.get("score"),
                    "source": hostname,
                    "raw_content": item.get("raw_content"),
                    "published_date": item.get("published_date"),
                    "favicon": item.get("favicon"),
                }
            )

        return {
            "results": normalized_results,
            "answer": data.get("answer"),
            "response_time": data.get("response_time"),
            "request_id": data.get("request_id"),
            "auto_parameters": data.get("auto_parameters"),
            "usage": data.get("usage"),
        }