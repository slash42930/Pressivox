"""Text normalization and processing utilities for search."""
import re


def normalize_text(value: str) -> str:
    """Normalize text by removing punctuation and lowercasing."""
    return re.sub(r"[^a-z0-9\s]", " ", (value or "").lower()).strip()


def query_terms(query: str) -> list[str]:
    """Extract normalized query terms."""
    return [term for term in normalize_text(query).split() if term]


def host_root(source: str) -> str:
    """Extract root domain from source URL."""
    source = (source or "").lower()
    if source.startswith("www."):
        source = source[4:]
    return source


def strip_source_suffix(value: str) -> str:
    """Remove source suffixes like '- Wikipedia' from titles."""
    text = (value or "").strip()
    text = re.sub(r"\s*-\s*Wikipedia\s*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*-\s*Simple English Wikipedia.*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*-\s*Encyclop[a-z. ]*$", "", text, flags=re.IGNORECASE)
    return text.strip()
