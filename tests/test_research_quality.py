"""Regression tests for research output quality.

Acceptance criteria (query "artificial intelligence", topic "general"):
- No UI boilerplate ("Print Email Cite Translate Listen") in output.
- No image copyright lines in output.
- Film result ("A.I. Artificial Intelligence") is heavily penalised.
- Follow-up queries are natural-language questions, not keyword blobs.
- Sources include quality_score and relevance_score.
- Structured sections are well-formed.
"""

import asyncio

import pytest

from app.services.search.presentation import (
    build_follow_up_queries,
    build_research_response_payload,
    build_research_results,
)
from app.services.search.scoring import film_intent_mismatch_penalty, rerank_results
from app.services.summarization.text_cleaning import remove_ui_boilerplate


# ---------------------------------------------------------------------------
# Fixtures: realistic data modelled on reported bad output
# ---------------------------------------------------------------------------

BRITANNICA_AI_RESULT = {
    "title": "Artificial intelligence",
    "url": "https://www.britannica.com/technology/artificial-intelligence",
    "snippet": (
        "Artificial intelligence (AI), the ability of a digital computer or "
        "computer-controlled robot to perform tasks commonly associated with "
        "intelligent beings."
    ),
    "source": "britannica.com",
    "score": 0.96,
    "rerank_score": 185.0,
}

WIKIPEDIA_AI_RESULT = {
    "title": "Artificial intelligence",
    "url": "https://en.wikipedia.org/wiki/Artificial_intelligence",
    "snippet": (
        "Artificial intelligence (AI) is the simulation of human intelligence "
        "processes by computer systems. Specific applications of AI include "
        "expert systems, natural language processing (NLP), speech recognition "
        "and machine vision."
    ),
    "source": "en.wikipedia.org",
    "score": 0.95,
    "rerank_score": 190.0,
}

OECD_AI_RESULT = {
    "title": "Artificial intelligence - OECD",
    "url": "https://www.oecd.org/digital/artificial-intelligence/",
    "snippet": (
        "AI refers to machine-based systems that can, for a given set of objectives, "
        "make predictions, recommendations, or decisions influencing real or virtual "
        "environments."
    ),
    "source": "oecd.org",
    "score": 0.88,
    "rerank_score": 170.0,
}

NASA_AI_RESULT = {
    "title": "Artificial Intelligence at NASA",
    "url": "https://www.nasa.gov/topics/technology/artificial-intelligence",
    "snippet": (
        "NASA uses artificial intelligence across a wide range of missions and "
        "research areas, including autonomous spacecraft navigation, data analysis, "
        "and Earth science."
    ),
    "source": "nasa.gov",
    "score": 0.85,
    "rerank_score": 168.0,
}

# Irrelevant: Spielberg's 2001 film
FILM_AI_RESULT = {
    "title": "A.I. Artificial Intelligence (film)",
    "url": "https://en.wikipedia.org/wiki/A.I._Artificial_Intelligence",
    "snippet": (
        "A.I. Artificial Intelligence (also known as A.I.) is a 2001 American "
        "science fiction drama film directed and co-produced by Steven Spielberg. "
        "The screenplay by Spielberg was adapted from a 1969 short story."
    ),
    "source": "en.wikipedia.org",
    "score": 0.72,
}

# Boilerplate-heavy Britannica scrape (simulates UI leaking into extracted text)
BRITANNICA_BOILERPLATE_SNIPPET = (
    "Print Email Cite Translate Listen Share "
    "Artificial intelligence (AI), the ability of a digital computer or "
    "computer-controlled robot to perform tasks commonly associated with "
    "intelligent beings. © america_stock/stock.adobe.com"
)

ALL_RESULTS = [
    BRITANNICA_AI_RESULT,
    WIKIPEDIA_AI_RESULT,
    OECD_AI_RESULT,
    NASA_AI_RESULT,
    FILM_AI_RESULT,
]


# ---------------------------------------------------------------------------
# 1. Text cleaning: UI boilerplate removal
# ---------------------------------------------------------------------------

class TestRemoveUiBoilerplate:
    def test_removes_print_email_cite_sequence(self) -> None:
        text = "Print Email Cite Translate Listen This is the real article text."
        cleaned = remove_ui_boilerplate(text)
        assert "Print" not in cleaned.split()[:3]
        assert "Email" not in cleaned
        assert "Cite" not in cleaned
        assert "article text" in cleaned

    def test_removes_stock_photo_credit(self) -> None:
        text = "AI enables robots. © america_stock/stock.adobe.com Some more text."
        cleaned = remove_ui_boilerplate(text)
        assert "stock.adobe.com" not in cleaned
        assert "america_stock" not in cleaned
        assert "AI enables robots" in cleaned

    def test_removes_getty_image_credit(self) -> None:
        text = "Climate change impacts. © Jane Doe/GettyImages.com Important data follows."
        cleaned = remove_ui_boilerplate(text)
        assert "GettyImages" not in cleaned
        assert "Important data" in cleaned

    def test_removes_social_share_cta(self) -> None:
        text = "Read the full study. Share on Facebook Share on Twitter More content here."
        cleaned = remove_ui_boilerplate(text)
        assert "Share on Facebook" not in cleaned
        assert "Share on Twitter" not in cleaned
        assert "More content here" in cleaned

    def test_removes_all_rights_reserved(self) -> None:
        text = "Some informative paragraph. All rights reserved. And another sentence."
        cleaned = remove_ui_boilerplate(text)
        assert "All rights reserved" not in cleaned
        assert "informative paragraph" in cleaned

    def test_preserves_substantive_content(self) -> None:
        text = (
            "Artificial intelligence refers to the simulation of human intelligence "
            "in machines that are programmed to think and act like humans."
        )
        cleaned = remove_ui_boilerplate(text)
        assert "Artificial intelligence" in cleaned
        assert "simulation" in cleaned

    def test_cleans_britannica_style_boilerplate(self) -> None:
        cleaned = remove_ui_boilerplate(BRITANNICA_BOILERPLATE_SNIPPET)
        assert "Print" not in cleaned.split()[:3]
        assert "stock.adobe.com" not in cleaned
        assert "Artificial intelligence" in cleaned


# ---------------------------------------------------------------------------
# 2. Film mismatch penalty
# ---------------------------------------------------------------------------

class TestFilmIntentMismatchPenalty:
    def test_film_result_penalised_for_non_film_query(self) -> None:
        penalty = film_intent_mismatch_penalty("artificial intelligence", FILM_AI_RESULT)
        assert penalty >= 50, f"Expected penalty ≥50, got {penalty}"

    def test_film_result_not_penalised_for_film_query(self) -> None:
        penalty = film_intent_mismatch_penalty("best science fiction film 2001", FILM_AI_RESULT)
        assert penalty == 0

    def test_film_result_not_penalised_for_movie_query(self) -> None:
        penalty = film_intent_mismatch_penalty("A.I. movie Spielberg", FILM_AI_RESULT)
        assert penalty == 0

    def test_non_film_result_not_penalised(self) -> None:
        penalty = film_intent_mismatch_penalty("artificial intelligence", WIKIPEDIA_AI_RESULT)
        assert penalty == 0

    def test_film_rerank_score_lower_than_tech_sources(self) -> None:
        """Film result should rank below authoritative AI sources after reranking."""
        results = rerank_results("artificial intelligence", "general", ALL_RESULTS)

        film_item = next(r for r in results if "film" in r["title"].lower())
        wiki_item = next(r for r in results if r["source"] == "en.wikipedia.org" and "film" not in r["title"].lower())
        britannica_item = next(r for r in results if r["source"] == "britannica.com")

        assert film_item["rerank_score"] < wiki_item["rerank_score"], (
            f"Film ({film_item['rerank_score']}) should rank below Wikipedia "
            f"({wiki_item['rerank_score']})"
        )
        assert film_item["rerank_score"] < britannica_item["rerank_score"], (
            f"Film ({film_item['rerank_score']}) should rank below Britannica "
            f"({britannica_item['rerank_score']})"
        )


# ---------------------------------------------------------------------------
# 3. Follow-up query generation
# ---------------------------------------------------------------------------

class TestBuildFollowUpQueries:
    def test_ai_query_returns_natural_language_questions(self) -> None:
        queries = build_follow_up_queries("artificial intelligence", [], [])
        assert len(queries) >= 3
        for q in queries:
            assert "?" in q, f"Expected question mark in follow-up query: {q!r}"

    def test_ai_query_does_not_produce_keyword_blobs(self) -> None:
        queries = build_follow_up_queries("artificial intelligence", [], [])
        for q in queries:
            lower = q.lower()
            # The old system produced things like "artificial intelligence Ai latest evidence"
            assert "latest evidence" not in lower, f"Keyword blob detected: {q!r}"
            assert lower.startswith(("what", "how", "who", "which", "where", "when", "why")), (
                f"Expected question to start with a question word: {q!r}"
            )

    def test_ai_query_covers_meaningful_aspects(self) -> None:
        queries = build_follow_up_queries("artificial intelligence", [], [])
        combined = " ".join(queries).lower()
        # Should touch at least one of: types/branches, applications, risks/ethics
        touched = any(term in combined for term in ("type", "branch", "appli", "risk", "ethic", "limit"))
        assert touched, f"Follow-up queries don't cover key AI aspects: {queries}"

    def test_general_query_returns_five_or_fewer_unique_questions(self) -> None:
        queries = build_follow_up_queries("climate change", [], [])
        assert 1 <= len(queries) <= 5
        assert len(queries) == len(set(q.lower() for q in queries))


# ---------------------------------------------------------------------------
# 4. Source quality and relevance scores
# ---------------------------------------------------------------------------

class TestSourceScoring:
    def _build_payload(self) -> dict:
        result = {
            "query": "artificial intelligence",
            "topic": "general",
            "provider": "tavily",
            "results": [WIKIPEDIA_AI_RESULT, BRITANNICA_AI_RESULT, OECD_AI_RESULT, NASA_AI_RESULT],
            "extracted_count": 2,
            "selected_sources": [],
            "ambiguous": False,
            "meaning_groups": [],
            "request_id": None,
            "response_time": 1.0,
            "usage": None,
        }
        return build_research_response_payload(
            result=result,
            summary_clean="AI is the simulation of human intelligence in computer systems.",
            summary_points=["Overview: AI enables machines to perform cognitive tasks."],
            summary_markdown="- Overview: AI enables machines to perform cognitive tasks.",
        )

    def test_sections_sources_have_quality_score(self) -> None:
        payload = self._build_payload()
        for source in payload["sections"]["sources"]:
            assert "quality_score" in source, f"Missing quality_score in source: {source}"
            assert isinstance(source["quality_score"], int)
            assert 0 <= source["quality_score"] <= 100

    def test_sections_sources_have_relevance_score(self) -> None:
        payload = self._build_payload()
        for source in payload["sections"]["sources"]:
            assert "relevance_score" in source, f"Missing relevance_score in source: {source}"
            assert isinstance(source["relevance_score"], float)
            assert 0.0 <= source["relevance_score"] <= 1.0

    def test_high_trust_domain_gets_high_quality_score(self) -> None:
        payload = self._build_payload()
        sources = payload["sections"]["sources"]
        nasa = next((s for s in sources if "nasa.gov" in (s.get("source") or "")), None)
        if nasa:
            assert nasa["quality_score"] >= 80, (
                f"NASA should have high quality score, got {nasa['quality_score']}"
            )


# ---------------------------------------------------------------------------
# 5. Structured output with film excluded
# ---------------------------------------------------------------------------

class TestResearchOutputWithFilmExcluded:
    def _build_payload_all_results(self) -> dict:
        # Rerank to simulate the real pipeline (film gets penalised)
        reranked = rerank_results("artificial intelligence", "general", ALL_RESULTS)
        # build_research_results also filters via is_good_result_for_extraction
        result = {
            "query": "artificial intelligence",
            "topic": "general",
            "provider": "tavily",
            "results": reranked,
            "extracted_count": 3,
            "selected_sources": [],
            "ambiguous": False,
            "meaning_groups": [],
            "request_id": None,
            "response_time": 1.5,
            "usage": None,
        }
        return build_research_response_payload(
            result=result,
            summary_clean=(
                "Artificial intelligence (AI) is the simulation of human intelligence "
                "processes by computer systems. AI encompasses machine learning, "
                "natural language processing, computer vision, and robotics."
            ),
            summary_points=[
                "Overview: AI is the simulation of human intelligence in machines.",
                "Applications: AI is used in healthcare, finance, transportation, and education.",
                "Governance: OECD and other bodies have developed AI principles.",
            ],
            summary_markdown=(
                "- Overview: AI is the simulation of human intelligence in machines.\n"
                "- Applications: AI is used in healthcare, finance, transportation.\n"
                "- Governance: OECD and other bodies have developed AI principles."
            ),
        )

    def test_film_not_in_top_sources(self) -> None:
        """After reranking, film result should not appear in top 3 sections.sources."""
        payload = self._build_payload_all_results()
        source_titles = [s["title"].lower() for s in payload["sections"]["sources"][:3]]
        assert not any("film" in t or "spielberg" in t for t in source_titles), (
            f"Film result found in top 3 sections.sources: {source_titles}"
        )

    def test_concise_summary_is_clean_paragraph(self) -> None:
        payload = self._build_payload_all_results()
        summary = payload["sections"]["concise_summary"]
        assert len(summary) > 40, "Summary too short"
        assert "Print" not in summary
        assert "Email" not in summary
        assert "stock.adobe" not in summary.lower()

    def test_follow_up_queries_are_questions(self) -> None:
        payload = self._build_payload_all_results()
        follow_ups = payload["sections"]["suggested_follow_up_queries"]
        assert len(follow_ups) >= 3
        for q in follow_ups:
            assert "?" in q, f"Follow-up is not a question: {q!r}"

    def test_sections_has_omitted_sources_field(self) -> None:
        payload = self._build_payload_all_results()
        assert "omitted_sources" in payload["sections"]
        assert isinstance(payload["sections"]["omitted_sources"], list)


# ---------------------------------------------------------------------------
# 6. build_research_results – filters extraction-unfriendly items
# ---------------------------------------------------------------------------

class TestBuildResearchResults:
    def test_film_result_excluded_by_is_good_result_filter(self) -> None:
        """
        The film result snippet "may refer to" / short snippet should be blocked
        or its rerank_score pushed far below threshold after film penalty.
        Even if is_good_result_for_extraction passes (the film has a valid snippet),
        the film should not appear at the top of the results list.
        """
        reranked = rerank_results("artificial intelligence", "general", ALL_RESULTS)
        clean = build_research_results(reranked)

        top_3_titles = [r["title"].lower() for r in clean[:3]]
        assert not any("film" in t for t in top_3_titles), (
            f"Film result appears in top 3 sources: {top_3_titles}"
        )

    def test_deduplication_removes_duplicate_urls(self) -> None:
        results = [
            {
                "title": "Artificial intelligence",
                "url": "https://en.wikipedia.org/wiki/Artificial_intelligence",
                "snippet": "AI is the simulation of human intelligence in computer systems.",
                "source": "en.wikipedia.org",
                "score": 0.95,
            },
            {
                "title": "Artificial intelligence",
                "url": "https://en.wikipedia.org/wiki/Artificial_intelligence/",
                "snippet": "AI is the simulation of human intelligence in computer systems.",
                "source": "en.wikipedia.org",
                "score": 0.94,
            },
        ]
        clean = build_research_results(results)
        assert len(clean) == 1
