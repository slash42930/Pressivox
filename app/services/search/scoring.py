"""Scoring and ranking logic for search results."""

import re
from datetime import datetime, timezone

from .text_processing import host_root, normalize_text, query_terms
from .title_analysis import (
    extract_comma_meaning,
    extract_parenthetical_meaning,
    is_exact_base_topic,
)


TRUSTED_GENERAL = {
    "wikipedia.org": 12,
    "simple.wikipedia.org": 10,
    "britannica.com": 16,
    "nationalgeographic.com": 14,
    "smithsonianmag.com": 12,
    "nasa.gov": 18,
}

TRUST_SCORE_BY_DOMAIN = {
    "reuters.com": 22,
    "apnews.com": 21,
    "bbc.com": 20,
    "npr.org": 18,
    "pbs.org": 18,
    "wsj.com": 19,
    "nytimes.com": 18,
    "washingtonpost.com": 17,
    "ft.com": 19,
    "economist.com": 19,
    "bloomberg.com": 19,
    "cnbc.com": 16,
    "forbes.com": 14,
    "theguardian.com": 16,
    "nature.com": 22,
    "science.org": 22,
    "nejm.org": 22,
    "thelancet.com": 22,
    "who.int": 21,
    "cdc.gov": 21,
    "worldbank.org": 20,
    "imf.org": 20,
    "oecd.org": 19,
    "un.org": 18,
    "wikipedia.org": 14,
    "britannica.com": 18,
    "nasa.gov": 21,
    "mit.edu": 20,
    "stanford.edu": 20,
    "harvard.edu": 20,
    "ox.ac.uk": 20,
    "cam.ac.uk": 20,
}

TOPIC_DOMAIN_HINTS = {
    "news": {
        "reuters.com",
        "apnews.com",
        "bbc.com",
        "nytimes.com",
        "washingtonpost.com",
        "theguardian.com",
        "france24.com",
        "dw.com",
    },
    "general": {
        "wikipedia.org",
        "britannica.com",
        "smithsonianmag.com",
        "nationalgeographic.com",
        "bbc.com",
        "reuters.com",
    },
}

QUERY_INTENT_HINTS = {
    "football": {"bbc.com", "espn.com", "uefa.com", "fifa.com", "theathletic.com", "goal.com"},
    "soccer": {"bbc.com", "espn.com", "uefa.com", "fifa.com", "theathletic.com", "goal.com"},
    "animal": {"nationalgeographic.com", "worldwildlife.org", "iucn.org", "animalplanet.com"},
    "animals": {"nationalgeographic.com", "worldwildlife.org", "iucn.org", "animalplanet.com"},
    "economy": {"ft.com", "economist.com", "wsj.com", "bloomberg.com", "imf.org", "worldbank.org"},
    "finance": {"ft.com", "economist.com", "wsj.com", "bloomberg.com", "imf.org", "worldbank.org"},
    "inflation": {"ft.com", "economist.com", "wsj.com", "bloomberg.com", "imf.org", "oecd.org"},
    "ai": {"openai.com", "mit.edu", "stanford.edu", "nature.com", "science.org"},
    "health": {"who.int", "cdc.gov", "nejm.org", "thelancet.com", "nature.com"},
}

TOPIC_SCORE_WEIGHTS = {
    "general": {
        "provider": 1.0,
        "domain_bonus": 1.0,
        "trust": 1.0,
        "topic_relevance": 1.0,
        "content": 1.0,
        "freshness": 0.4,
        "title_match": 1.1,
        "title_shape": 1.0,
        "bad_page": 1.0,
        "specificity": 1.0,
        "side_topic": 1.0,
        "commercial": 1.0,
        "non_english_wikipedia": 1.0,
    },
    "news": {
        "provider": 1.0,
        "domain_bonus": 0.8,
        "trust": 1.35,
        "topic_relevance": 1.45,
        "content": 1.4,
        "freshness": 1.9,
        "title_match": 1.2,
        "title_shape": 0.6,
        "bad_page": 1.0,
        "specificity": 0.7,
        "side_topic": 1.0,
        "commercial": 1.1,
        "non_english_wikipedia": 0.8,
    },
}


def get_topic_weights(topic: str) -> dict[str, float]:
    """Return score weighting profile for the given topic."""
    key = (topic or "").strip().lower()
    return TOPIC_SCORE_WEIGHTS.get(key, TOPIC_SCORE_WEIGHTS["general"])


def smart_select_domains(query: str, topic: str, top_n: int = 50) -> list[str]:
    """Infer a trusted+relevant include-domain list for the given topic/query."""
    topic_key = (topic or "").strip().lower()
    terms = query_terms(query)

    candidates: set[str] = set(TRUSTED_GENERAL) | set(TRUST_SCORE_BY_DOMAIN)
    for domains in TOPIC_DOMAIN_HINTS.values():
        candidates.update(domains)
    for domains in QUERY_INTENT_HINTS.values():
        candidates.update(domains)

    ranked: list[tuple[str, float]] = []
    for domain in candidates:
        score = float(TRUST_SCORE_BY_DOMAIN.get(domain, 0))
        score += float(TRUSTED_GENERAL.get(domain, 0)) * 0.6

        if topic_key in TOPIC_DOMAIN_HINTS and domain in TOPIC_DOMAIN_HINTS[topic_key]:
            score += 14.0

        for term in terms:
            if domain in QUERY_INTENT_HINTS.get(term, set()):
                score += 7.0

        if term_related_domain(term=topic_key, domain=domain):
            score += 3.0

        ranked.append((domain, score))

    ranked.sort(key=lambda x: (x[1], x[0]), reverse=True)
    return [domain for domain, _ in ranked[:top_n]]


def term_related_domain(term: str, domain: str) -> bool:
    """Return whether a topic term appears in a domain token."""
    if not term:
        return False
    root_token = domain.split(".")[0].lower()
    return term in root_token or root_token in term


def domain_bonus(topic: str, source: str) -> int:
    """Calculate domain trust bonus based on source."""
    del topic  # current project only needs one trust map for this use-case

    root = host_root(source)
    for domain, bonus in TRUSTED_GENERAL.items():
        if root == domain or root.endswith(f".{domain}"):
            return bonus
    return 0


def domain_trust_score(source: str) -> int:
    """Return trustworthiness score based on known domain quality."""
    root = host_root(source)
    for domain, score in TRUST_SCORE_BY_DOMAIN.items():
        if root == domain or root.endswith(f".{domain}"):
            return score
    return 0


def topical_domain_relevance(topic: str, query: str, source: str) -> int:
    """Boost results whose source domain is relevant to topic and query intent."""
    score = 0
    root = host_root(source)

    topic_key = (topic or "").strip().lower()
    if topic_key in TOPIC_DOMAIN_HINTS:
        for domain in TOPIC_DOMAIN_HINTS[topic_key]:
            if root == domain or root.endswith(f".{domain}"):
                score += 12
                break

    for term in query_terms(query):
        for domain in QUERY_INTENT_HINTS.get(term, set()):
            if root == domain or root.endswith(f".{domain}"):
                score += 6
                break

    return score


def content_relevance_score(query: str, item: dict) -> int:
    """Score relevance using title/snippet overlap with query terms."""
    query_list = query_terms(query)
    if not query_list:
        return 0

    title_text = normalize_text(item.get("title", ""))
    snippet_text = normalize_text(item.get("snippet", ""))

    title_hits = sum(1 for term in query_list if term in title_text)
    snippet_hits = sum(1 for term in query_list if term in snippet_text)

    return title_hits * 5 + snippet_hits * 2


def parse_published_datetime(value: str | None) -> datetime | None:
    """Safely parse published date string into UTC datetime."""
    if not value:
        return None

    raw = value.strip()
    if not raw:
        return None

    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def freshness_score(topic: str, item: dict) -> int:
    """Reward freshness for news-like topics, mild penalty for stale pages."""
    if (topic or "").strip().lower() != "news":
        return 0

    published = parse_published_datetime(item.get("published_date"))
    if not published:
        return 0

    now = datetime.now(timezone.utc)
    age_days = max(0.0, (now - published).total_seconds() / 86400.0)

    if age_days <= 1:
        return 9
    if age_days <= 7:
        return 6
    if age_days <= 30:
        return 3
    if age_days > 365:
        return -4
    return 0


def non_english_wikipedia_penalty(source: str) -> int:
    """Penalize non-English Wikipedia sources."""
    host = (source or "").lower()
    if host.endswith(".wikipedia.org") and host not in {"en.wikipedia.org", "simple.wikipedia.org"}:
        return 18
    return 0


def bad_page_penalty(item: dict) -> int:
    """Calculate penalty for low-quality page types."""
    url = (item.get("url") or "").lower()
    title = (item.get("title") or "").lower()

    penalties = {
        "/category:": 40,
        "/wiki/category:": 40,
        "category:": 35,
        "glossary": 30,
        "list of ": 30,
        "outline of ": 28,
        "portal:": 40,
        "/portal:": 40,
        "template:": 35,
        "disambiguation": 22,
        "file:": 35,
        "/wiki/file:": 35,
        "wiktionary": 30,
    }

    score = 0
    for pattern, penalty in penalties.items():
        if pattern in url or pattern in title:
            score += penalty

    return score


def title_shape_bonus(query: str, title: str) -> int:
    """Reward titles that are likely to be canonical meanings."""
    bonus = 0

    if is_exact_base_topic(query, title):
        bonus += 42

    if extract_parenthetical_meaning(title):
        bonus += 34

    if extract_comma_meaning(title, query):
        bonus += 28

    query_norm = normalize_text(query)
    title_norm = normalize_text(title)

    if query_norm and title_norm.startswith(query_norm):
        bonus += 8

    return bonus


def title_match_bonus(query: str, title: str) -> int:
    """Calculate bonus for title matching query."""
    query_norm = normalize_text(query)
    title_norm = normalize_text(title)

    if not query_norm or not title_norm:
        return 0

    bonus = 0

    if title_norm == query_norm:
        bonus += 20

    if query_norm in title_norm:
        bonus += 10

    query_terms_list = query_terms(query)
    if query_terms_list:
        overlap = sum(1 for term in query_terms_list if term in title_norm)
        bonus += overlap * 6

        if overlap == len(query_terms_list):
            bonus += 8

    return bonus


def specificity_penalty(query: str, title: str) -> int:
    """Penalize overly specific titles."""
    query_terms_list = query_terms(query)
    title_terms_list = query_terms(title)

    if not query_terms_list or not title_terms_list:
        return 0

    overlap = sum(1 for term in query_terms_list if term in title_terms_list)
    extra_terms = max(len(title_terms_list) - overlap, 0)

    if len(query_terms_list) <= 2 and overlap >= 1 and extra_terms >= 2:
        return 12

    return 0


def side_topic_penalty(query: str, title: str) -> int:
    """Penalize obvious side topics such as 'X in location'."""
    query_norm = normalize_text(query)
    title_raw = title or ""
    title_norm = normalize_text(title)

    if not query_norm or not title_norm:
        return 0

    if title_norm == query_norm:
        return 0

    penalty = 0

    if re.search(rf"\b{re.escape(query_norm)}\b\s+in\s+", title_norm):
        penalty += 35

    if re.search(rf"\b{re.escape(query_norm)}\b\s*\(", title_raw, flags=re.IGNORECASE):
        penalty -= 12

    return penalty


def commercial_page_penalty(query: str, item: dict) -> int:
    """Penalize commercial/product/insurance pages for short ambiguous queries."""
    title = (item.get("title") or "").lower()
    snippet = (item.get("snippet") or "").lower()
    url = (item.get("url") or "").lower()

    query_terms_list = query_terms(query)
    is_short_query = len(query_terms_list) <= 2

    if not is_short_query:
        return 0

    text = f"{title} {snippet} {url}"

    hard_penalty_terms = [
        "insurance",
        "policyholders",
        "underwriting",
        "claims",
        "coverage",
        "quote",
        "get a quote",
        "auto insurance",
        "homeowners insurance",
        "login",
        "sign in",
        "pricing",
        "shop",
        "buy now",
    ]

    medium_penalty_terms = [
        "investor relations",
        "cookie policy",
        "privacy policy",
        "terms of service",
        "product",
        "store",
    ]

    penalty = 0

    for term in hard_penalty_terms:
        if term in text:
            penalty += 35

    for term in medium_penalty_terms:
        if term in text:
            penalty += 18

    return penalty


def rerank_results(query: str, topic: str, results: list[dict]) -> list[dict]:
    """Rerank search results based on scoring criteria."""
    reranked = []
    weights = get_topic_weights(topic)

    for item in results:
        provider_score = float(item.get("score") or 0.0)
        title = item.get("title", "")
        source = item.get("source", "")

        final_score = (
            (provider_score * 100 * weights["provider"])
            + (domain_bonus(topic, source) * weights["domain_bonus"])
            + (domain_trust_score(source) * weights["trust"])
            + (topical_domain_relevance(topic, query, source) * weights["topic_relevance"])
            + (content_relevance_score(query, item) * weights["content"])
            + (freshness_score(topic, item) * weights["freshness"])
            + (title_match_bonus(query, title) * weights["title_match"])
            + (title_shape_bonus(query, title) * weights["title_shape"])
            - (bad_page_penalty(item) * weights["bad_page"])
            - (specificity_penalty(query, title) * weights["specificity"])
            - (side_topic_penalty(query, title) * weights["side_topic"])
            - (commercial_page_penalty(query, item) * weights["commercial"])
            - (non_english_wikipedia_penalty(source) * weights["non_english_wikipedia"])
        )

        new_item = dict(item)
        new_item["rerank_score"] = round(final_score, 3)
        reranked.append(new_item)

    reranked.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)
    return reranked