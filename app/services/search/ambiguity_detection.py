"""Ambiguity detection logic."""

from collections import Counter

from .result_filtering import (
    derive_meaning_label,
    is_good_result_for_extraction,
    looks_like_related_not_alternate,
)
from .title_analysis import title_shape


def count_distinct_meanings(query: str, results: list[dict]) -> int:
    """Count distinct meanings in top results."""
    labels: set[str] = set()

    for item in results[:8]:
        if not is_good_result_for_extraction(item):
            continue

        title = item.get("title", "")
        if looks_like_related_not_alternate(query, title):
            continue

        label = derive_meaning_label(query, item).lower().strip()
        if label and not label.startswith("other"):
            labels.add(label)

    return len(labels)


def detect_ambiguity(query: str, results: list[dict]) -> bool:
    """Detect if query results indicate an ambiguous query."""
    if len(results) < 2:
        return False

    top = float(results[0].get("rerank_score") or 0)
    second = float(results[1].get("rerank_score") or 0)

    if top <= 0:
        return False

    ratio = second / top
    distinct_meanings = count_distinct_meanings(query, results)

    title_shapes = [title_shape(query, item.get("title", "")) for item in results[:6]]
    shape_counts = Counter(title_shapes)

    exact_count = shape_counts.get("exact", 0)
    parenthetical_count = shape_counts.get("parenthetical", 0)
    comma_count = shape_counts.get("comma", 0)
    regional_count = shape_counts.get("regional", 0)

    if distinct_meanings >= 3:
        return True

    if ratio >= 0.78 and (parenthetical_count + comma_count + regional_count) >= 2:
        return True

    if exact_count >= 1 and ratio >= 0.72 and distinct_meanings >= 2:
        return True

    if parenthetical_count >= 2:
        return True

    return False