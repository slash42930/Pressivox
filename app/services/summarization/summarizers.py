"""High-level summarization functions."""

import re

from .snippet_processing import build_doc_summary_piece, clean_summary_snippet
from .text_cleaning import clean_text, strip_source_suffix


NOISY_SNIPPET_MARKERS = {
    "from wikipedia, the free encyclopedia",
    "article talk read edit view history",
    "what links here",
    "related changes",
    "page information",
    "cite this page",
    "get shortened url",
    "print/export",
    "download as pdf",
    "wikidata item",
    "could refer to",
    "topics referred to by the same",
    "disambiguation pages should",
    "order by importance",
    "clicking on links",
}


def _looks_like_noisy_disambiguation_text(value: str) -> bool:
    """Return True if text looks like navigation/disambiguation boilerplate."""
    lowered = clean_text(value).lower()
    if not lowered:
        return False

    if any(marker in lowered for marker in NOISY_SNIPPET_MARKERS):
        return True

    if lowered.count("read edit view history") >= 1:
        return True

    discussion_markers = {
        "i've read that",
        "if a reader is browsing",
        "subject to disagreement",
        "reliable source for the order",
        "in this case we actually have",
    }
    if any(marker in lowered for marker in discussion_markers):
        return True

    words = re.findall(r"\b[a-z]{2,}\b", lowered)
    if len(words) >= 28 and lowered.count(".") <= 1 and lowered.count(",") <= 2:
        common_verbs = {"is", "are", "was", "were", "has", "have", "study", "used", "include"}
        verb_hits = sum(1 for w in words if w in common_verbs)
        if verb_hits <= 1:
            return True

    return False


def _is_contextless_other_body(query: str, point: str) -> bool:
    """Return True when an Other point is generic/meta and not useful for the query."""
    if ":" not in point:
        return False

    label, body = point.split(":", 1)
    if _sanitize_point_label(label).lower() != "other":
        return False

    body_clean = clean_text(body)
    lowered = body_clean.lower()
    if not body_clean:
        return True

    if _looks_like_noisy_disambiguation_text(body_clean):
        return True

    query_terms = [token for token in re.findall(r"\b[a-zA-Z]{3,}\b", clean_text(query).lower()) if token]
    has_query_term = any(term in lowered for term in query_terms)

    meta_markers = {
        "disambiguation",
        "order by importance",
        "subject to disagreement",
        "reliable source",
        "reader",
        "clicking on links",
        "in this case",
    }
    if any(marker in lowered for marker in meta_markers):
        return True

    if not has_query_term and len(body_clean) < 220:
        return True

    return False


def _select_group_snippet_source(group: dict) -> tuple[str, str]:
    """Choose the best available snippet/title from a meaning group."""
    results = group.get("results") or []
    if results:
        for item in results[:4]:
            title = strip_source_suffix(item.get("title", ""))
            snippet = clean_text(item.get("snippet", "") or "")
            candidate = snippet or title
            if candidate and not _looks_like_noisy_disambiguation_text(candidate):
                return title, candidate

        # Fall back to top result if all options look noisy.
        top = results[0]
        title = strip_source_suffix(top.get("title", ""))
        return title, clean_text(top.get("snippet", "") or title)

    snippets = group.get("snippets") or []
    for snippet in snippets[:4]:
        snippet_clean = clean_text(str(snippet))
        if snippet_clean and not _looks_like_noisy_disambiguation_text(snippet_clean):
            return "", snippet_clean

    if snippets:
        return "", clean_text(str(snippets[0]))

    return "", ""


def summarize_search_results(query: str, results: list[dict]) -> str:
    """Summarize top search results."""
    if not results:
        return f"No results found for '{query}'."

    top_titles = []
    for item in results[:3]:
        title = strip_source_suffix(item.get("title", "Untitled"))
        if title:
            top_titles.append(title)

    if not top_titles:
        return f"No useful results found for '{query}'."

    if len(top_titles) == 1:
        return f"Top result for '{query}': {top_titles[0]}."

    return f"Top findings for '{query}': " + "; ".join(top_titles) + "."


def summarize_ambiguity_groups(query: str, meaning_groups: list[dict]) -> str:
    """Summarize results grouped by different meanings, sorted by importance."""
    if not meaning_groups:
        return f"No useful results found for '{query}'."

    sorted_groups = sorted(
        meaning_groups,
        key=lambda g: float(g.get("top_score") or 0),
        reverse=True,
    )

    non_other_groups = [
        g for g in sorted_groups
        if clean_text(g.get("meaning", "")).strip().lower() not in {"other", ""}
    ]

    groups_to_use = non_other_groups[:5] if len(non_other_groups) >= 2 else sorted_groups[:5]

    lines = []

    for group in groups_to_use:
        meaning = normalize_meaning_label(group.get("meaning") or "Other")
        results = group.get("results") or []
        if not results:
            continue

        top = results[0]
        title = strip_source_suffix(top.get("title", ""))
        snippet_source = top.get("snippet") or title
        snippet = clean_summary_snippet(
            snippet_source,
            max_chars=800,
            title=title,
            is_snippet=True,
        )

        if not snippet:
            continue

        lines.append(f"• {meaning}: {snippet}")

    if not lines:
        titles = [
            strip_source_suffix(group["results"][0]["title"])
            for group in groups_to_use[:3]
            if group.get("results")
        ]
        return f"Top findings for '{query}': " + "; ".join(titles) + "."

    return "\n\n".join(lines)


def build_meaning_map(meaning_groups: list[dict] | None) -> dict[str, str]:
    """Build mapping from title to meaning label."""
    if not meaning_groups:
        return {}

    mapping: dict[str, str] = {}

    for group in meaning_groups:
        meaning = clean_text(group.get("meaning", "Other"))
        for item in group.get("results") or []:
            title = strip_source_suffix(item.get("title", ""))
            if title:
                mapping[title.lower()] = meaning

    return mapping


def normalize_meaning_label(meaning: str) -> str:
    """Normalize meaning label for display."""
    value = clean_text(meaning).strip()

    if not value:
        return "Other"

    lower = value.lower()
    if lower == "main topic":
        return "Overview"
    if lower == "overview":
        return "Overview"
    if lower.startswith("other"):
        return "Other"

    if value[0].isupper() and " (" not in value:
        return value

    return value[0].upper() + value[1:] if value else value


def summarize_extracted_documents(
    query: str,
    documents: list[dict],
    meaning_groups: list[dict] | None = None,
) -> str:
    """Summarize extracted documents, optionally grouped by meaning."""
    if not documents:
        return f"No extracted content available for '{query}'."

    if meaning_groups:
        doc_by_title = {
            strip_source_suffix(doc.get("title", "Untitled")).lower(): doc
            for doc in documents
        }

        sorted_groups = sorted(
            meaning_groups,
            key=lambda g: float(g.get("top_score") or 0),
            reverse=True,
        )

        non_other_groups = [
            g for g in sorted_groups
            if clean_text(g.get("meaning", "")).strip().lower() not in {"other", ""}
        ]

        groups_to_use = non_other_groups[:5] if len(non_other_groups) >= 2 else sorted_groups[:5]

        blocks = []

        for idx, group in enumerate(groups_to_use):
            meaning_label = normalize_meaning_label(group.get("meaning", "Other"))
            results = group.get("results") or []
            if not results:
                continue

            top = results[0]
            title = strip_source_suffix(top.get("title", ""))
            doc = doc_by_title.get(title.lower())

            summary_piece = ""
            if doc:
                summary_piece = build_doc_summary_piece(
                    doc,
                    title,
                    max_sentences=6 if idx < 4 else 4,
                    max_chars=2400,
                )

            if not summary_piece:
                snippet_source = top.get("snippet") or title
                summary_piece = clean_summary_snippet(
                    snippet_source,
                    max_chars=2000,
                    title=title,
                    is_snippet=True,
                )

            if not summary_piece:
                continue

            blocks.append(f"• {meaning_label}: {summary_piece}")

        if blocks:
            return "\n\n".join(blocks)

        return summarize_ambiguity_groups(query, meaning_groups)

    parts = []

    for doc in documents[:6]:
        title = strip_source_suffix(doc.get("title", "Untitled"))
        summary_piece = build_doc_summary_piece(doc, title, max_sentences=6, max_chars=2400)

        if not summary_piece:
            snippet_source = doc.get("important_passages", [""])[0] if doc.get("important_passages") else title
            summary_piece = clean_summary_snippet(
                snippet_source,
                max_chars=2000,
                title=title,
                is_snippet=False,
            )

        if not summary_piece:
            continue

        parts.append(f"{title}: {summary_piece}")

    if not parts:
        return f"No useful extracted content available for '{query}'."

    return f"Research summary for '{query}': " + " | ".join(parts)


def _points_from_meaning_groups(meaning_groups: list[dict] | None) -> list[str]:
    """Build concise points from grouped meanings as a fallback formatter."""
    if not meaning_groups:
        return []

    sorted_groups = sorted(
        meaning_groups,
        key=lambda g: float(g.get("top_score") or 0),
        reverse=True,
    )

    non_other_groups = [
        g for g in sorted_groups
        if clean_text(g.get("meaning", "")).strip().lower() not in {"other", ""}
    ]
    groups_to_use = non_other_groups[:5] if len(non_other_groups) >= 2 else sorted_groups[:5]

    points: list[str] = []
    seen: set[str] = set()

    for group in groups_to_use:
        # Accept both repository-native schema and compact test schema.
        meaning = normalize_meaning_label(
            group.get("meaning") or group.get("label") or "Other"
        )

        title, snippet_source = _select_group_snippet_source(group)

        if not snippet_source:
            continue

        snippet = clean_summary_snippet(
            snippet_source,
            max_chars=800,
            title=title,
            is_snippet=True,
        )

        if not snippet:
            continue

        point = clean_text(f"{meaning}: {snippet}")
        key = point.lower()
        if key in seen:
            continue
        seen.add(key)
        points.append(point)

    return points


def _extract_point_label(point: str) -> str:
    """Extract normalized label prefix from a summary point like 'Planet: ...'."""
    if ":" not in point:
        return ""
    label = clean_text(point.split(":", 1)[0]).strip().lower()
    return label


def _sanitize_point_label(label: str) -> str:
    """Normalize free-form labels to safe display labels."""
    normalized = clean_text(label).strip().title()
    if not normalized:
        return "Other"

    if len(normalized) > 28:
        return "Other"

    if not re.fullmatch(r"[A-Za-z][A-Za-z\- ]*", normalized):
        return "Other"

    return normalized


def _sanitize_point_body(body: str) -> str:
    """Apply generic cleanup to point body text."""
    value = clean_text(body)
    value = re.sub(r"\s+#\s+[A-Za-z0-9'\-]{1,40}(?=\s|$)", " ", value)
    value = re.sub(r"\s+#\s+[A-Z][A-Za-z0-9'\- ]{1,50}\s+", " ", value)
    value = re.sub(r"\s+#{2,6}\s+[A-Z][A-Za-z0-9'\- ]{1,80}", " ", value)
    value = re.sub(r"\bPowered\s+by\s+MediaWiki\b", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\bWikimedia\s+Foundation\b", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\bmay\s+refer\s+to\b", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\bFrom\s+Wikipedia,\s+the\s+free\s+encyclopedia\b", "", value, flags=re.IGNORECASE)
    value = re.sub(
        r"\bArticle\s+Talk\s+Read\s+Edit\s+View\s+history\b.*$",
        "",
        value,
        flags=re.IGNORECASE,
    )
    value = re.sub(
        r"\bGeneral\s+What\s+links\s+here\s+Related\s+changes\b.*$",
        "",
        value,
        flags=re.IGNORECASE,
    )
    value = re.sub(r"\b(What links here|Related changes|Print/export|Download as PDF)\b.*$", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\bTopics\s+referred\s+to\s+by\s+the\s+same\b.*$", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\bFrom\s+the\s+[^.]{0,120}?manual,\s*page\s*\d+\s*:\s*", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\(>\s*", "", value)
    value = re.sub(r"\s{2,}", " ", value).strip(" -|;")
    return value


def _is_noisy_group_point(point: str) -> bool:
    """Detect visibly noisy list-like group summaries."""
    lowered = point.lower()

    noisy_markers = [
        "## ",
        " # ",
        " script error:",
        " powered by mediawiki",
        " wikimedia foundation",
        " the free encyclopedia",
        " list of ",
        " see also",
    ]
    if any(marker in lowered for marker in noisy_markers):
        return True

    if "\")" in point or "\" )" in point:
        return True

    if point.count("\n") >= 4:
        return True

    # Long comma-heavy lines are usually disambiguation-style dumps.
    if lowered.count(",") >= 12:
        return True

    # Very long semicolon-heavy lines are usually concatenated list artifacts.
    if lowered.count(";") >= 6:
        return True

    return False


def _relabel_point_by_content(point: str) -> str:
    """Relabel low-confidence point labels using generic content signals."""
    if ":" not in point:
        return point

    label, body = point.split(":", 1)
    normalized_label = _sanitize_point_label(label)
    body_clean = _sanitize_point_body(body)
    lowered = body_clean.lower()

    person_markers = {
        " born ",
        " singer",
        " songwriter",
        " actor",
        " actress",
        " author",
        " musician",
        " lead vocalist",
    }
    if normalized_label == "Location" and any(marker in f" {lowered} " for marker in person_markers):
        normalized_label = "Person"

    if normalized_label in {"Film", "Location"} and "may refer to" in lowered:
        normalized_label = "Other"

    if normalized_label == "Person":
        body_clean = re.sub(r"^\(\s*born[^)]*\)\s*", "", body_clean, flags=re.IGNORECASE)

    return f"{normalized_label}: {body_clean}"


def _trim_point_text(point: str, max_chars: int = 900) -> str:
    """Trim very long points at sentence boundaries for readability."""
    value = clean_text(point)
    if len(value) <= max_chars:
        return value

    head = value[:max_chars]
    endings = [head.rfind(". "), head.rfind("! "), head.rfind("? ")]
    best = max(endings)
    if best >= 180:
        return head[: best + 1].strip()

    last_space = head.rfind(" ")
    if last_space >= 180:
        return head[:last_space].strip() + "..."

    return head.strip() + "..."


def _point_body_too_short(point: str, min_chars: int = 20) -> bool:
    """Return True when a labeled point body is too short to be informative."""
    if ":" not in point:
        return False
    _, body = point.split(":", 1)
    return len(clean_text(body)) < min_chars


def _ensure_distinct_labels(
    points: list[str],
    meaning_groups: list[dict] | None,
    min_labels: int = 3,
) -> list[str]:
    """Add fallback points to increase distinct label coverage after cleanup."""
    if not points:
        return points

    existing_labels = {_extract_point_label(point) for point in points if _extract_point_label(point)}
    if len(existing_labels) >= min_labels:
        return points

    existing_points = {clean_text(point).lower() for point in points}

    for fallback in _points_from_meaning_groups(meaning_groups):
        candidate = _relabel_point_by_content(_trim_point_text(fallback))
        label = _extract_point_label(candidate)
        key = clean_text(candidate).lower()

        if not label or label in existing_labels:
            continue
        if key in existing_points:
            continue
        if _is_noisy_group_point(candidate) or _point_body_too_short(candidate):
            continue

        points.append(candidate)
        existing_labels.add(label)
        existing_points.add(key)

        if len(existing_labels) >= min_labels:
            break

    return points


def _token_set(value: str) -> set[str]:
    """Tokenize text into a set of meaningful lowercase words."""
    return {
        token
        for token in re.findall(r"\b[a-zA-Z]{4,}\b", clean_text(value).lower())
        if token not in {"that", "with", "from", "this", "into", "about", "which"}
    }


def _is_high_overlap(existing: str, candidate: str, threshold: float = 0.55) -> bool:
    """Return True when two bodies are near-duplicates by token overlap."""
    left = _token_set(existing)
    right = _token_set(candidate)
    if not left or not right:
        return False

    intersection = len(left & right)
    union = len(left | right)
    if not union:
        return False

    return (intersection / union) >= threshold


def _collapse_points_by_label(points: list[str], max_chars: int = 560) -> list[str]:
    """Collapse repeated labels into a single point per label."""
    collapsed: list[str] = []
    label_index: dict[str, int] = {}

    for point in points:
        cleaned = clean_text(point)
        if not cleaned or ":" not in cleaned:
            if cleaned:
                collapsed.append(_trim_point_text(cleaned, max_chars=max_chars))
            continue

        raw_label, raw_body = cleaned.split(":", 1)
        label = _sanitize_point_label(raw_label)
        body = _sanitize_point_body(raw_body)
        if not body:
            continue

        key = label.lower()
        candidate = f"{label}: {body}"

        if key not in label_index:
            label_index[key] = len(collapsed)
            collapsed.append(_trim_point_text(candidate, max_chars=max_chars))
            continue

        idx = label_index[key]
        existing = collapsed[idx]
        if ":" not in existing:
            continue

        _, existing_body = existing.split(":", 1)
        existing_body_clean = clean_text(existing_body)
        body_clean = clean_text(body)

        # Merge only when it adds non-duplicate value and doesn't over-bloat a point.
        if len(existing_body_clean) > 220:
            continue
        if body_clean and body_clean.lower() not in existing_body_clean.lower() and not _is_high_overlap(existing_body_clean, body_clean):
            merged = f"{label}: {existing_body_clean} {body_clean}"
            collapsed[idx] = _trim_point_text(merged, max_chars=max_chars)

    return collapsed


def _resolve_cross_label_body_overlap(
    points: list[str],
    fallback_map: dict[str, str],
) -> list[str]:
    """Replace cross-label near-duplicate bodies using label-specific fallback snippets."""
    resolved = list(points)
    parsed: list[tuple[int, str, str]] = []

    for idx, point in enumerate(resolved):
        if ":" not in point:
            continue
        label, body = point.split(":", 1)
        parsed.append((idx, _sanitize_point_label(label).lower(), clean_text(body)))

    for i in range(len(parsed)):
        idx_i, label_i, body_i = parsed[i]
        for j in range(i + 1, len(parsed)):
            idx_j, label_j, body_j = parsed[j]
            if label_i == label_j:
                continue
            if not _is_high_overlap(body_i, body_j, threshold=0.65):
                continue

            fallback_i = fallback_map.get(label_i)
            fallback_j = fallback_map.get(label_j)

            # Prefer replacing the lower-information point first.
            target_idx = idx_j if len(body_j) <= len(body_i) else idx_i
            target_label = label_j if target_idx == idx_j else label_i
            fallback = fallback_j if target_idx == idx_j else fallback_i

            if not fallback:
                continue

            repaired = _relabel_point_by_content(_trim_point_text(fallback))
            if ":" in repaired:
                rep_label = _extract_point_label(repaired)
                if rep_label == target_label and not _point_body_too_short(repaired):
                    resolved[target_idx] = repaired

    # Remove repeated sentences across different labels to keep sections distinct.
    sentence_sets: list[tuple[int, str, list[str]]] = []
    for idx, point in enumerate(resolved):
        if ":" not in point:
            continue
        label, body = point.split(":", 1)
        sentences = [
            clean_text(sentence).strip()
            for sentence in re.split(r"(?<=[.!?])\s+", clean_text(body))
            if clean_text(sentence).strip()
        ]
        sentence_sets.append((idx, _sanitize_point_label(label), sentences))

    for idx, label, sentences in sentence_sets:
        unique_sentences: list[str] = []
        for sentence in sentences:
            duplicate_elsewhere = False
            for other_idx, other_label, other_sentences in sentence_sets:
                if other_idx == idx or other_label.lower() == label.lower():
                    continue
                if any(_is_high_overlap(sentence, other_sentence, threshold=0.8) for other_sentence in other_sentences):
                    duplicate_elsewhere = True
                    break
            if not duplicate_elsewhere:
                unique_sentences.append(sentence)

        if unique_sentences:
            merged_body = " ".join(unique_sentences)
            resolved[idx] = _trim_point_text(f"{label}: {merged_body}")

    return resolved


def _enforce_meaning_group_coverage(
    points: list[str],
    meaning_groups: list[dict] | None,
    min_groups: int = 3,
) -> list[str]:
    """Ensure summary includes at least min_groups top non-other meaning groups."""
    if not meaning_groups:
        return points

    fallback_points = _points_from_meaning_groups(meaning_groups)
    if not fallback_points:
        return points

    merged: list[str] = []
    seen_labels: set[str] = set()
    seen_points: set[str] = set()

    # Prefer existing points first to preserve specificity.
    for point in points:
        normalized = clean_text(point)
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen_points:
            continue
        seen_points.add(key)
        merged.append(normalized)
        label = _extract_point_label(normalized)
        if label:
            seen_labels.add(label)

    # Add fallback points until top meaning coverage is satisfied.
    for fallback in fallback_points:
        normalized = clean_text(fallback)
        if not normalized:
            continue
        label = _extract_point_label(normalized)
        key = normalized.lower()
        if key in seen_points:
            continue
        if label and len(seen_labels) >= min_groups and label in seen_labels:
            continue

        merged.append(normalized)
        seen_points.add(key)
        if label:
            seen_labels.add(label)

        if len(seen_labels) >= min_groups:
            break

    return merged


def _fallback_by_label(meaning_groups: list[dict] | None) -> dict[str, str]:
    """Map normalized meaning label to a cleaner fallback point."""
    mapping: dict[str, str] = {}
    for point in _points_from_meaning_groups(meaning_groups):
        label = _extract_point_label(point)
        if label and label not in mapping:
            mapping[label] = point
    return mapping


def _target_label_count(meaning_groups: list[dict] | None, cap: int = 4) -> int:
    """Determine desired distinct label count from available meaning groups."""
    if not meaning_groups:
        return cap

    labels: list[str] = []
    for point in _points_from_meaning_groups(meaning_groups):
        label = _extract_point_label(point)
        if not label or label.startswith("other"):
            continue
        if label not in labels:
            labels.append(label)

    if not labels:
        return 1
    return min(cap, len(labels))


def _label_body_keywords() -> dict[str, set[str]]:
    """Return lightweight semantic anchors used for label/body consistency checks."""
    oak_ridge = "oak ridge"
    return {
        "programming": {"programming", "language", "interpreter", "python software foundation", "code"},
        "genus": {"species", "genus", "cat", "snake", "family", "panthera", "pythonidae"},
        "car": {"car", "cars", "vehicle", "automaker", "automobile", "jaguar land rover", "luxury"},
        "supercomputer": {"supercomputer", "cray", oak_ridge, "gpu", "olcf"},
        "planet": {"planet", "orbit", "solar system", "mercury", "venus", "mars", "jupiter"},
        "moon": {"moon", "saturn", "natural satellite", "titan", "lunar"},
        "mythology": {"mythology", "god", "deity", "pantheon", "titans"},
        "element": {"element", "atomic", "periodic", "symbol", "chemical"},
        "film": {"film", "directed", "starring", "screenplay", "comedy drama"},
        "software": {"software", "editor", "microsoft", "windows", "application", "graphics"},
        "material": {"paint", "pigment", "coating", "acrylic", "oil", "watercolor", "surface"},
        "psychology": {"psychology", "mind", "brain", "behavior", "cognitive", "neuroscience"},
        "technology": {
            "chip",
            "chip set",
            "graphics processor",
            "digital sound processor",
            "console",
            "hardware",
            "supercomputer",
            "cray",
            oak_ridge,
        },
    }


def _guess_label_from_body(body: str) -> str | None:
    """Infer a likely label from body text when the current label is not semantically aligned."""
    lowered = clean_text(body).lower()
    oak_ridge = "oak ridge"
    label_hints = [
        ("Supercomputer", {"supercomputer", "cray", oak_ridge, "gpu", "olcf"}),
        ("Car", {"cars", "vehicle", "automaker", "automobile", "luxury", "jaguar land rover"}),
        ("Genus", {"species", "genus", "cat", "snake", "family", "panthera", "pythonidae"}),
        ("Mythology", {"mythology", "god", "deity", "pantheon", "titans", "aztec", "warrior", "ocelotl"}),
        ("Programming", {"programming", "language", "interpreter", "software foundation", "code"}),
        ("Planet", {"planet", "orbit", "solar system", "mercury", "venus", "mars", "jupiter"}),
        ("Moon", {"moon", "saturn", "natural satellite", "titan", "lunar"}),
        ("Element", {"element", "atomic", "periodic", "symbol", "chemical"}),
        ("Film", {"film", "directed", "starring", "screenplay", "comedy drama"}),
        ("Software", {"software", "editor", "microsoft", "windows", "application", "graphics"}),
        ("Material", {"paint", "pigment", "coating", "acrylic", "oil", "watercolor"}),
        ("Psychology", {"psychology", "mind", "brain", "behavior", "cognitive", "neuroscience"}),
        ("Technology", {"chip", "chip set", "graphics processor", "digital sound processor", "console", "hardware"}),
    ]

    best_label = None
    best_score = 0
    for label, anchors in label_hints:
        score = sum(1 for anchor in anchors if anchor in lowered)
        if score > best_score:
            best_score = score
            best_label = label

    return best_label if best_score >= 1 else None


def _matches_label_semantics(point: str) -> bool:
    """Check whether point body contains cues consistent with its label."""
    if ":" not in point:
        return True

    label, body = point.split(":", 1)
    label_key = _sanitize_point_label(label).lower()
    anchors = _label_body_keywords().get(label_key)
    if not anchors:
        return True

    lowered = clean_text(body).lower()
    matches = sum(1 for token in anchors if token in lowered)
    return matches >= 1


def format_research_summary(
    summary: str | None,
    query: str,
    meaning_groups: list[dict] | None = None,
) -> dict:
    """Normalize summary text into frontend-friendly plain text and points."""
    if not summary:
        return {
            "summary_clean": f"No useful research findings found for '{query}'.",
            "summary_points": [],
            "summary_markdown": "",
        }

    text = summary or ""
    text = re.sub(
        rf"^Research summary for\s+'{re.escape(query)}'\s*:\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    whitespace_pattern = r"\s{2,}"

    # Clean common markdown/wiki artifacts that leak into extracted snippets.
    text = text.replace("[...]", "")
    text = re.sub(r"\s+#\s+[A-Za-z0-9'\-]{1,40}(?=\s|$)", " ", text)
    text = re.sub(r'"\s*[A-Za-z][A-Za-z\s_-]{0,40}\s*"\)', "", text)
    text = re.sub(r"\s+#\s+[A-Z][A-Za-z0-9'\- ]{1,50}\s+", " ", text)
    text = re.sub(r"\s+#{2,6}\s+[A-Z][A-Za-z0-9'\- ]{1,80}", " ", text)
    text = re.sub(r"\bPowered\s+by\s+MediaWiki\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bWikimedia\s+Foundation\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+\.{3,}", "", text)
    text = re.sub(r"\s+\)\s*", " ", text)

    raw_chunks: list[str] = []
    normalized_bullets = re.sub(r"(^|\n)\s*[•-]\s+", r"\1--POINT-- ", text)
    bullet_parts = [part.strip() for part in normalized_bullets.split("--POINT--") if part.strip()]

    if bullet_parts and any(":" in part for part in bullet_parts):
        for part in bullet_parts:
            if ":" not in part:
                continue
            label, body = part.split(":", 1)
            label = clean_text(label).strip(" -")
            body = clean_text(body)
            if not label or not body:
                continue
            body = re.sub(r"\s*[-|]\s*", " ", body)
            body = re.sub(whitespace_pattern, " ", body).strip(" -|;")
            raw_chunks.append(f"{label}: {body}")
    else:
        # Fallback for non-bulleted text while avoiding aggressive splitting.
        raw_chunks = [
            chunk.strip(" -|\n\t")
            for chunk in re.split(r"\n\n+|\s\|\s", text)
            if chunk.strip()
        ]

    points: list[str] = []
    seen: set[str] = set()

    for chunk in raw_chunks:
        candidate = clean_text(chunk.lstrip("- "))
        if not candidate:
            continue

        # Drop obvious disambiguation/list artifacts that create noisy points.
        lowered = candidate.lower()
        if " may refer to" in lowered:
            continue

        # Reject line-noise where one token is repeated in a disambiguation list.
        token_counts = re.findall(r"\b[a-z]{4,}\b", lowered)
        if token_counts:
            most_common_count = max(token_counts.count(token) for token in set(token_counts))
            if most_common_count >= 4 and lowered.count(".") <= 1:
                continue

        candidate = re.sub(r"\s*\[[^\]]*\]\s*", " ", candidate)
        candidate = re.sub(whitespace_pattern, " ", candidate).strip(" -|;")

        key = candidate.lower()
        if key in seen:
            continue
        seen.add(key)
        points.append(candidate)
        if len(points) >= 8:
            break

    if len(points) < 2:
        fallback_points = _points_from_meaning_groups(meaning_groups)
        if fallback_points:
            points = fallback_points

    target_labels = _target_label_count(meaning_groups, cap=4)
    points = _enforce_meaning_group_coverage(points, meaning_groups, min_groups=target_labels)

    fallback_map = _fallback_by_label(meaning_groups)
    normalized_points: list[str] = []
    for point in points:
        label = _extract_point_label(point)
        candidate = clean_text(point)
        if _is_noisy_group_point(candidate) and label in fallback_map:
            candidate = fallback_map[label]
        candidate = _relabel_point_by_content(candidate)
        normalized_label = _extract_point_label(candidate)
        if normalized_label in {"other", "location"} and ":" in candidate:
            _, body = candidate.split(":", 1)
            guessed = _guess_label_from_body(body)
            if guessed and guessed.lower() not in {"other", "location"}:
                candidate = f"{guessed}: {_sanitize_point_body(body)}"
            normalized_label = _extract_point_label(candidate)
        if normalized_label in fallback_map and not _matches_label_semantics(candidate):
            candidate = _relabel_point_by_content(_trim_point_text(fallback_map[normalized_label]))
        if not _matches_label_semantics(candidate) and ":" in candidate:
            _, body = candidate.split(":", 1)
            guessed = _guess_label_from_body(body)
            if guessed:
                candidate = f"{guessed}: {_sanitize_point_body(body)}"
        if _looks_like_noisy_disambiguation_text(candidate):
            label_now = _extract_point_label(candidate)
            if label_now in fallback_map:
                candidate = _relabel_point_by_content(_trim_point_text(fallback_map[label_now]))
            if _looks_like_noisy_disambiguation_text(candidate):
                continue
        if _is_contextless_other_body(query, candidate):
            label_now = _extract_point_label(candidate)
            if label_now in fallback_map:
                candidate = _relabel_point_by_content(_trim_point_text(fallback_map[label_now]))
            if _is_contextless_other_body(query, candidate):
                continue
        if _point_body_too_short(candidate):
            continue
        normalized_points.append(_trim_point_text(candidate))

    # Refill from fallback groups if cleanup dropped too many points.
    if len(normalized_points) < 3:
        existing = {clean_text(point).lower() for point in normalized_points}
        for fallback in _points_from_meaning_groups(meaning_groups):
            candidate = _relabel_point_by_content(_trim_point_text(fallback))
            key = clean_text(candidate).lower()
            if key in existing:
                continue
            if _is_noisy_group_point(candidate):
                continue
            if _point_body_too_short(candidate):
                continue
            normalized_points.append(candidate)
            existing.add(key)
            if len(normalized_points) >= 3:
                break

    if not normalized_points:
        normalized_points = [
            _trim_point_text(point)
            for point in _points_from_meaning_groups(meaning_groups)
            if not _point_body_too_short(point)
        ][:3]

    normalized_points = _ensure_distinct_labels(normalized_points, meaning_groups, min_labels=target_labels)
    normalized_points = _collapse_points_by_label(normalized_points)
    normalized_points = _ensure_distinct_labels(normalized_points, meaning_groups, min_labels=target_labels)
    normalized_points = _resolve_cross_label_body_overlap(normalized_points, fallback_map)

    points = normalized_points
    points = points[:8]

    cleaned_text = clean_text(text)

    # Build a prose paragraph by joining point bodies (without label prefixes)
    # so the summary paragraph and key-points bullets don't repeat the same content.
    if points:
        bodies = []
        for point in points:
            body = point.split(":", 1)[1] if ":" in point else point
            body = clean_text(body).strip()
            if body:
                bodies.append(body)
        summary_clean = " ".join(bodies)
    else:
        summary_clean = cleaned_text

    summary_markdown = "\n\n".join(f"- {point}" for point in points)

    return {
        "summary_clean": summary_clean,
        "summary_points": points,
        "summary_markdown": summary_markdown,
    }