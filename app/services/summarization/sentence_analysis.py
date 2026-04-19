"""Sentence analysis and selection utilities."""

import re

from .text_cleaning import clean_text


def is_disambiguation_like(text: str) -> bool:
    """Check if text looks like a disambiguation page or a list of meanings."""
    low = clean_text(text).lower()
    if not low:
        return True

    strong_markers = [
        "may refer to",
        "most commonly refers to",
        "can refer to multiple things",
        "for other uses",
        "this article is about",
        "not to be confused with",
        "disambiguation",
        "list of ",
        "wiktionary",
    ]
    if any(marker in low for marker in strong_markers):
        return True

    if "## contents" in low:
        return True

    if low.count("may also refer to") >= 1:
        return True

    if low.count(",") >= 10:
        return True

    if low.count(";") >= 5:
        return True

    if low.count("(") >= 5 and low.count(")") >= 5:
        return True

    if "|" in low and low.count("|") >= 4:
        return True

    return False


def split_sentences(text: str) -> list[str]:
    """Split text into sentences."""
    cleaned = clean_text(text)
    if not cleaned:
        return []

    parts = re.split(r"(?<=[.!?])\s+", cleaned)
    sentences = []

    for part in parts:
        part = part.strip()
        if not part:
            continue

        if re.match(r"^[\d#\+\*\-]+", part):
            continue

        sentences.append(part)

    return sentences


def looks_like_good_summary_sentence(sentence: str, entity: str | None = None) -> bool:
    """Determine if a sentence is suitable for summary."""
    s = clean_text(sentence)
    low = s.lower()

    if len(s) < 35:
        return False

    if len(s) > 420:
        return False

    if is_disambiguation_like(s):
        return False

    if low.count("/") >= 3:
        return False

    if low.count("|") >= 1:
        return False

    if re.match(r"^[\d#\+\*\-]\s*[\d.]*\s*[#\+\*]*", s):
        return False

    if re.match(r"^[)\]\}\-\+\*#]+", s):
        return False

    if low.count(",") >= 7 and not re.search(r"\b(was|born|died|is|are|has|have)\b", low):
        return False

    if low.count("(") >= 3 and not re.search(r"\b(was|born|died|is|are|\d{4})\b", low):
        return False

    bad_phrases = [
        "former range",
        "equatorial rotation velocity",
        "coat of arms",
        "location within",
        "location of",
        "summary licensing",
        "file history",
        "logo",
        "see also",
        "citation needed",
        "simple english",
        "low saxon",
        "wiktionary",
        "may refer to",
        "most commonly refers to",
        "## contents",
    ]
    if any(phrase in low for phrase in bad_phrases):
        return False

    if re.search(r"\b\d{4}\b.*\b\d{4}\b.*\b\d{4}\b", s):
        return False

    good_verbs = r"\b(is|was|are|were|refers to|has|have|lived|became|known as|named after)\b"
    if re.search(good_verbs, low):
        return True

    if entity and re.search(rf"\b{re.escape(entity.lower())}\b", low):
        return True

    return False


def pick_best_sentences(
    text: str,
    entity: str | None = None,
    max_sentences: int = 2,
    max_chars: int = 320,
) -> str:
    """Select best sentences from text."""
    sentences = split_sentences(text)
    if not sentences:
        return ""

    preferred = [s for s in sentences if looks_like_good_summary_sentence(s, entity=entity)]

    if not preferred:
        fallback_candidates = [
            s for s in sentences
            if len(s) >= 40 and not is_disambiguation_like(s) and "|" not in s
        ]
        preferred = fallback_candidates[:2]

    if not preferred:
        return ""

    selected: list[str] = []
    total = 0

    for sentence in preferred:
        extra = len(sentence) + (1 if selected else 0)
        if selected and total + extra > max_chars:
            break

        selected.append(sentence)
        total += extra

        if len(selected) >= max_sentences:
            break

    if not selected:
        first = preferred[0]
        if len(first) <= max_chars:
            return first
        shortened = first[:max_chars].rsplit(" ", 1)[0].strip()
        return f"{shortened}..." if shortened else first[:max_chars].strip() + "..."

    return " ".join(selected).strip()


def first_sentence(text: str) -> str:
    """Extract first sentence from text."""
    cleaned = clean_text(text)
    if not cleaned:
        return ""

    match = re.search(r"^[^.!?]+[.!?]", cleaned)
    if match:
        return match.group(0).strip()

    return cleaned


def truncate_at_sentence(text: str, max_chars: int = 220) -> str:
    """Truncate text at sentence boundary without cutting mid-word."""
    text = clean_text(text)

    if len(text) <= max_chars:
        return text

    candidate = text[:max_chars]
    matches = list(re.finditer(r"[.!?](?=\s|$)", candidate))
    if matches:
        return candidate[:matches[-1].end()].strip()

    last_space_idx = candidate.rfind(" ")
    if last_space_idx > max_chars // 2:
        return candidate[:last_space_idx].strip() + "..."

    return candidate.strip() + "..."