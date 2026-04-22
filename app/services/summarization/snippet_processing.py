"""Snippet and document processing utilities."""

import re

from .sentence_analysis import (
    first_sentence,
    is_disambiguation_like,
    pick_best_sentences,
    truncate_at_sentence,
)
from .text_cleaning import (
    clean_text,
    remove_leading_title_echo,
    remove_meta_noise,
    remove_prefix_before_entity,
    strip_parenthetical_suffix,
)


def clean_summary_snippet(text: str, max_chars: int = 400, title: str | None = None, is_snippet: bool = True) -> str:
    """Clean and prepare a summary snippet from raw text.

    Args:
        text: Raw text to process
        max_chars: Maximum characters to return
        title: Title for context and cleaning
        is_snippet: If True, be lenient with search snippets. If False, stricter for extracted text.
    """
    text = re.sub(r"###\s*", "", text)
    text = re.sub(r"(?m)^#{1,6}\s*", "", text)
    text = re.sub(r"\s+#{2,6}\s+[A-Z][A-Za-z0-9'\- ]{1,80}", " ", text)
    text = re.sub(r"\bPowered\s+by\s+MediaWiki\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bWikimedia\s+Foundation\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"__(.+?)__", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"`{1,3}(.+?)`{1,3}", r"\1", text)
    text = re.sub(r"\{\{(.+?)\}\}", "", text)
    text = re.sub(r'\"Symbol\s*\)', "", text)

    cleaned = clean_text(text)

    if not cleaned:
        return ""

    if is_snippet:
        entity = strip_parenthetical_suffix(title or "")
        if title:
            cleaned = remove_leading_title_echo(cleaned, title)
        cleaned = remove_meta_noise(cleaned)
        if title:
            cleaned = remove_prefix_before_entity(cleaned, entity)
        return truncate_at_sentence(cleaned, max_chars=max_chars) if cleaned else ""

    entity = strip_parenthetical_suffix(title or "")
    if title:
        cleaned = remove_leading_title_echo(cleaned, title)
        cleaned = remove_prefix_before_entity(cleaned, entity)
    cleaned = remove_meta_noise(cleaned)
    if title:
        cleaned = remove_prefix_before_entity(cleaned, entity)

    if not cleaned or is_disambiguation_like(cleaned):
        return ""

    best = pick_best_sentences(cleaned, entity=entity, max_sentences=1, max_chars=max_chars)

    if not best:
        return truncate_at_sentence(cleaned, max_chars=max_chars)

    return truncate_at_sentence(best, max_chars=max_chars)


def build_doc_summary_piece(doc: dict, title: str, max_sentences: int = 2, max_chars: int = 650) -> str:
    """Build summary snippet from extracted document."""
    passages = doc.get("important_passages") or []
    raw_text = ""

    if passages:
        raw_text = " ".join(clean_text(p) for p in passages[:6])
    else:
        raw_text = clean_text(doc.get("extracted_text", ""))

    raw_text = remove_leading_title_echo(raw_text, title)
    raw_text = remove_prefix_before_entity(raw_text, strip_parenthetical_suffix(title))
    raw_text = remove_meta_noise(raw_text)
    raw_text = remove_prefix_before_entity(raw_text, strip_parenthetical_suffix(title))

    if not raw_text or is_disambiguation_like(raw_text):
        return ""

    entity = strip_parenthetical_suffix(title)
    summary = pick_best_sentences(
        raw_text,
        entity=entity,
        max_sentences=max_sentences,
        max_chars=max_chars,
    ).strip()

    if not summary or is_disambiguation_like(summary):
        return ""

    return truncate_at_sentence(summary, max_chars=max_chars)