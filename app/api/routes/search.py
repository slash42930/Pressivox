from typing import Annotated, Literal

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_optional_current_user
from app.api.error_utils import map_network_error, map_provider_data_error, map_provider_error
from app.core.database import get_db
from app.models.user import User
from app.schemas.search import QueryAnalysisResponse, SearchHistoryItem, SearchRequest, SearchResponse
from app.services.search import SearchService

router = APIRouter(prefix="/search", tags=["search"])


@router.post(
    "",
    responses={
        400: {"description": "Validation error"},
        502: {"description": "Search failed"},
    },
)
async def search_web(
    payload: SearchRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
    session_id: Annotated[str | None, Header(alias="X-Session-Id")] = None,
) -> SearchResponse:
    try:
        service = SearchService(db)
        data = await service.run_search(
            payload,
            session_id=session_id,
            user_id=current_user.id if current_user else None,
        )
        return SearchResponse(**data)
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
        raise HTTPException(status_code=502, detail="Search failed. Try again later.") from exc


@router.get("/history")
def get_search_history(
    current_user: Annotated[User, Depends(get_current_user)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    db: Annotated[Session, Depends(get_db)] = None,
    session_id: Annotated[str | None, Header(alias="X-Session-Id")] = None,
) -> list[SearchHistoryItem]:
    service = SearchService(db)
    rows = service.list_history(limit=limit, session_id=session_id, user_id=current_user.id)
    return [SearchHistoryItem.model_validate(row) for row in rows]


@router.get(
    "/analyze",
    responses={
        400: {"description": "Validation error"},
    },
)
def analyze_query(
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
    q: Annotated[str, Query(min_length=2, max_length=500)],
    topic: Annotated[Literal["general", "news", "finance"], Query()] = "general",
    db: Annotated[Session, Depends(get_db)] = None,
) -> QueryAnalysisResponse:
    service = SearchService(db)
    try:
        data = service.analyze_query(q, topic=topic)
        return QueryAnalysisResponse(**data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc