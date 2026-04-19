"""Text cleaning and normalization utilities for summarization."""

import re


def clean_text(value: str) -> str:
    """Clean text by fixing encoding issues and normalizing whitespace."""
    replacements = {
        "\u00e2\u0080\u0099": "'",
        "\u00e2\u0080\u0098": "'",
        "\u00e2\u0080\u009c": '"',
        "\u00e2\u0080\u009d": '"',
        "\u00e2\u0080\u0093": "-",
        "\u00e2\u0080\u0094": "-",
        "\u00e2\u0080\u00a6": "...",
        "\u00c2": "",
        "\u00e2": "-",
    }

    cleaned = value or ""
    for bad, good in replacements.items():
        cleaned = cleaned.replace(bad, good)

    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def strip_source_suffix(value: str) -> str:
    """Remove source suffixes like '- Wikipedia' from titles."""
    text = clean_text(value)
    text = re.sub(r"\s*-\s*Wikipedia\s*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*-\s*Simple English Wikipedia.*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*-\s*Encyclop[a-z. ]*$", "", text, flags=re.IGNORECASE)
    return text.strip()


def strip_parenthetical_suffix(value: str) -> str:
    """Remove parenthetical suffixes from titles."""
    text = strip_source_suffix(value)
    text = re.sub(r"\s*\([^)]*\)\s*$", "", text).strip()
    return text


def remove_leading_title_echo(text: str, title: str) -> str:
    """Remove title echoed at the beginning of text."""
    cleaned_text = clean_text(text)
    cleaned_title = strip_source_suffix(title)

    if not cleaned_text or not cleaned_title:
        return cleaned_text

    patterns = [
        rf"^{re.escape(cleaned_title)}\s*:\s*",
        rf"^{re.escape(cleaned_title)}\s*-\s*",
        rf"^{re.escape(cleaned_title)}\s+",
    ]

    for pattern in patterns:
        cleaned_text = re.sub(pattern, "", cleaned_text, flags=re.IGNORECASE)

    return cleaned_text.strip()


def remove_reference_noise(text: str) -> str:
    """Remove reference markers like [1], [citation needed], etc."""
    text = re.sub(r"\[\s*\d+\s*\]", "", text)
    text = re.sub(r"\[\s*citation needed\s*\]", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\[\s*clarification needed\s*\]", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\[\s*note \d+\s*\]", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\[\s*update\s*\]", "", text, flags=re.IGNORECASE)
    return text


def remove_intro_noise(text: str) -> str:
    """Remove common introductory phrases from articles."""
    patterns = [
        r"^From Wikipedia, the free encyclopedia\s*",
        r"^From the free encyclopedia\s*",
        r"^Simple English Wikipedia, the free encyclopedia\s*",
        r"^Look up .*? in Wiktionary.*?[.!?]\s*",
        r"^This article is about .*?[.!?]\s*",
        r"^For other uses, see .*?[.!?]\s*",
        r"^For other uses of this term, see .*?[.!?]\s*",
        r"^For other .*?, see .*?[.!?]\s*",
        r"^Not to be confused with .*?[.!?]\s*",
        r"^[A-Z][A-Za-z\s,-]{0,80}\s+may refer to:\s*",
        r"^[A-Z][A-Za-z\s,-]{0,80}\s+most commonly refers to:\s*",
    ]

    cleaned = text
    for pattern in patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

    return cleaned.strip()


def remove_pronunciation_noise(text: str) -> str:
    """Remove pronunciation and language notation artifacts."""
    text = re.sub(r"\([^)]*ⓘ[^)]*\)", "", text)
    text = re.sub(r"\s*ⓘ\s*", " ", text)
    text = re.sub(r"\([^)]*pronounced[^)]*\)", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\([^)]*listen[^)]*\)", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\([^)]*\bIPA\b[^)]*\)", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\([^)]*\bUS\b:\s*/[^)]*\)", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\([^)]*\bUK\b:\s*/[^)]*\)", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\(\s*;\s*Latin:[^)]+\)", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\(\s*;\s*Greek:[^)]+\)", "", text, flags=re.IGNORECASE)
    return text


def dedupe_leading_phrase(text: str) -> str:
    """Remove duplicated leading phrases."""
    cleaned = clean_text(text)

    cleaned = re.sub(
        r"^([A-Z][a-z]+(?:\s+[a-z]+){0,4})\s+\1\b",
        r"\1",
        cleaned,
        flags=re.IGNORECASE,
    )

    return cleaned.strip()


def remove_metadata_like_prefix(text: str) -> str:
    """Remove metadata-like prefixes before main content."""
    cleaned = clean_text(text)
    if not cleaned:
        return ""

    if re.match(r"^[A-Z][A-Za-z0-9'()\-&, ]+\s+(is|was|are|were|refers to|can refer to)\b", cleaned):
        return cleaned

    patterns = [
        r"^(?:[A-Z][a-z]+(?:\s+[a-z]+){1,8})\s+([A-Z][A-Za-z0-9'()\-&, ]+\s+(?:is|was|are|were|refers to|can refer to)\b.*)$",
        r"^(?:[A-Z][a-z]+(?:\s+(?:of|from|for|and|the|to|in|on|with|by|at|an|a|[a-z]+)){1,10})\s+([A-Z][A-Za-z0-9'()\-&, ]+\s+(?:is|was|are|were|refers to|can refer to)\b.*)$",
    ]

    for pattern in patterns:
        match = re.match(pattern, cleaned)
        if match:
            candidate = match.group(1).strip()
            if len(candidate) >= 20:
                return candidate

    return cleaned


def remove_prefix_before_entity(text: str, entity: str) -> str:
    """Remove prefix before entity mention."""
    cleaned = clean_text(text)
    entity = clean_text(entity)

    if not cleaned or not entity:
        return cleaned

    idx = cleaned.lower().find(entity.lower())
    if idx > 0:
        prefix = cleaned[:idx].strip()
        suffix = cleaned[idx:].strip()

        if len(prefix) <= 90 and not re.search(r"[.!?]", prefix) and len(suffix) >= 20:
            return suffix

    return cleaned


def remove_meta_noise(text: str) -> str:
    """Remove all types of metadata and noise from text."""
    if not text:
        return ""

    text = clean_text(text)

    # Remove markdown emphasis but keep content
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"__([^_]+)__", r"\1", text)
    text = re.sub(r"_([^_]+)_", r"\1", text)
    text = re.sub(r"''([^']+)''", r"\1", text)

    # Remove markdown table rows and separators
    text = re.sub(r"\|(?:\s*[^|\n]+\s*\|){2,}", " ", text)
    text = re.sub(r"(?:\|\s*---+\s*){2,}\|?", " ", text)

    # Remove obvious wiki/logo/label artifacts
    text = re.sub(r"\bWiktionary logo\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bWikimedia Commons logo\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bDisambiguation icon\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bContents\b", "", text, flags=re.IGNORECASE)

    # Remove malformed quoted label artifacts
    text = re.sub(r'"\s*Symbol\s*"\)', "", text, flags=re.IGNORECASE)
    text = re.sub(r'"\s*MESSENGER\s*"\)', "", text, flags=re.IGNORECASE)
    text = re.sub(r'"\s*[A-Z][A-Za-z0-9 _-]{1,40}\s*"\)', "", text)

    # Remove malformed quoted-reference patterns
    text = re.sub(r'"([^"]+)"\("([^"]+)"\)', r"\1", text)
    text = re.sub(r'([A-Za-z0-9\s]+)\s+\("([^"]+)"\)', r"\1", text)
    text = re.sub(r'([A-Za-z0-9\s]+)\s+\([A-Za-z0-9\s&]+\)', r"\1", text)

    # Remove malformed parenthetical junk like (Mercury "Mercury")) or (Jaguar "Jaguar")
    text = re.sub(r"\(\s*[^()]{0,40}\"[^\"]{1,40}\"\s*\)\)?", "", text)

    # Remove stray closing parens after entity names like Mercury)
    text = re.sub(r"\b([A-Z][a-z]+)\)", r"\1", text)

    # Remove markdown/list/header fragments
    text = re.sub(r"^#+\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\+\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\*\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\d+\.\d+\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\#{1,6}", "", text, flags=re.MULTILINE)

    text = remove_intro_noise(text)
    text = remove_pronunciation_noise(text)
    text = remove_reference_noise(text)
    text = dedupe_leading_phrase(text)
    text = remove_metadata_like_prefix(text)

    text = re.sub(r"\*\s+[A-Z][^:]{0,80}\)", "", text)
    text = re.sub(r'".+?–.+?"\)', "", text)
    text = re.sub(r"\bSimple English\b[^.!?]*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bLow Saxon\b[^.!?]*", "", text, flags=re.IGNORECASE)

    # Clean leftover empty punctuation groups and spacing
    text = re.sub(r"\(\s*\)", "", text)
    text = re.sub(r"\[\s*\]", "", text)
    text = re.sub(r"\s+\)", ")", text)
    text = re.sub(r"\(\s+", "(", text)
    text = re.sub(r"\s+,", ",", text)
    text = re.sub(r"\s+;", ";", text)
    text = re.sub(r"\s{2,}", " ", text)

    return text.strip(" -:;,.")