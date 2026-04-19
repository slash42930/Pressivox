"""Scoring and ranking logic for search results."""

import re

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


def domain_bonus(topic: str, source: str) -> int:
    """Calculate domain trust bonus based on source."""
    del topic  # current project only needs one trust map for this use-case

    root = host_root(source)
    for domain, bonus in TRUSTED_GENERAL.items():
        if root == domain or root.endswith(f".{domain}"):
            return bonus
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

    for item in results:
        provider_score = float(item.get("score") or 0.0)
        title = item.get("title", "")
        source = item.get("source", "")

        final_score = (
            provider_score * 100
            + domain_bonus(topic, source)
            + title_match_bonus(query, title)
            + title_shape_bonus(query, title)
            - bad_page_penalty(item)
            - specificity_penalty(query, title)
            - side_topic_penalty(query, title)
            - commercial_page_penalty(query, item)
            - non_english_wikipedia_penalty(source)
        )

        new_item = dict(item)
        new_item["rerank_score"] = round(final_score, 3)
        reranked.append(new_item)

    reranked.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)
    return reranked