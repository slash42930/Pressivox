"""Service layer for Serper API operations (crawl, map, research tasks)."""
from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.providers.serper_provider import SerperSearchProvider

_MISSING_API_KEY_ERROR = "SERPER_API_KEY is missing. Set it in your .env file."

# In-memory task store — keyed by task_id.
# Tasks are lost on server restart; acceptable for dev/demo use.
_TASK_STORE: dict[str, dict] = {}


class SerperService:
    """Service for crawl, map, and research-task operations backed by Serper."""

    def __init__(self) -> None:
        self.settings = get_settings()

    # ------------------------------------------------------------------
    # Crawl
    # ------------------------------------------------------------------

    async def crawl(
        self,
        urls: list[str],
        max_pages: int = 10,
        include_raw_content: bool = False,
        include_images: bool = False,
    ) -> dict:
        """Extract content from a list of URLs using httpx + readability-lxml.

        The Serper API does expose a scrape endpoint, but this implementation
        reuses the project's own ExtractionService so no extra API credits
        are consumed.  The response shape mirrors the old Tavily /crawl output.
        """
        if not self.settings.serper_api_key or self.settings.serper_api_key == "replace_me":
            raise ValueError(_MISSING_API_KEY_ERROR)

        # Import here to avoid circular imports (ExtractionService uses the db).
        from app.services.extraction_service import ExtractionService

        t0 = time.monotonic()
        results: list[dict] = []

        # We need a throwaway db session only for ExtractionService's history
        # insert. Because crawl callers do not supply a db, we create a
        # session-less instance by passing None — ExtractionService only writes
        # to db when db is not None.
        extractor = ExtractionService(db=None)  # type: ignore[arg-type]

        for url in urls[: max(1, max_pages)]:
            try:
                extracted = await extractor.extract_from_url(url)
                results.append(
                    {
                        "url": extracted.get("url", url),
                        "title": extracted.get("title", ""),
                        "content": extracted.get("extracted_text", ""),
                        "raw_content": extracted.get("extracted_text", "") if include_raw_content else None,
                        "content_length": extracted.get("content_length", 0),
                        "source": extracted.get("source"),
                    }
                )
            except Exception as exc:  # noqa: BLE001
                results.append(
                    {
                        "url": url,
                        "title": "",
                        "content": "",
                        "raw_content": None,
                        "content_length": 0,
                        "source": None,
                        "error": str(exc),
                    }
                )

        return {
            "results": results,
            "response_time": round(time.monotonic() - t0, 3),
        }

    # ------------------------------------------------------------------
    # Map
    # ------------------------------------------------------------------

    async def map(
        self,
        url: str,
        max_depth: int = 1,
        max_results: int = 50,
        include_subdomains: bool = True,
    ) -> dict:
        """Crawl a website and return a flat list of discovered URLs.

        Performs a BFS link extraction up to *max_depth* levels deep,
        collecting up to *max_results* unique URLs.  Implemented with
        httpx + BeautifulSoup — no Serper credits consumed.
        """
        if not self.settings.serper_api_key or self.settings.serper_api_key == "replace_me":
            raise ValueError(_MISSING_API_KEY_ERROR)

        parsed_base = urlparse(url)
        base_host = parsed_base.hostname or ""

        headers = {
            "User-Agent": (
                "WebSearchBackend/0.1 "
                "(learning project) Python-httpx"
            ),
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

        t0 = time.monotonic()
        visited: set[str] = set()
        discovered: list[str] = []
        queue: list[tuple[str, int]] = [(url, 0)]

        async with httpx.AsyncClient(
            timeout=self.settings.http_timeout_seconds,
            trust_env=False,
            follow_redirects=True,
        ) as client:
            while queue and len(discovered) < max_results:
                current_url, depth = queue.pop(0)

                if current_url in visited:
                    continue
                visited.add(current_url)

                try:
                    resp = await client.get(current_url, headers=headers)
                    resp.raise_for_status()
                except Exception:  # noqa: BLE001
                    continue

                if current_url != url:
                    discovered.append(current_url)

                if depth >= max_depth:
                    continue

                content_type = resp.headers.get("content-type", "")
                if "html" not in content_type:
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")
                for tag in soup.find_all("a", href=True):
                    href = str(tag["href"]).strip()
                    if not href or href.startswith("#") or href.startswith("mailto:"):
                        continue

                    absolute = urljoin(current_url, href)
                    parsed = urlparse(absolute)

                    if parsed.scheme not in {"http", "https"}:
                        continue

                    link_host = parsed.hostname or ""
                    if include_subdomains:
                        # Accept same domain and any subdomain
                        if not (link_host == base_host or link_host.endswith(f".{base_host}")):
                            continue
                    else:
                        if link_host != base_host:
                            continue

                    # Normalise — drop fragment
                    clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                    if parsed.query:
                        clean += f"?{parsed.query}"

                    if clean not in visited:
                        queue.append((clean, depth + 1))

        return {
            "base_url": url,
            "urls": discovered[:max_results],
            "url_count": len(discovered[:max_results]),
            "response_time": round(time.monotonic() - t0, 3),
        }

    # ------------------------------------------------------------------
    # Research tasks (synchronous execution, in-memory store)
    # ------------------------------------------------------------------

    async def submit_research_task(
        self,
        query: str,
        focus: str | None = None,
        max_sources: int = 20,
    ) -> dict:
        """Execute research synchronously and store results under a new task ID.

        The caller receives a task record with ``status: "queued"``; a
        subsequent call to :meth:`get_research_task` will return the completed
        results.  This simulates an async task API so that the frontend polling
        pattern continues to work without modification.
        """
        if not self.settings.serper_api_key or self.settings.serper_api_key == "replace_me":
            raise ValueError(_MISSING_API_KEY_ERROR)

        normalized_query = query.strip()
        if not normalized_query:
            raise ValueError("Query is required.")

        task_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()

        # Run the searches now and store results — "async task" illusion.
        provider = SerperSearchProvider()
        results: list[dict] = []

        try:
            main_payload = await provider.search(
                query=normalized_query,
                topic="general",
                max_results=min(max_sources, 20),
            )
            results.extend(main_payload.get("results", []))

            if focus and focus.strip():
                focus_query = f"{normalized_query} {focus.strip()}"
                focus_payload = await provider.search(
                    query=focus_query,
                    topic="general",
                    max_results=10,
                )
                # Merge de-duplicated by URL
                seen_urls = {r["url"] for r in results}
                for item in focus_payload.get("results", []):
                    if item["url"] not in seen_urls:
                        results.append(item)
                        seen_urls.add(item["url"])

            status = "completed"
            error = None
        except Exception as exc:  # noqa: BLE001
            status = "failed"
            error = str(exc)

        _TASK_STORE[task_id] = {
            "task_id": task_id,
            "status": status,
            "query": normalized_query,
            "focus": focus,
            "results": results,
            "created_at": created_at,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "error": error,
        }

        return {
            "task_id": task_id,
            "status": "queued",
            "created_at": created_at,
        }

    def get_research_task(self, task_id: str) -> dict:
        """Retrieve research task results by task ID."""
        if not self.settings.serper_api_key or self.settings.serper_api_key == "replace_me":
            raise ValueError(_MISSING_API_KEY_ERROR)

        task = _TASK_STORE.get(task_id)
        if task is None:
            raise KeyError(f"Task {task_id} not found.")

        return task
