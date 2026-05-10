"""Presentation helpers for search and research API responses."""

from urllib.parse import ParseResult, urlparse, urlunparse

from app.services.search.result_filtering import is_good_result_for_extraction


def _clean_text(value: str | None) -> str:
    return " ".join((value or "").split()).strip()


def _normalized_url_key(raw_url: str) -> str:
    parsed = urlparse(raw_url)
    netloc = parsed.netloc.lower().removeprefix("www.")
    path = parsed.path.rstrip("/")
    return f"{parsed.scheme.lower()}://{netloc}{path}"


def _sanitize_http_url(value: str | None) -> str | None:
    raw = _clean_text(value)
    if not raw:
        return None

    parsed = urlparse(raw)
    if parsed.scheme.lower() not in {"http", "https"}:
        return None
    if not parsed.netloc or any(ch.isspace() for ch in parsed.netloc):
        return None

    # Reject credential-bearing URLs and malformed host labels.
    if parsed.username or parsed.password:
        return None
    host = (parsed.hostname or "").strip().lower()
    if not host or ".." in host or host.startswith(".") or host.endswith("."):
        return None

    normalized = ParseResult(
        scheme=parsed.scheme.lower(),
        netloc=parsed.netloc,
        path=parsed.path or "/",
        params="",
        query=parsed.query,
        fragment="",
    )
    return urlunparse(normalized)


def _normalize_source_label(item: dict) -> str | None:
    source = _clean_text(item.get("source"))
    if source:
        return source.lower().removeprefix("www.")

    raw_url = _sanitize_http_url(item.get("url"))
    if not raw_url:
        return None

    parsed = urlparse(raw_url)
    return parsed.netloc.lower().removeprefix("www.") or None


def _dedupe_results(results: list[dict]) -> list[dict]:
    deduped: list[dict] = []
    seen: set[tuple[str, str]] = set()

    for item in results:
        raw_url = _clean_text(item.get("url"))
        title = _clean_text(item.get("title"))
        if not raw_url or not title:
            continue

        key = (_normalized_url_key(raw_url), title.lower())
        if key in seen:
            continue

        seen.add(key)
        deduped.append(item)

    return deduped


def build_follow_up_queries(query: str, meaning_groups: list[dict], sources: list[dict]) -> list[str]:
    suggestions: list[str] = []
    normalized_query = _clean_text(query)

    label_templates = {
        "programming": [
            "{query} language design tradeoffs",
            "{query} implementation details",
        ],
        "planet": [
            "{query} latest planetary research",
            "{query} orbital observations",
        ],
        "mythology": [
            "{query} primary mythology sources",
            "{query} historical interpretations",
        ],
        "element": [
            "{query} safety and toxicity evidence",
            "{query} industrial applications",
        ],
        "company": [
            "{query} business model analysis",
            "{query} recent regulatory developments",
        ],
        "supercomputer": [
            "{query} benchmark comparisons",
            "{query} architecture details",
        ],
        "car": [
            "{query} reliability and safety reports",
            "{query} total cost of ownership",
        ],
        "film": [
            "{query} critical reception evidence",
            "{query} production background",
        ],
        "genus": [
            "{query} habitat and conservation status",
            "{query} taxonomy updates",
        ],
    }

    for group in meaning_groups[:3]:
        meaning = _clean_text(group.get("meaning"))
        meaning_key = meaning.lower()
        if meaning and meaning_key not in {"other", "overview", "main topic"}:
            templates = label_templates.get(meaning_key)
            if templates:
                suggestions.extend(template.format(query=normalized_query) for template in templates)
            else:
                suggestions.append(f"{normalized_query} {meaning} latest evidence")

    if not suggestions:
        suggestions.extend(
            [
                f"{normalized_query} key statistics",
                f"{normalized_query} expert analysis",
            ]
        )

    unique_suggestions: list[str] = []
    seen: set[str] = set()
    for item in suggestions:
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        unique_suggestions.append(item)
        if len(unique_suggestions) >= 5:
            break

    if not unique_suggestions and sources:
        unique_suggestions = [f"{normalized_query} recent updates"]

    return unique_suggestions


def _build_limitations(
    query: str,
    source_count: int,
    extracted_count: int,
    key_findings: list[str],
) -> list[str]:
    limitations: list[str] = []

    if source_count == 0:
        limitations.append(f"No high-confidence sources passed filtering for '{query}'.")
    if extracted_count == 0 and source_count > 0:
        limitations.append("Detailed extraction was unavailable for the returned sources.")
    if source_count < 3 and source_count > 0:
        limitations.append("Source coverage is limited; findings may not represent all perspectives.")
    if not key_findings:
        limitations.append("Structured key findings are limited due to sparse or noisy source content.")

    return limitations


def _confidence_label(source_count: int, extracted_count: int, key_finding_count: int) -> str:
    if source_count >= 6 and extracted_count >= 3 and key_finding_count >= 4:
        return "high"
    if source_count >= 3 and key_finding_count >= 2:
        return "medium"
    return "low"


def build_research_results(results: list[dict]) -> list[dict]:
    """Build frontend-safe research result cards from raw search results."""
    deduped = _dedupe_results(results)

    return [
        {
            "title": _clean_text(item.get("title")),
            "url": sanitized_url,
            "snippet": _clean_text(item.get("snippet")) or None,
            "source": _normalize_source_label(item),
            "score": item.get("score"),
            "rerank_score": item.get("rerank_score"),
            "published_date": item.get("published_date"),
            "favicon": item.get("favicon"),
        }
        for item in deduped
        for sanitized_url in [_sanitize_http_url(item.get("url"))]
        if sanitized_url
        if is_good_result_for_extraction(item)
    ]


def _build_structured_sections(
    query: str,
    summary_clean: str,
    summary_points: list[str],
    summary_markdown: str,
    clean_results: list[dict],
    extracted_count: int,
    meaning_groups: list[dict],
) -> dict:
    detailed_analysis = summary_markdown.strip()
    if not detailed_analysis and summary_points:
        detailed_analysis = "\n".join(f"- {point}" for point in summary_points)
    if not detailed_analysis:
        detailed_analysis = summary_clean

    source_items = [
        {
            "title": item["title"],
            "url": item["url"],
            "source": item.get("source"),
            "snippet": item.get("snippet"),
            "score": item.get("score"),
            "published_date": item.get("published_date"),
        }
        for item in clean_results[:8]
    ]

    limitations = _build_limitations(
        query=query,
        source_count=len(clean_results),
        extracted_count=extracted_count,
        key_findings=summary_points,
    )

    return {
        "concise_summary": summary_clean,
        "key_findings": summary_points,
        "detailed_analysis": detailed_analysis,
        "sources": source_items,
        "limitations": limitations,
        "suggested_follow_up_queries": build_follow_up_queries(query, meaning_groups, source_items),
        "confidence": _confidence_label(len(clean_results), extracted_count, len(summary_points)),
    }


def build_research_response_payload(
    result: dict,
    summary_clean: str,
    summary_points: list[str],
    summary_markdown: str,
) -> dict:
    """Build API response payload for the /research endpoint."""
    clean_results = build_research_results(result["results"])
    meaning_groups = result.get("meaning_groups", [])

    sections = _build_structured_sections(
        query=result["query"],
        summary_clean=summary_clean,
        summary_points=summary_points,
        summary_markdown=summary_markdown,
        clean_results=clean_results,
        extracted_count=result.get("extracted_count", 0),
        meaning_groups=meaning_groups,
    )

    return {
        "query": result["query"],
        "topic": result["topic"],
        "provider": result["provider"],
        "summary": summary_clean,
        "summary_points": summary_points,
        "summary_markdown": summary_markdown,
        "results": clean_results,
        "selected_sources": result.get("selected_sources", []),
        "source_count": len(clean_results),
        "extracted_count": result["extracted_count"],
        "ambiguous": result.get("ambiguous", False),
        "sections": sections,
        "meaning_groups": meaning_groups,
        "request_id": result.get("request_id"),
        "response_time": result.get("response_time"),
        "usage": result.get("usage"),
    }
