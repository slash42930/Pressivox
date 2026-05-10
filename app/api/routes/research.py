from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_optional_current_user
from app.api.error_utils import map_network_error, map_provider_data_error, map_provider_error
from app.core.database import get_db
from app.models.user import User
from app.schemas.search import ResearchResponse, SearchRequest
from app.services.search import SearchService
from app.services.search.presentation import build_research_response_payload
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
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
    session_id: Annotated[str | None, Header(alias="X-Session-Id")] = None,
) -> ResearchResponse:
    """Aggregated internal research flow combining search and extraction.

    This is not Tavily's native /research API, but rather an internal flow
    that leverages search results with content extraction and summarization.
    """
    try:
        service = SearchService(db)
        result = await service.run_search(
            payload,
            session_id=session_id,
            user_id=current_user.id if current_user else None,
        )

        summary_text = result["extracted_summary"] or result["summary"] or result.get("answer")
        formatted_summary = format_research_summary(
            summary_text,
            result["query"],
            meaning_groups=result.get("meaning_groups", []),
        )

        return build_research_response_payload(
            result=result,
            summary_clean=formatted_summary["summary_clean"],
            summary_points=formatted_summary["summary_points"],
            summary_markdown=formatted_summary["summary_markdown"],
        )
    except ValueError as exc:
        detail = str(exc)
        if detail.lower().startswith("tavily returned"):
            raise map_provider_data_error() from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        raise map_provider_error(exc) from exc
    except httpx.HTTPError as exc:
        raise map_network_error(exc) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Research flow failed. Try again later.") from exc