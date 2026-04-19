from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.search import ResearchResponse, SearchRequest
from app.services.search import SearchService
from app.services.search.result_filtering import is_good_result_for_extraction
from app.services.summarization_service import format_research_summary

router = APIRouter(prefix="/research", tags=["research"])


@router.post(
    "",
    responses={
        400: {"description": "Validation error"},
        502: {"description": "Research flow failed"},
    },
)
async def run_research(
    payload: SearchRequest,
    db: Annotated[Session, Depends(get_db)],
) -> ResearchResponse:
    """Aggregated internal research flow combining search and extraction.

    This is not Tavily's native /research API, but rather an internal flow
    that leverages search results with content extraction and summarization.
    """
    try:
        service = SearchService(db)
        result = await service.run_search(payload)

        clean_results = [
            {
                "title": item["title"],
                "url": item["url"],
                "source": item.get("source"),
                "score": item.get("score"),
                "rerank_score": item.get("rerank_score"),
                "published_date": item.get("published_date"),
                "favicon": item.get("favicon"),
            }
            for item in result["results"]
            if is_good_result_for_extraction(item)
        ]

        summary_text = result["extracted_summary"] or result["summary"] or result.get("answer")
        formatted_summary = format_research_summary(
            summary_text,
            result["query"],
            meaning_groups=result.get("meaning_groups", []),
        )

        return {
            "query": result["query"],
            "topic": result["topic"],
            "provider": result["provider"],
            "summary": formatted_summary["summary_clean"],
            "summary_points": formatted_summary["summary_points"],
            "summary_markdown": formatted_summary["summary_markdown"],
            "results": clean_results,
            "selected_sources": result.get("selected_sources", []),
            "source_count": len(clean_results),
            "extracted_count": result["extracted_count"],
            "ambiguous": result.get("ambiguous", False),
            "meaning_groups": result.get("meaning_groups", []),
            "request_id": result.get("request_id"),
            "response_time": result.get("response_time"),
            "usage": result.get("usage"),
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code if exc.response else 502
        raise HTTPException(status_code=502, detail=f"Search provider returned HTTP {status}.") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Search provider network error: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Research flow failed: {exc}") from exc