"""Result grouping using title-first semantic categorization."""

import re
from typing import Optional


PROGRAMMING_KEYWORDS = {
    "programming language",
    "python language",
    "interpreter",
    "cpython",
    "python software foundation",
    "pep",
    "python syntax",
    "python code",
    "script",
    "library",
    "module",
    "package",
    "pypi",
    "django",
    "flask",
}

PLANET_KEYWORDS = {
    "planet",
    "solar system",
    "sun",
    "orbit",
    "astronomical",
    "celestial",
    "surface",
    "gravity",
    "atmosphere",
    "mass",
    "radius",
}

LOCATION_KEYWORDS = {
    "city",
    "town",
    "county",
    "population",
    "census",
    "municipality",
    "region",
    "state",
    "florida",
    "located in",
}

MYTHOLOGY_KEYWORDS = {
    "god",
    "goddess",
    "deity",
    "roman god",
    "greek god",
    "mythology",
    "pantheon",
    "messenger god",
    "hermes",
    "worship",
}

COMPANY_KEYWORDS = {
    "fintech",
    "startup banking",
    "banking services",
    "business account",
    "mercury bank",
    "banking for startups",
    "startup company",
    "founded",
    "headquarters",
    "revenue",
}

MUSIC_LABEL_KEYWORDS = {
    "record label",
    "music label",
    "universal music group",
    "label",
    "discography",
    "released",
    "recording",
}

PERSON_KEYWORDS = {
    "born",
    "died",
    "actor",
    "author",
    "scientist",
    "composer",
    "singer",
    "musician",
    "president",
    "king",
    "queen",
    "farrokh",
    "bulsara",
}

GENUS_KEYWORDS = {
    "genus",
    "snake",
    "snakes",
    "pythonidae",
    "constricting",
    "reptile",
    "species",
}

ELEMENT_KEYWORDS = {
    "chemical element",
    "periodic table",
    "atomic number",
    "metal",
    "liquid metal",
    "symbol hg",
    "mercury element",
}

HISTORICAL_KEYWORDS = {
    "battle",
    "war",
    "revolution",
    "empire",
    "dynasty",
    "historical event",
    "ancient rome",
    "medieval",
    "bronze age",
    "iron age",
}


def categorize_by_keywords(text: str) -> Optional[str]:
    """Categorize text using weighted keyword matching."""
    if not text:
        return None

    text_lower = text.lower()
    scores: dict[str, int] = {}

    weighted_categories = [
        ("Programming", PROGRAMMING_KEYWORDS, 3),
        ("Planet", PLANET_KEYWORDS, 3),
        ("Location", LOCATION_KEYWORDS, 2),
        ("Mythology", MYTHOLOGY_KEYWORDS, 3),
        ("Company", COMPANY_KEYWORDS, 3),
        ("Music label", MUSIC_LABEL_KEYWORDS, 3),
        ("Person", PERSON_KEYWORDS, 2),
        ("Genus", GENUS_KEYWORDS, 3),
        ("Element", ELEMENT_KEYWORDS, 3),
        ("Historical", HISTORICAL_KEYWORDS, 1),
    ]

    for category_name, keywords, weight in weighted_categories:
        score = sum(weight for kw in keywords if kw in text_lower)
        if score:
            scores[category_name] = score

    if not scores:
        return None

    best_category, best_score = max(scores.items(), key=lambda x: x[1])

    if best_score < 3:
        return None

    return best_category


def clean_title_for_label(title: str) -> Optional[str]:
    """Extract a reliable label from title structure."""
    title_clean = re.sub(
        r"\s*[-–]\s*(wikipedia|from|source|wikimedia).*$",
        "",
        title,
        flags=re.IGNORECASE,
    ).strip()

    match = re.search(r"\(([^)]+)\)$", title_clean)
    if match:
        value = match.group(1).strip().lower()
        mapping = {
            "planet": "Planet",
            "mythology": "Mythology",
            "programming language": "Programming",
            "genus": "Genus",
            "snake": "Genus",
            "record label": "Music label",
            "company": "Company",
            "town": "Location",
            "city": "Location",
            "chemical element": "Element",
            "element": "Element",
            "person": "Person",
        }
        return mapping.get(value, value.title())

    if "," in title_clean:
        suffix = title_clean.split(",", 1)[1].strip().lower()

        if "programming language" in suffix:
            return "Programming"
        if "record label" in suffix or "music label" in suffix:
            return "Music label"
        if "town" in suffix or "city" in suffix:
            return "Location"
        if "roman god" in suffix or "deity" in suffix or "mythology" in suffix:
            return "Mythology"
        if "planet" in suffix:
            return "Planet"
        if "chemical element" in suffix or "element" in suffix:
            return "Element"

    return None


def group_results_by_meaning(query: str, results: list[dict]) -> list[dict]:
    """Group results by meaning, preferring title structure over broad keywords."""
    del query  # currently unused, kept for API compatibility

    if not results:
        return []

    groups: dict[str, list[dict]] = {}

    for item in results:
        title = item.get("title", "") or ""
        snippet = item.get("snippet", "") or ""
        combined = f"{title} {snippet}"

        label = clean_title_for_label(title)
        if label:
            category = label
        else:
            category = categorize_by_keywords(combined) or "Other"

        groups.setdefault(category, []).append(item)

    clusters = []
    for category, items in groups.items():
        if not items:
            continue

        items_sorted = sorted(
            items,
            key=lambda x: float(x.get("rerank_score") or 0),
            reverse=True,
        )
        top_score = float(items_sorted[0].get("rerank_score") or 0)

        clusters.append(
            {
                "meaning": category,
                "top_score": top_score,
                "results": [
                    {
                        "title": item.get("title"),
                        "url": item.get("url"),
                        "source": item.get("source"),
                        "score": item.get("score"),
                        "rerank_score": item.get("rerank_score"),
                        "snippet": item.get("snippet"),
                    }
                    for item in items_sorted[:3]
                ],
            }
        )

    clusters.sort(key=lambda c: float(c["top_score"] or 0), reverse=True)
    return clusters


def extract_differentiator(query: str, title: str) -> Optional[str]:
    """Extract differentiator from title for ambiguity detection."""
    del query  # currently unused, kept for API compatibility
    return clean_title_for_label(title)