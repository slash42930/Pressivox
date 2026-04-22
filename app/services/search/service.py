"""Main search service class."""

from sqlalchemy.orm import Session

from app.models.search import SearchHistory
from app.providers.tavily_provider import TavilySearchProvider
from app.schemas.search import SearchRequest
from app.services.extraction_service import ExtractionService
from app.services.summarization_service import (
    summarize_ambiguity_groups,
    summarize_extracted_documents,
    summarize_search_results,
)

from .ambiguity_detection import detect_ambiguity
from .result_filtering import (
    ambiguous_results_for_extraction,
    group_results_by_meaning,
    is_good_result_for_extraction,
    looks_like_related_not_alternate,
    primary_results_for_extraction,
)
from .scoring import rerank_results
from .scoring import smart_select_domains
from .text_processing import query_terms


class SearchService:
    """Service for searching and processing search results."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.provider = TavilySearchProvider()
        self.extraction_service = ExtractionService(db)

    def _is_short_general_query(self, request: SearchRequest) -> bool:
        return request.topic == "general" and len(query_terms(request.query)) <= 2

    def analyze_query(self, query: str, topic: str = "general") -> dict:
        """Return lightweight query diagnostics for UI guidance."""
        normalized = query.strip()
        if len(normalized) < 2:
            raise ValueError("Query must contain at least 2 characters.")

        terms = query_terms(normalized)
        is_short_query = len(terms) <= 2
        ambiguous_likely = topic == "general" and is_short_query

        topic_hints = {
            "news": {"news", "latest", "today", "breaking", "update"},
            "finance": {"stock", "stocks", "market", "economy", "inflation", "earnings"},
        }
        lowered_terms = {term.lower() for term in terms}
        recommended_topic = topic
        for candidate_topic, hints in topic_hints.items():
            if lowered_terms.intersection(hints):
                recommended_topic = candidate_topic
                break

        suggested_queries: list[str] = []
        if ambiguous_likely:
            suggested_queries = [
                f"{normalized} meaning",
                f"{normalized} overview",
                f"{normalized} wikipedia",
            ]
        elif is_short_query:
            suggested_queries = [
                f"{normalized} latest developments",
                f"{normalized} key facts",
            ]

        return {
            "query": normalized,
            "topic": topic,
            "token_count": len(terms),
            "is_short_query": is_short_query,
            "ambiguous_likely": ambiguous_likely,
            "recommended_topic": recommended_topic,
            "suggested_queries": suggested_queries,
        }

    def _merge_results(self, *result_lists: list[dict]) -> list[dict]:
        merged: list[dict] = []
        seen_urls: set[str] = set()

        for results in result_lists:
            for item in results:
                url = item.get("url")
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                merged.append(item)

        return merged

    def _meaning_input_results(self, query: str, results: list[dict]) -> list[dict]:
        filtered = [
            item
            for item in results
            if is_good_result_for_extraction(item)
            and not looks_like_related_not_alternate(query, item.get("title", ""))
        ]
        return filtered or results

    def _build_selected_sources(
        self,
        query: str,
        results: list[dict],
        ambiguous: bool,
        meaning_groups: list[dict] | None = None,
    ) -> list[dict]:
        """Build list of selected sources for response."""
        if ambiguous:
            grouped = meaning_groups or group_results_by_meaning(query, results)
            selected = []

            for group in grouped[:5]:
                if not group["results"]:
                    continue

                top_item = group["results"][0]
                selected.append(
                    {
                        "meaning": group["meaning"],
                        "title": top_item["title"],
                        "url": top_item["url"],
                        "source": top_item.get("source"),
                        "rerank_score": top_item.get("rerank_score"),
                        "favicon": top_item.get("favicon"),
                    }
                )

            return selected

        primary = primary_results_for_extraction(query, results)
        return [
            {
                "title": item["title"],
                "url": item["url"],
                "source": item.get("source"),
                "rerank_score": item.get("rerank_score"),
                "favicon": item.get("favicon"),
            }
            for item in primary
        ]

    async def run_search(self, request: SearchRequest, session_id: str | None = None) -> dict:
        """Execute search and return results."""
        include_domains = request.include_domains or smart_select_domains(
            request.query,
            request.topic,
            request.language,
            50,
        )

        primary_payload = await self.provider.search(
            query=request.query,
            topic=request.topic,
            max_results=max(request.max_results, 8 if self._is_short_general_query(request) else request.max_results),
            include_domains=include_domains,
            exclude_domains=request.exclude_domains,
            search_depth=request.search_depth,
            include_answer=request.include_answer,
            include_raw_content=request.include_raw_content,
            include_images=request.include_images,
            include_image_descriptions=request.include_image_descriptions,
            include_favicon=request.include_favicon,
            exact_match=request.exact_match,
            time_range=request.time_range,
            start_date=request.start_date,
            end_date=request.end_date,
            auto_parameters=request.auto_parameters,
        )
        primary_results = primary_payload["results"]

        results = primary_results

        if self._is_short_general_query(request):
            disambiguation_results = await self.provider.search(
                query=f"{request.query} disambiguation",
                topic=request.topic,
                max_results=8,
                include_domains=["en.wikipedia.org", "britannica.com"],
                exclude_domains=request.exclude_domains,
                search_depth=request.search_depth,
                include_answer=False,
                include_raw_content=request.include_raw_content,
                include_images=False,
                include_image_descriptions=False,
                include_favicon=request.include_favicon,
                exact_match=request.exact_match,
                time_range=request.time_range,
                start_date=request.start_date,
                end_date=request.end_date,
                auto_parameters=request.auto_parameters,
            )
            results = self._merge_results(primary_results, disambiguation_results["results"])

        results = rerank_results(
            request.query,
            request.topic,
            results,
            request.language,
        )

        meaning_input = self._meaning_input_results(request.query, results)
        ambiguous = detect_ambiguity(request.query, meaning_input)
        meaning_groups = group_results_by_meaning(request.query, meaning_input) if ambiguous else []
        selected_sources = self._build_selected_sources(
            query=request.query,
            results=meaning_input,
            ambiguous=ambiguous,
            meaning_groups=meaning_groups,
        )

        summary = summarize_search_results(request.query, results) if request.summarize else None
        extracted_summary = None
        extraction_attempted = request.extract_top_results
        extracted_count = 0

        if request.extract_top_results and results:
            if ambiguous:
                candidate_results = ambiguous_results_for_extraction(request.query, meaning_input)
            else:
                candidate_results = primary_results_for_extraction(request.query, results)

            extracted_docs = []

            for item in candidate_results:
                try:
                    extracted = await self.extraction_service.extract_from_url(
                        item["url"],
                        query=request.query,
                    )
                    extracted_docs.append(extracted)
                except Exception:
                    continue

            extracted_count = len(extracted_docs)

            if extracted_docs:
                extracted_summary = summarize_extracted_documents(
                    request.query,
                    extracted_docs,
                    meaning_groups=meaning_groups if ambiguous else None,
                )
            elif ambiguous:
                extracted_summary = summarize_ambiguity_groups(
                    request.query,
                    meaning_groups,
                )
            else:
                extracted_summary = summarize_search_results(
                    request.query,
                    results,
                )

        if session_id:
            final_summary = extracted_summary or summary or primary_payload.get("answer")
            history_row = SearchHistory(
                session_id=session_id,
                query=request.query,
                topic=request.topic,
                provider=self.provider.name,
                result_count=len(results),
                answer=final_summary,
                ambiguous=ambiguous,
                selected_source_count=len(selected_sources),
                meaning_group_count=len(meaning_groups),
                has_summary=bool(final_summary),
            )
            self.db.add(history_row)
            self.db.commit()

        return {
            "query": request.query,
            "topic": request.topic,
            "provider": self.provider.name,
            "results": results,
            "summary": summary,
            "extracted_summary": extracted_summary,
            "extraction_attempted": extraction_attempted,
            "extracted_count": extracted_count,
            "answer": extracted_summary or summary or primary_payload.get("answer"),
            "response_time": primary_payload.get("response_time"),
            "request_id": primary_payload.get("request_id"),
            "auto_parameters": primary_payload.get("auto_parameters"),
            "usage": primary_payload.get("usage"),
            "selected_sources": selected_sources,
            "ambiguous": ambiguous,
            "meaning_groups": meaning_groups,
        }

    def list_history(self, limit: int = 20, session_id: str | None = None) -> list[SearchHistory]:
        """List search history."""
        if not session_id:
            return []

        return (
            self.db.query(SearchHistory)
            .filter(SearchHistory.session_id == session_id)
            .order_by(SearchHistory.created_at.desc())
            .limit(limit)
            .all()
        )