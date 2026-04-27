from __future__ import annotations

import re
import time
import uuid
import unicodedata
from datetime import date as _date, timedelta as _timedelta
from urllib.parse import urlparse

import httpx

from app.core.config import get_settings
from app.providers.base import SearchProvider

_MONTH_MAP = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def _normalize_serper_date(raw: str | None) -> str | None:
    """Convert Serper news date strings to ISO YYYY-MM-DD.

    Serper /news returns relative and absolute formats in multiple locales.
    - Relative EN: "4 days ago", "2 hours ago", "1 month ago", "yesterday"
    - Relative RO: "acum 2 ore", "Acum o zi", "acum 20 de ore"
    - Absolute: "Feb 6, 2024", "Nov 12, 2018"
    Returns ISO string when parseable, original string otherwise.
    """
    if not raw:
        return None
    s = raw.strip().lower()
    s_norm = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s_norm = re.sub(r"\s+", " ", s_norm).strip()
    today = _date.today()

    if s_norm in ("yesterday", "ieri"):
        return (today - _timedelta(days=1)).isoformat()
    if s_norm in ("today", "azi"):
        return today.isoformat()

    # Relative: "N unit(s) ago"
    m = re.match(r"(\d+)\s*(minute|hour|day|week|month|year)s?\s+ago", s_norm)
    if m:
        n, unit = int(m.group(1)), m.group(2)
        if unit in ("minute", "hour"):
            return today.isoformat()
        if unit == "day":
            return (today - _timedelta(days=n)).isoformat()
        if unit == "week":
            return (today - _timedelta(weeks=n)).isoformat()
        if unit == "month":
            return (today - _timedelta(days=n * 30)).isoformat()
        if unit == "year":
            return (today - _timedelta(days=n * 365)).isoformat()

    # Relative RO: "acum 2 ore", "acum o zi", "acum 20 de ore"
    m = re.match(r"acum\s+(\d+|o|un|una)\s*(?:de\s+)?([a-z]+)", s_norm)
    if m:
        n_raw, unit = m.group(1), m.group(2)
        n = 1 if n_raw in ("o", "un", "una") else int(n_raw)
        if unit.startswith("minut") or unit.startswith("ora") or unit.startswith("ore"):
            return today.isoformat()
        if unit.startswith("zi"):
            return (today - _timedelta(days=n)).isoformat()
        if unit.startswith("saptaman"):
            return (today - _timedelta(weeks=n)).isoformat()
        if unit.startswith("luna") or unit.startswith("luni"):
            return (today - _timedelta(days=n * 30)).isoformat()
        if unit.startswith("an"):
            return (today - _timedelta(days=n * 365)).isoformat()

    # Absolute: "Feb 6, 2024" or "Feb 06, 2024"
    m = re.match(r"([a-z]{3})\s+(\d{1,2}),?\s+(\d{4})", s_norm)
    if m:
        month = _MONTH_MAP.get(m.group(1))
        if month:
            try:
                return _date(int(m.group(3)), month, int(m.group(2))).isoformat()
            except ValueError:
                pass

    return raw  # unrecognised — return as-is


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


def _iso_to_serper_date(iso: object) -> str:
    """Convert YYYY-MM-DD string or date object to M/D/YYYY (no leading zeros) for Serper tbs."""
    try:
        if isinstance(iso, _date):
            return f"{iso.month}/{iso.day}/{iso.year}"
        y, m, d = str(iso).split("-")
        return f"{int(m)}/{int(d)}/{y}"
    except (ValueError, AttributeError):
        return ""


def _build_custom_date_tbs(start_date: str | None, end_date: str | None) -> str:
    """Build Serper tbs string for a custom date range.

    Serper (Google) /search custom date range format:
        cdr:1,cd_min:M/D/YYYY,cd_max:M/D/YYYY
    Either bound may be omitted.
    """
    parts = ["cdr:1"]
    if start_date:
        cd_min = _iso_to_serper_date(start_date)
        if cd_min:
            parts.append(f"cd_min:{cd_min}")
    if end_date:
        cd_max = _iso_to_serper_date(end_date)
        if cd_max:
            parts.append(f"cd_max:{cd_max}")
    return ",".join(parts)


def _date_span_to_news_tbs(start_date: object, end_date: object) -> str:
    """Map a date range to the nearest Serper /news tbs preset.

    Serper /news only supports preset qdr:d/w/m/y — custom cdr:1 is silently
    ignored on the news endpoint.  Pick the tightest preset that covers the
    requested range, measured from start_date back to today.
    Accepts both datetime.date objects and YYYY-MM-DD strings.
    """
    try:
        today = _date.today()
        if start_date:
            ref = start_date if isinstance(start_date, _date) else _date.fromisoformat(str(start_date))
        else:
            ref = today
        days_ago = max(0, (today - ref).days)
    except (ValueError, AttributeError, TypeError):
        days_ago = 7  # safe fallback

    if days_ago <= 1:
        return "qdr:d"
    if days_ago <= 7:
        return "qdr:w"
    if days_ago <= 31:
        return "qdr:m"
    return "qdr:y"

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

        return value if len(value) >= 10 else None

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

        from app.utils.validators import validate_serper_api_key
        validate_serper_api_key(self.settings.serper_api_key, env=self.settings.app_env)

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

        start_date = kwargs.get("start_date")
        end_date = kwargs.get("end_date")

        if start_date or end_date:
            # Custom date range takes priority over named time_range.
            # /news endpoint only supports preset qdr:* values; cdr:1 is silently
            # ignored there, so map the span to the nearest preset instead.
            if topic == "news":
                payload["tbs"] = _date_span_to_news_tbs(start_date, end_date)
            else:
                payload["tbs"] = _build_custom_date_tbs(start_date, end_date)
        elif time_range and time_range in _TBS_MAP:
            payload["tbs"] = _TBS_MAP[time_range]

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

            favicon_url: str | None = None
            if include_favicon and hostname:
                favicon_url = f"https://www.google.com/s2/favicons?sz=32&domain={hostname}"

            normalized_results.append(
                {
                    "title": item.get("title", "Untitled"),
                    "url": item_url,
                    "snippet": self._clean_snippet(item.get("snippet")),
                    "score": score,
                    "source": hostname,
                    "raw_content": None,
                    "published_date": _normalize_serper_date(item.get("date")),
                    "favicon": favicon_url,
                    # news results carry an article thumbnail; organic results don't
                    "thumbnail": item.get("imageUrl"),
                }
            )

        # ── Serper rich SERP features ─────────────────────────────────────────
        kg_data: dict = data.get("knowledgeGraph") or {}
        ab_data: dict = data.get("answerBox") or {}

        # Best answer text: prefer KG description, then answerBox snippet, then answer
        answer: str | None = None
        if include_answer:
            answer = (
                kg_data.get("description")
                or ab_data.get("snippet")
                or ab_data.get("answer")
            )

        # Knowledge graph — entity card (title, type, description, attributes)
        knowledge_graph: dict | None = None
        if kg_data:
            knowledge_graph = {
                "title": kg_data.get("title"),
                "type": kg_data.get("type"),
                "description": kg_data.get("description"),
                "website": kg_data.get("website"),
                "image_url": kg_data.get("imageUrl"),
                "attributes": kg_data.get("attributes") or {},
            }

        # Answer box — featured snippet
        answer_box: dict | None = None
        if ab_data:
            answer_box = {
                "title": ab_data.get("title"),
                "answer": ab_data.get("answer"),
                "snippet": ab_data.get("snippet"),
                "highlighted": ab_data.get("snippetHighlighted") or [],
            }

        # People Also Ask
        people_also_ask: list[dict] = [
            {
                "question": paa.get("question", ""),
                "snippet": paa.get("snippet", ""),
                "title": paa.get("title", ""),
                "link": paa.get("link", ""),
            }
            for paa in (data.get("peopleAlsoAsk") or [])
            if paa.get("question")
        ]

        # Related searches — list of query strings
        related_searches: list[str] = [
            rs["query"]
            for rs in (data.get("relatedSearches") or [])
            if rs.get("query")
        ]

        return {
            "results": normalized_results,
            "answer": answer,
            "knowledge_graph": knowledge_graph,
            "answer_box": answer_box,
            "people_also_ask": people_also_ask,
            "related_searches": related_searches,
            "response_time": elapsed,
            "request_id": str(uuid.uuid4()),
            "auto_parameters": None,
            "usage": {"searches": 1},
        }
