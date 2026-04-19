"""Service layer for Tavily API operations."""
import httpx

from app.core.config import get_settings
from app.providers.tavily_provider import TavilySearchProvider

_MISSING_API_KEY_ERROR = "TAVILY_API_KEY is missing. Set it in your .env file."


class TavilyService:
    """Service for Tavily API operations."""

    def __init__(self) -> None:
        self.provider = TavilySearchProvider()
        self.settings = get_settings()

    def _get_headers(self) -> dict:
        """Get standard Tavily API headers."""
        return {
            "Authorization": f"Bearer {self.settings.tavily_api_key}",
            "Content-Type": "application/json",
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
        if not self.settings.tavily_api_key:
            raise ValueError(_MISSING_API_KEY_ERROR)

        endpoint = f"{self.settings.tavily_base_url}/map"
        headers = self._get_headers()
        payload = {
            "url": url,
            "max_depth": max_depth,
            "max_results": max_results,
            "include_subdomains": include_subdomains,
        }

        async with httpx.AsyncClient(
            timeout=self.settings.http_timeout_seconds,
            trust_env=False,
        ) as client:
            response = await client.post(endpoint, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

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
        if not self.settings.tavily_api_key:
            raise ValueError(_MISSING_API_KEY_ERROR)

        url = f"{self.settings.tavily_base_url}/crawl"
        headers = self._get_headers()

        payload = {
            "urls": urls,
            "max_pages": max_pages,
            "include_raw_content": include_raw_content,
            "include_images": include_images,
        }

        async with httpx.AsyncClient(
            timeout=self.settings.http_timeout_seconds,
            trust_env=False,
        ) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

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
        if not self.settings.tavily_api_key:
            raise ValueError(_MISSING_API_KEY_ERROR)

        url = f"{self.settings.tavily_base_url}/research/tasks"
        headers = self._get_headers()

        payload = {
            "query": query,
            "max_sources": max_sources,
        }

        if focus:
            payload["focus"] = focus

        async with httpx.AsyncClient(
            timeout=self.settings.http_timeout_seconds,
            trust_env=False,
        ) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        return data

    async def get_research_task(self, task_id: str) -> dict:
        """Get research task status and results from Tavily.
        
        Polls task status by ID. Returns in-progress indicator or final results.
        """
        if not self.settings.tavily_api_key:
            raise ValueError(_MISSING_API_KEY_ERROR)

        url = f"{self.settings.tavily_base_url}/research/tasks/{task_id}"
        headers = self._get_headers()

        async with httpx.AsyncClient(
            timeout=self.settings.http_timeout_seconds,
            trust_env=False,
        ) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

        return data
