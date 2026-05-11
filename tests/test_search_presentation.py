from app.services.search.presentation import (
    build_follow_up_queries,
    build_research_response_payload,
    build_research_results,
)


def test_build_research_results_filters_non_extractable_items() -> None:
    results = [
        {
            "title": "Python programming language",
            "url": "https://www.python.org/",
            "snippet": "Python is a popular programming language.",
            "source": "python.org",
            "score": 0.95,
        },
        {
            "title": "List of Python software",
            "url": "https://example.com/list-of-python",
            "snippet": "May refer to many software projects",
            "source": "example.com",
            "score": 0.10,
        },
    ]

    clean = build_research_results(results)

    assert len(clean) == 1
    assert clean[0]["title"] == "Python programming language"
    assert clean[0]["url"] == "https://www.python.org/"


def test_build_research_response_payload_sets_source_count_from_filtered_results() -> None:
    result = {
        "query": "python",
        "topic": "general",
        "provider": "tavily",
        "results": [
            {
                "title": "Python programming language",
                "url": "https://www.python.org/",
                "snippet": "Python is a popular programming language.",
                "source": "python.org",
                "score": 0.95,
            },
            {
                "title": "List of Python software",
                "url": "https://example.com/list-of-python",
                "snippet": "May refer to many software projects",
                "source": "example.com",
                "score": 0.10,
            },
        ],
        "selected_sources": ["python.org"],
        "extracted_count": 1,
        "ambiguous": False,
        "meaning_groups": [],
        "request_id": "req-1",
        "response_time": 0.42,
        "usage": {"prompt_tokens": 10, "completion_tokens": 20},
    }

    payload = build_research_response_payload(
        result=result,
        summary_clean="clean",
        summary_points=["point"],
        summary_markdown="- point",
    )

    assert payload["source_count"] == 1
    assert len(payload["results"]) == 1
    assert payload["summary"] == "clean"
    assert payload["summary_points"] == ["point"]
    assert payload["sections"]["concise_summary"] == "clean"
    assert payload["sections"]["sources"][0]["url"] == "https://www.python.org/"


def test_build_research_results_deduplicates_urls() -> None:
    results = [
        {
            "title": "Example title",
            "url": "https://example.com/path",
            "snippet": "A valid research snippet with enough content for filtering.",
            "source": "example.com",
            "score": 0.8,
        },
        {
            "title": "Example title",
            "url": "https://example.com/path/",
            "snippet": "A valid research snippet with enough content for filtering.",
            "source": "example.com",
            "score": 0.79,
        },
    ]

    clean = build_research_results(results)

    assert len(clean) == 1


def test_sections_include_limitations_when_sources_missing() -> None:
    result = {
        "query": "rare topic",
        "topic": "general",
        "provider": "tavily",
        "results": [],
        "selected_sources": [],
        "extracted_count": 0,
        "ambiguous": False,
        "meaning_groups": [],
    }

    payload = build_research_response_payload(
        result=result,
        summary_clean="No useful findings.",
        summary_points=[],
        summary_markdown="",
    )

    assert payload["sections"]["limitations"]
    assert payload["sections"]["suggested_follow_up_queries"]


def test_follow_up_queries_use_ambiguity_label_templates() -> None:
    meaning_groups = [
        {"meaning": "Programming"},
        {"meaning": "Planet"},
        {"meaning": "Other"},
    ]

    queries = build_follow_up_queries("mercury", meaning_groups, sources=[])

    # New implementation returns natural-language questions
    assert len(queries) >= 1
    assert all("?" in q for q in queries)
    assert all("other" not in q.lower() for q in queries)


def test_follow_up_queries_fallback_when_no_meaning_groups() -> None:
    queries = build_follow_up_queries("rare topic", meaning_groups=[], sources=[])

    # New implementation returns natural-language questions for any domain
    assert len(queries) >= 1
    assert all("?" in q for q in queries)


def test_build_research_results_rejects_malformed_urls() -> None:
    results = [
        {
            "title": "Valid source",
            "url": "https://example.com/page",
            "snippet": "This snippet is sufficiently descriptive for filtering checks.",
            "source": "example.com",
        },
        {
            "title": "Bad source",
            "url": "javascript:alert(1)",
            "snippet": "This snippet is sufficiently descriptive for filtering checks.",
            "source": "bad.example",
        },
    ]

    clean = build_research_results(results)

    assert len(clean) == 1
    assert clean[0]["url"] == "https://example.com/page"
