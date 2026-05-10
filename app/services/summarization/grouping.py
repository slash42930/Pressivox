"""Meaning-group selection helpers for summarization flows."""

from .text_cleaning import clean_text


def top_meaning_groups(
    meaning_groups: list[dict],
    limit: int = 5,
    min_non_other_for_prefer: int = 2,
) -> list[dict]:
    """Return top meaning groups, preferring non-'Other' labels when sufficient."""
    if not meaning_groups:
        return []

    sorted_groups = sorted(
        meaning_groups,
        key=lambda g: float(g.get("top_score") or 0),
        reverse=True,
    )

    non_other_groups = [
        g
        for g in sorted_groups
        if clean_text(g.get("meaning", "")).strip().lower() not in {"other", ""}
    ]

    if len(non_other_groups) >= min_non_other_for_prefer:
        return non_other_groups[:limit]
    return sorted_groups[:limit]
