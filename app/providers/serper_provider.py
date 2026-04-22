from __future__ import annotations

import re
import time
import uuid
from urllib.parse import urlparse

import httpx

from app.core.config import get_settings
from app.providers.base import SearchProvider

_TBS_MAP = {
    "day": "qdr:d",
    "d": "qdr:d",
    "week": "qdr:w",
    "w": "qdr:w",
    "month": "qdr:m",
    "m": "qdr:m",
    "year": "qdr:y",
    "y": "qdr:y",
}

_LANG_MAP = {
    "english": "en",
    "romanian": "ro",
}


class SerperSearchProvider(SearchProvider):
    name = "serper"

    def __init__(self) -> None:
        self.settings = get_settings()

    def _clean_snippet(self, snippet: str | None) -> str | None:
        if not snippet:
            return None

        value = snippet
        value = re.sub(r"\s*##\s*[A-Za-z][^\n]*", " ", value)
        value = re.sub(r"\bWikipedia\s+The\s+Free\s+Encyclopedia\b", "", value, flags=re.IGNORECASE)
        value = re.sub(r"\bWikimedia\s+Foundation\b", "", value, flags=re.IGNORECASE)
        value = re.sub(r"\s+", " ", value).strip()

        return value if len(value) >= 20 else None

    def _build_query(
        self,
        query: str,
        include_domains: list[str] | None,
        exclude_domains: list[str] | None,
        exact_match: bool,
    ) -> str:
        q = f'"{query}"' if exact_match else query

        if include_domains:
            site_clause = " OR ".join(f"site:{d}" for d in include_domains)
            q = f"({site_clause}) {q}"
        if exclude_domains:
            exclusions = " ".join(f"-site:{d}" for d in exclude_domains)
            q = f"{q} {exclusions}"

        return q

    async def search(
        self,
        query: str,
        topic: str,
        max_results: int,
        include_domains: list[str] | None = None,
        exclude_domains: list[str] | None = None,
        **kwargs,
    ) -> dict:
        include_answer = kwargs.get("include_answer", False)
        include_favicon = kwargs.get("include_favicon", False)
        exact_match = kwargs.get("exact_match", False)
        time_range = kwargs.get("time_range")
        language = kwargs.get("language", "english")

        if not self.settings.serper_api_key or self.settings.serper_api_key == "replace_me":
            raise ValueError("SERPER_API_KEY is missing. Set it in your .env file.")

        built_query = self._build_query(query, include_domains, exclude_domains, exact_match)

        # Serper has a dedicated /news endpoint; everything else hits /search
        if topic == "news":
            endpoint = f"{self.settings.serper_base_url}/news"
        else:
            endpoint = f"{self.settings.serper_base_url}/search"

        headers = {
            "X-API-KEY": self.settings.serper_api_key,
            "Content-Type": "application/json",
        }

        payload: dict = {
            "q": built_query,
            "num": min(max_results, 100),
            "hl": _LANG_MAP.get(str(language), "en"),
        }

        if time_range and time_range in _TBS_MAP:
            payload["tbs"] = _TBS_MAP[time_range]

        # Serper does not support start_date / end_date natively; ignore gracefully.

        t0 = time.monotonic()

        async with httpx.AsyncClient(
            timeout=self.settings.http_timeout_seconds,
            trust_env=False,
        ) as client:
            response = await client.post(endpoint, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        elapsed = round(time.monotonic() - t0, 3)

        # Serper returns "organic" for /search and "news" for /news
        if topic == "news":
            raw_results = data.get("news", [])
        else:
            raw_results = data.get("organic", [])

        normalized_results: list[dict] = []

        for item in raw_results:
            item_url = item.get("link")
            if not item_url:
                continue

            hostname = urlparse(item_url).hostname
            position = item.get("position", len(normalized_results) + 1)
            score = round(1.0 / position, 6) if position else None

            normalized_results.append(
                {
                    "title": item.get("title", "Untitled"),
                    "url": item_url,
                    "snippet": self._clean_snippet(item.get("snippet")),
                    "score": score,
                    "source": hostname,
                    "raw_content": None,
                    "published_date": item.get("date"),
                    "favicon": None,
                }
            )

        answer: str | None = None
        if include_answer:
            kg = data.get("knowledgeGraph", {})
            answer = kg.get("description") or data.get("answerBox", {}).get("answer")

        return {
            "results": normalized_results,
            "answer": answer,
            "response_time": elapsed,
            "request_id": str(uuid.uuid4()),
            "auto_parameters": None,
            "usage": {"searches": 1},
        }
