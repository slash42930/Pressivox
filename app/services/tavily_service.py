"""Service layer for Tavily API operations."""
from datetime import datetime, timezone
from typing import Any, Callable

import httpx

from app.core.config import get_settings
from app.providers.tavily_provider import TavilySearchProvider

_MISSING_API_KEY_ERROR = "TAVILY_API_KEY is missing. Set it in your .env file."


class ProviderResponseError(ValueError):
    """Raised when an upstream provider payload cannot be parsed safely."""


class TavilyService:
    """Service for Tavily API operations."""

    def __init__(
        self,
        client_factory: Callable[..., httpx.AsyncClient] | None = None,
    ) -> None:
        self.provider = TavilySearchProvider()
        self.settings = get_settings()
        self._client_factory = client_factory or httpx.AsyncClient

    def _validate_api_key(self) -> None:
        if not self.settings.tavily_api_key or self.settings.tavily_api_key == "replace_me":
            raise ValueError(_MISSING_API_KEY_ERROR)

    def _get_headers(self) -> dict:
        """Get standard Tavily API headers."""
        return {
            "Authorization": f"Bearer {self.settings.tavily_api_key}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _response_json(response: httpx.Response) -> dict[str, Any]:
        if not response.content:
            return {}
        try:
            payload = response.json()
        except ValueError as exc:
            raise ProviderResponseError("Tavily returned invalid JSON.") from exc
        if not isinstance(payload, dict):
            raise ProviderResponseError("Tavily returned an unexpected response shape.")
        return payload

    @staticmethod
    def _normalize_task_status(status: str | None) -> str:
        raw = (status or "").strip().lower()
        aliases = {
            "queued": "queued",
            "pending": "queued",
            "running": "running",
            "in_progress": "running",
            "processing": "running",
            "completed": "completed",
            "done": "completed",
            "success": "completed",
            "failed": "failed",
            "error": "failed",
            "cancelled": "failed",
        }
        return aliases.get(raw, "unknown")

    def _normalize_task_payload(self, task_id: str, data: dict[str, Any]) -> dict[str, Any]:
        status = self._normalize_task_status(
            str(data.get("status") or data.get("state") or data.get("task_status") or "")
        )
        normalized_task_id = (
            str(data.get("task_id") or data.get("request_id") or data.get("id") or task_id)
            .strip()
            or task_id
        )

        result_blob = data.get("result") or data.get("data") or {}
        result_items = result_blob.get("results") if isinstance(result_blob, dict) else []
        if not isinstance(result_items, list):
            result_items = []

        sources: list[dict[str, Any]] = []
        for item in result_items[:10]:
            if not isinstance(item, dict):
                continue
            url = str(item.get("url") or "").strip()
            title = str(item.get("title") or "").strip() or "Untitled"
            if not url:
                continue
            sources.append(
                {
                    "title": title,
                    "url": url,
                    "source": item.get("source"),
                    "snippet": item.get("content") or item.get("snippet"),
                }
            )

        normalized = dict(data)
        normalized["task_id"] = normalized_task_id
        normalized["status"] = status
        normalized["is_terminal"] = status in {"completed", "failed"}
        normalized["result_sources"] = sources
        normalized["result_count"] = len(sources)
        normalized["error_message"] = data.get("error") or data.get("message")
        return normalized

    def _normalize_task_submission(self, data: dict) -> dict:
        """Normalize Tavily response to the UI contract.

        Tavily deployments can return different keys for task submission.
        This method keeps our API stable for the frontend.
        """
        task_id = (
            data.get("task_id")
            or data.get("request_id")
            or data.get("id")
            or data.get("research_id")
            or data.get("job_id")
            or ""
        )
        if not task_id:
            raise ValueError("Tavily response did not include a task identifier.")

        status = str(data.get("status") or data.get("state") or "queued")
        created_at = (
            data.get("created_at")
            or data.get("created")
            or data.get("submitted_at")
            or datetime.now(timezone.utc).isoformat()
        )

        return {
            "task_id": task_id,
            "status": status,
            "created_at": str(created_at),
        }

    async def map(
        self,
        url: str,
        max_depth: int = 1,
        max_results: int = 50,
        include_subdomains: bool = True,
    ) -> dict:
        """Retrieve map data from Tavily.
        
        Fetches available sources and domains available through Tavily.
        """
        self._validate_api_key()

        endpoint = f"{self.settings.tavily_base_url}/map"
        headers = self._get_headers()
        payload = {
            "url": url,
            "max_depth": max_depth,
            "max_results": max_results,
            "include_subdomains": include_subdomains,
        }

        async with self._client_factory(
            timeout=self.settings.http_timeout_seconds,
            trust_env=False,
        ) as client:
            response = await client.post(endpoint, headers=headers, json=payload)
            response.raise_for_status()
            data = self._response_json(response)

        return data

    async def crawl(
        self,
        urls: list[str],
        max_pages: int = 10,
        include_raw_content: bool = False,
        include_images: bool = False,
    ) -> dict:
        """Crawl URLs using Tavily.
        
        Extracts and processes content from multiple URLs.
        """
        self._validate_api_key()

        url = f"{self.settings.tavily_base_url}/crawl"
        headers = self._get_headers()

        payload = {
            "urls": urls,
            "max_pages": max_pages,
            "include_raw_content": include_raw_content,
            "include_images": include_images,
        }

        async with self._client_factory(
            timeout=self.settings.http_timeout_seconds,
            trust_env=False,
        ) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = self._response_json(response)

        return data

    async def submit_research_task(
        self,
        query: str,
        focus: str | None = None,
        max_sources: int = 20,
    ) -> dict:
        """Submit a research task to Tavily.
        
        Submits an async research task and returns task ID for polling.
        """
        self._validate_api_key()

        primary_url = f"{self.settings.tavily_base_url}/research"
        fallback_url = f"{self.settings.tavily_base_url}/research/tasks"
        headers = self._get_headers()

        normalized_query = query.strip()
        if not normalized_query:
            raise ValueError("Query is required.")

        enriched_input = normalized_query
        if focus and focus.strip():
            enriched_input = f"{normalized_query}\nFocus areas: {focus.strip()}"

        primary_payload = {
            "input": enriched_input,
            "stream": False,
        }
        legacy_payload = {
            "query": normalized_query,
            "max_sources": max_sources,
        }
        if focus and focus.strip():
            legacy_payload["focus"] = focus.strip()

        attempts = [
            (primary_url, primary_payload),
            (primary_url, legacy_payload),
            (fallback_url, legacy_payload),
            (fallback_url, primary_payload),
        ]

        async with self._client_factory(
            timeout=self.settings.http_timeout_seconds,
            trust_env=False,
        ) as client:
            last_response: httpx.Response | None = None
            data: dict[str, Any] = {}

            for url, payload in attempts:
                response = await client.post(url, headers=headers, json=payload)
                last_response = response
                if response.is_success:
                    data = self._response_json(response)
                    break

                # Different Tavily API generations may reject one shape but accept another.
                if response.status_code in {404, 405, 422}:
                    continue

                response.raise_for_status()

            if not data:
                assert last_response is not None
                last_response.raise_for_status()

        return self._normalize_task_submission(data)

    async def get_research_task(self, task_id: str) -> dict:
        """Get research task status and results from Tavily.
        
        Polls task status by ID. Returns in-progress indicator or final results.
        """
        self._validate_api_key()

        primary_url = f"{self.settings.tavily_base_url}/research/{task_id}"
        fallback_url = f"{self.settings.tavily_base_url}/research/tasks/{task_id}"
        headers = self._get_headers()

        async with self._client_factory(
            timeout=self.settings.http_timeout_seconds,
            trust_env=False,
        ) as client:
            response = await client.get(primary_url, headers=headers)
            if response.status_code in {404, 405}:
                response = await client.get(fallback_url, headers=headers)

            response.raise_for_status()
            data = self._response_json(response)

        return self._normalize_task_payload(task_id, data)
