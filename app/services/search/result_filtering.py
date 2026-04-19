"""Result filtering and grouping logic."""

import re
from collections import defaultdict

from .text_processing import normalize_text, query_terms, strip_source_suffix
from .title_analysis import (
    extract_comma_meaning,
    extract_parenthetical_meaning,
    is_exact_base_topic,
)


LABEL_MUSIC = "Music label"
LABEL_PROGRAMMING = "Programming"
TERM_PROGRAMMING_LANGUAGE = "programming language"
TERM_RECORD_LABEL = "record label"


NON_PRIMARY_PATTERNS = [
    r"\bin\s+the\s+united\s+states\b",
    r"\bin\s+[A-Z][a-z]+\b",
    r"\bisland\b",
    r"\briver\b",
    r"\bmountain\b",
    r"\balbum\b",
    r"\bfilm\b",
    r"\bsong\b",
    r"\bbook\b",
    r"\bnovel\b",
    r"\bmagazine\b",
    r"\bfederation\b",
    r"\bclub\b",
    r"\bseries\b",
    r"\bstore\b",
    r"\bprime\b",
    r"\bstudios\b",
]

PROGRAMMING_KEYWORDS = {
    TERM_PROGRAMMING_LANGUAGE,
    "python language",
    "interpreter",
    "cpython",
    "python software foundation",
    "python use",
    "guido van rossum",
}

PLANET_KEYWORDS = {
    "planet",
    "solar system",
    "orbit",
    "gravity",
    "messenger spacecraft",
    "bepicolombo",
    "mariner 10",
}

MOON_KEYWORDS = {
    "moon",
    "largest moon of saturn",
    "saturn",
    "ringed planet",
    "natural satellite",
}

MYTHOLOGY_KEYWORDS = {
    "mythology",
    "roman god",
    "greek god",
    "deity", 
    "pantheon",
    "titans",
    "gaia",
    "uranus",
    "commerce",
    "aztec",
    "warrior",
    "warriors",
    "ocelotl",
}

ELEMENT_KEYWORDS = {
    "chemical element",
    "atomic number",
    "quicksilver",
    "symbol hg",
    "periodic table",
}

COMPANY_KEYWORDS = {
    "fintech",
    "banking services",
    "business account",
    "startup banking",
    "mercury bank",
    "banking for startups",
}

SUPERCOMPUTER_KEYWORDS = {
    "supercomputer",
    "olcf-3",
    "oak ridge",
    "cray",
    "graphics processing units",
}

CAR_KEYWORDS = {
    "cars",
    "automobile",
    "automaker",
    "luxury vehicle",
    "luxury car",
    "jaguar cars",
    "jaguar land rover",
    "sedan",
    "suv",
    "vehicle brand",
}

FILM_KEYWORDS = {
    "film",
    "thriller film",
    "directed by",
    "screenplay",
    "starring",
}

GENUS_KEYWORDS = {
    "genus",
    "pythonidae",
    "snake",
    "snakes",
    "nonvenomous",
    "panthera",
}

DISAMBIGUATION_SNIPPET_MARKERS = {
    "may refer to",
    "most commonly refers to",
    "can refer to",
    "see also",
    "wikimedia foundation",
    "powered by mediawiki",
}


def _looks_like_disambiguation_snippet(snippet: str) -> bool:
    lowered = (snippet or "").lower()
    if not lowered:
        return False
    if any(marker in lowered for marker in DISAMBIGUATION_SNIPPET_MARKERS):
        return True
    if lowered.count("##") >= 2:
        return True
    if lowered.count(",") >= 14 and lowered.count(".") <= 2:
        return True
    return False


def _is_low_quality_source(source: str, url: str) -> bool:
    source = (source or "").lower()
    url = (url or "").lower()
    low_quality_tokens = ["test", "sandbox", "staging", "dev."]
    return any(token in source or token in url for token in low_quality_tokens)


def _normalize_meaning_label(label: str) -> str:
    normalized = (label or "").strip().lower()
    mapping = {
        "main topic": "Overview",
        "overview": "Overview",
        TERM_RECORD_LABEL: LABEL_MUSIC,
        "music label": LABEL_MUSIC,
        TERM_PROGRAMMING_LANGUAGE: LABEL_PROGRAMMING,
    }
    if normalized in mapping:
        return mapping[normalized]
    return label.strip().title() if label.strip() else "Other"


def is_good_result_for_extraction(item: dict) -> bool:
    """Check if result is suitable for content extraction."""
    url = (item.get("url") or "").lower()
    title = (item.get("title") or "").lower()
    snippet = (item.get("snippet") or "").lower()
    source = (item.get("source") or "").lower()

    blocked_patterns = [
        "/category:",
        "/wiki/category:",
        "glossary",
        "list of ",
        "outline of ",
        "portal:",
        "template:",
        "disambiguation",
        "file:",
        "/wiki/file:",
        "may refer to",
        "wiktionary",
    ]

    blocked_low_value_pages = [
        "privacy policy",
        "terms of service",
        "cookie policy",
        "investor relations",
        "claims process",
        "coverage details",
        "underwriting",
        "policyholders",
        "umbrella insurance",
        "auto insurance",
        "homeowners insurance",
        "get a quote",
        "sign in",
        "login",
    ]

    if any(pattern in url or pattern in title for pattern in blocked_patterns):
        return False

    if any(pattern in url or pattern in title or pattern in snippet for pattern in blocked_low_value_pages):
        return False

    if _is_low_quality_source(source, url):
        return False

    if _looks_like_disambiguation_snippet(snippet):
        return False

    if len(re.sub(r"\s+", " ", snippet).strip()) < 20:
        return False

    return True


def looks_like_related_not_alternate(query: str, title: str) -> bool:
    """Check if title appears to be a related topic, not an alternate meaning."""
    title_clean = strip_source_suffix(title)
    title_norm = normalize_text(title_clean)
    query_norm = normalize_text(query)
    query_terms_list = query_terms(query)

    if is_exact_base_topic(query, title_clean):
        return False

    if extract_parenthetical_meaning(title_clean):
        return False

    if extract_comma_meaning(title_clean, query):
        return False

    if re.search(rf"\b{re.escape(query_norm)}\b\s+in\s+", title_norm):
        return False

    for pattern in NON_PRIMARY_PATTERNS:
        if re.search(pattern, title_clean, flags=re.IGNORECASE):
            return True

    if query_norm and title_norm.startswith(query_norm):
        extra_words = len(title_norm.split()) - len(query_norm.split())
        if len(query_terms_list) <= 2 and extra_words >= 1:
            return True
        if extra_words >= 2:
            return True

    return False


def _keyword_label(title: str, snippet: str) -> str | None:
    text = f"{title} {snippet}".lower()

    def _contains_keyword(haystack: str, keyword: str) -> bool:
        token = keyword.strip().lower()
        if not token:
            return False

        # Single-word short tokens need exact word boundaries.
        if " " not in token and len(token) <= 5:
            return re.search(rf"\b{re.escape(token)}\b", haystack) is not None

        return token in haystack

    label_sets = [
        ("Car", CAR_KEYWORDS),
        ("Programming", PROGRAMMING_KEYWORDS),
        ("Planet", PLANET_KEYWORDS),
        ("Moon", MOON_KEYWORDS),
        ("Mythology", MYTHOLOGY_KEYWORDS),
        ("Element", ELEMENT_KEYWORDS),
        ("Company", COMPANY_KEYWORDS),
        ("Supercomputer", SUPERCOMPUTER_KEYWORDS),
        ("Film", FILM_KEYWORDS),
        ("Genus", GENUS_KEYWORDS),
    ]

    min_score_by_label = {
        "Car": 2,
        "Planet": 2,
        "Moon": 2,
        "Genus": 2,
        "Supercomputer": 2,
    }

    best_label = None
    best_score = 0

    for label, keywords in label_sets:
        score = sum(1 for kw in keywords if _contains_keyword(text, kw))
        if score > best_score:
            best_label = label
            best_score = score

    # Require stronger evidence for easy-to-confuse labels.
    required = min_score_by_label.get(best_label or "", 1)
    if best_label and best_score < required:
        return None

    if best_score >= 1:
        return best_label
    return None


def _result_selection_score(item: dict) -> tuple[int, float]:
    """Rank items by snippet quality first, then rerank score."""
    snippet = item.get("snippet") or ""
    badness = 0
    lowered = snippet.lower()

    if _looks_like_disambiguation_snippet(snippet):
        badness += 3
    if lowered.count("read edit view history") >= 1:
        badness += 2
    if lowered.count(",") >= 10 and lowered.count(".") <= 1:
        badness += 2

    score = float(item.get("rerank_score") or 0)
    return (-badness, score)


def derive_meaning_label(query: str, item: dict) -> str:
    """Derive a clearer meaning label for a result."""
    title = item.get("title", "") or ""
    snippet = item.get("snippet", "") or ""

    query_norm = normalize_text(query)
    title_clean = strip_source_suffix(title)
    title_norm = normalize_text(title_clean)
    combined = f"{title_clean} {snippet}".lower()

    if _looks_like_disambiguation_snippet(snippet):
        return "Other"

    if is_exact_base_topic(query, title_clean):
        inferred = _keyword_label(title_clean, snippet)
        return inferred or "Main topic"

    comma_label = extract_comma_meaning(title_clean, query)
    if comma_label:
        label_lower = comma_label.lower()

        if "programming language" in label_lower:
            return LABEL_PROGRAMMING
        if TERM_RECORD_LABEL in label_lower or "music label" in label_lower:
            return LABEL_MUSIC
        if "town" in label_lower or "city" in label_lower:
            return "Location"
        if "planet" in label_lower:
            return "Planet"
        if "moon" in label_lower:
            return "Moon"
        if "god" in label_lower or "deity" in label_lower or "mythology" in label_lower:
            return "Mythology"
        if "supercomputer" in label_lower:
            return "Supercomputer"
        if "car" in label_lower or "automobile" in label_lower or "vehicle" in label_lower:
            return "Car"
        if "film" in label_lower:
            return "Film"

        return _normalize_meaning_label(comma_label)

    parenthetical = extract_parenthetical_meaning(title_clean)
    if parenthetical:
        normalized = parenthetical.strip().lower()

        mapping = {
            "planet": "Planet",
            "mythology": "Mythology",
            TERM_PROGRAMMING_LANGUAGE: LABEL_PROGRAMMING,
            "genus": "Genus",
            "snake": "Genus",
            TERM_RECORD_LABEL: LABEL_MUSIC,
            "company": "Company",
            "town": "Location",
            "city": "Location",
            "chemical element": "Element",
            "element": "Element",
            "moon": "Moon",
            "supercomputer": "Supercomputer",
            "car": "Car",
            "cars": "Car",
            "automobile": "Car",
            "film": "Film",
        }
        return _normalize_meaning_label(mapping.get(normalized, parenthetical.title()))

    inferred = _keyword_label(title_clean, snippet)
    if inferred:
        return _normalize_meaning_label(inferred)

    if "town" in combined or "city" in combined or "population" in combined or "census" in combined:
        return "Location"

    if "insurance" in combined or "policyholders" in combined or "underwriting" in combined:
        return "Commercial"

    # Only trust geospatial pattern matches if they contain clear location nouns.
    patterns = [
        rf"^{re.escape(query_norm)}\s+in\s+(.+)$",
        rf"^(.+)\s+{re.escape(query_norm)}$",
        rf"^{re.escape(query_norm)}\s+(.+)$",
    ]

    for pattern in patterns:
        match = re.match(pattern, title_norm)
        if match:
            label = match.group(1).strip()
            if label:
                label_low = label.lower()
                if any(token in label_low for token in {"city", "town", "county", "state", "province", "island", "river", "mountain"}):
                    return "Location"

                if re.search(r"\b(born|died|singer|actor|author|musician|scientist)\b", combined):
                    return "Person"

    source = item.get("source")
    if source:
        return f"Other ({source})"
    return "Other"


def group_results_by_meaning(query: str, results: list[dict]) -> list[dict]:
    """Group results by their meaning/interpretation."""
    groups: dict[str, list[dict]] = defaultdict(list)

    for item in results:
        if not is_good_result_for_extraction(item):
            continue

        if looks_like_related_not_alternate(query, item.get("title", "")):
            continue

        label = derive_meaning_label(query, item)
        groups[label].append(item)

    grouped_list = []
    for label, items in groups.items():
        items = sorted(items, key=_result_selection_score, reverse=True)
        grouped_list.append(
            {
                "meaning": label,
                "top_score": items[0].get("rerank_score", 0),
                "results": [
                    {
                        "title": item["title"],
                        "url": item["url"],
                        "source": item.get("source"),
                        "score": item.get("score"),
                        "rerank_score": item.get("rerank_score"),
                        "snippet": item.get("snippet"),
                        "favicon": item.get("favicon"),
                    }
                    for item in items[:3]
                ],
            }
        )

    grouped_list.sort(key=lambda x: x["top_score"], reverse=True)
    return grouped_list


def primary_results_for_extraction(query: str, results: list[dict]) -> list[dict]:
    """Select primary results for extraction (non-ambiguous case)."""
    if not results:
        return []

    exact_matches = [
        item
        for item in results
        if is_good_result_for_extraction(item) and is_exact_base_topic(query, item.get("title", ""))
    ]

    if exact_matches:
        exact_matches.sort(
            key=lambda item: (
                0 if item.get("source") == "en.wikipedia.org" else 1,
                -float(item.get("rerank_score") or 0),
            )
        )
        return exact_matches[:1]

    top_score = float(results[0].get("rerank_score") or 0)
    if top_score <= 0:
        return []

    primary = []
    for item in results:
        if not is_good_result_for_extraction(item):
            continue

        if looks_like_related_not_alternate(query, item.get("title", "")):
            continue

        score = float(item.get("rerank_score") or 0)
        ratio = score / top_score if top_score else 0

        if ratio >= 0.82:
            primary.append(item)

    if primary:
        return primary[:2]

    fallback = [
        item
        for item in results
        if is_good_result_for_extraction(item)
        and not looks_like_related_not_alternate(query, item.get("title", ""))
    ]
    return fallback[:1]


def ambiguous_results_for_extraction(query: str, results: list[dict]) -> list[dict]:
    """Select best extractable representative from each meaning group."""
    groups = group_results_by_meaning(query, results)
    candidates = []

    for group in groups[:6]:
        group_results = group.get("results") or []
        if not group_results:
            continue

        chosen = None
        for item in group_results:
            if not is_good_result_for_extraction(item):
                continue
            if looks_like_related_not_alternate(query, item.get("title", "")):
                continue
            chosen = item
            break

        if chosen:
            candidates.append(chosen)

    return candidates[:6]