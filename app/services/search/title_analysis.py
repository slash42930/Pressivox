"""Title analysis and shape detection logic."""
import re
from .text_processing import normalize_text, strip_source_suffix


def extract_parenthetical_meaning(title: str) -> str | None:
    """Extract meaning from parentheses in title (e.g., 'Word (meaning)')."""
    match = re.search(r"\(([^)]+)\)", title or "")
    if not match:
        return None
    return match.group(1).strip()


def extract_comma_meaning(title: str, query: str) -> str | None:
    """Extract meaning from comma in title (e.g., 'Word, meaning')."""
    title_clean = strip_source_suffix(title)
    match = re.match(rf"^{re.escape(query)}\s*,\s*(.+)$", title_clean, flags=re.IGNORECASE)
    if not match:
        return None
    return match.group(1).strip()


def is_exact_base_topic(query: str, title: str) -> bool:
    """Check if title is exactly the base topic."""
    return normalize_text(query) == normalize_text(strip_source_suffix(title))


def title_shape(query: str, title: str) -> str:
    """Classify the shape/structure of a title relative to the query."""
    query_norm = normalize_text(query)
    title_clean = strip_source_suffix(title)
    title_norm = normalize_text(title_clean)

    if not query_norm or not title_norm:
        return "other"

    if is_exact_base_topic(query, title_clean):
        return "exact"

    if extract_parenthetical_meaning(title_clean):
        return "parenthetical"

    if extract_comma_meaning(title_clean, query):
        return "comma"

    if re.search(rf"\b{re.escape(query_norm)}\b\s+in\s+", title_norm):
        return "regional"

    if query_norm in title_norm:
        return "contains"

    return "other"
