"""Presentation helpers for search and research API responses."""

from urllib.parse import ParseResult, urlparse, urlunparse

from app.services.search.result_filtering import is_good_result_for_extraction
from app.services.search.scoring import content_relevance_score, domain_trust_score
from app.services.search.text_processing import query_terms


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


def _detect_query_domain(query: str) -> str:
    """Infer the broad domain of a query for follow-up question generation."""
    lowered = query.lower()
    terms = set(query_terms(query))

    ai_terms = {
        "artificial", "intelligence", "machine", "learning", "neural", "deep",
        "ai", "ml", "llm", "gpt", "nlp", "chatgpt", "generative", "algorithm",
        "automation", "robotics",
    }
    if terms & ai_terms or "artificial intelligence" in lowered:
        return "ai_technology"

    tech_terms = {
        "technology", "software", "hardware", "computer", "programming",
        "internet", "digital", "cyber", "blockchain", "quantum", "semiconductor",
    }
    if terms & tech_terms:
        return "technology"

    science_terms = {
        "science", "physics", "chemistry", "biology", "genetics", "quantum",
        "atom", "molecule", "evolution", "climate", "energy", "nuclear",
    }
    if terms & science_terms:
        return "science"

    medical_terms = {
        "health", "medicine", "disease", "cancer", "drug", "treatment",
        "therapy", "virus", "vaccine", "hospital", "patient", "symptom",
    }
    if terms & medical_terms:
        return "medicine"

    history_terms = {
        "history", "historical", "war", "ancient", "empire", "civilization",
        "century", "revolution", "dynasty", "medieval", "colonial",
    }
    if terms & history_terms:
        return "history"

    space_terms = {
        "space", "planet", "star", "galaxy", "nasa", "orbit", "solar",
        "moon", "mars", "astronomy", "telescope", "exoplanet", "comet",
    }
    if terms & space_terms:
        return "space"

    econ_terms = {
        "economy", "economics", "inflation", "gdp", "market", "finance",
        "bank", "investment", "stock", "trade", "recession", "monetary",
    }
    if terms & econ_terms:
        return "economics"

    env_terms = {
        "climate", "environment", "carbon", "emission", "renewable",
        "sustainability", "biodiversity", "ecosystem", "pollution",
    }
    if terms & env_terms:
        return "environment"

    return "general"


# Natural-language follow-up question templates keyed by domain.
# {query} is substituted with the normalized query at runtime.
_DOMAIN_FOLLOW_UP_TEMPLATES: dict[str, list[str]] = {
    "ai_technology": [
        "What are the main branches and types of {query}?",
        "How is {query} applied in healthcare, finance, and education?",
        "What are the current risks and ethical concerns surrounding {query}?",
        "What is the difference between narrow AI, AGI, and superintelligence?",
        "Which organizations are leading research in {query}?",
        "What are the most significant recent breakthroughs in {query}?",
    ],
    "technology": [
        "What are the core principles and components of {query}?",
        "How is {query} transforming industry today?",
        "What are the main advantages and limitations of {query}?",
        "How has {query} evolved over the past decade?",
        "What are the security and privacy implications of {query}?",
    ],
    "science": [
        "What are the fundamental principles behind {query}?",
        "What are the most significant recent discoveries in {query}?",
        "How does {query} affect everyday life and society?",
        "What are the open questions and frontiers in {query}?",
        "What practical applications have emerged from research on {query}?",
    ],
    "medicine": [
        "What are the most effective current treatments for {query}?",
        "What are the main risk factors and prevention strategies related to {query}?",
        "What does recent clinical research show about {query}?",
        "How is {query} diagnosed and monitored?",
        "What emerging therapies are being tested for {query}?",
    ],
    "history": [
        "What were the main causes and long-term consequences of {query}?",
        "How did {query} reshape the modern world?",
        "Who were the key figures involved in {query}?",
        "How do historians differ in their interpretations of {query}?",
        "What primary sources are most valuable for studying {query}?",
    ],
    "space": [
        "What are the latest scientific findings about {query}?",
        "Which missions have explored or studied {query}?",
        "How does {query} compare to similar objects or phenomena?",
        "What are the biggest unanswered questions about {query}?",
        "What instruments and methods are used to study {query}?",
    ],
    "economics": [
        "What are the main drivers of {query} in the current global economy?",
        "How does {query} affect different income groups and countries?",
        "What policies have been most effective at managing {query}?",
        "What do major institutions like the IMF and World Bank say about {query}?",
        "How has {query} changed over the past ten years?",
    ],
    "environment": [
        "What are the key causes and consequences of {query}?",
        "What scientific evidence exists on the scale of {query}?",
        "What policy and technological responses have been proposed for {query}?",
        "How does {query} affect biodiversity and ecosystems?",
        "What can individuals and governments do to address {query}?",
    ],
    "general": [
        "What is the definition and scope of {query}?",
        "What are the most important facts to know about {query}?",
        "What are the main perspectives or interpretations of {query}?",
        "How has our understanding of {query} changed over time?",
        "What are the practical implications of {query}?",
    ],
}


def build_follow_up_queries(query: str, meaning_groups: list[dict], sources: list[dict]) -> list[str]:
    """Build natural-language follow-up questions tailored to the query's domain.

    Produces human-readable questions rather than keyword-stuffed phrases,
    regardless of whether meaning groups are present.
    """
    normalized = _clean_text(query)
    if not normalized:
        return []

    domain = _detect_query_domain(normalized)
    templates = _DOMAIN_FOLLOW_UP_TEMPLATES.get(domain, _DOMAIN_FOLLOW_UP_TEMPLATES["general"])

    suggestions = [t.format(query=normalized) for t in templates[:5]]

    unique: list[str] = []
    seen: set[str] = set()
    for item in suggestions:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            unique.append(item)

    return unique[:5]



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


def _source_quality_score(item: dict) -> int:
    """Return a 0–100 quality score for a source based on domain trust."""
    source = item.get("source") or ""
    trust = domain_trust_score(source)
    # trust is typically 0–22; normalise to 0–100.
    return min(100, round((trust / 22) * 100))


def _source_relevance_score(query: str, item: dict) -> float:
    """Return a 0.0–1.0 relevance score for a source against the query."""
    raw = content_relevance_score(query, item)
    query_terms_list = query_terms(query)
    # Max possible raw score: len(query_terms)*5 (title) + len(query_terms)*2 (snippet)
    max_possible = max(1, len(query_terms_list) * 7)
    return round(min(1.0, raw / max_possible), 3)


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
            "quality_score": _source_quality_score(item),
            "relevance_score": _source_relevance_score(query, item),
        }
        for item in clean_results[:8]
    ]

    # Sort sources so highest quality + relevance appear first.
    source_items.sort(
        key=lambda s: (s["quality_score"], s["relevance_score"]),
        reverse=True,
    )


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
        "omitted_sources": [],
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
