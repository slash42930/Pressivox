from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.search import SearchHistoryItem, SearchRequest, SearchResponse
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
) -> SearchResponse:
    try:
        service = SearchService(db)
        data = await service.run_search(payload)
        return SearchResponse(**data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code if exc.response else 502
        raise HTTPException(status_code=502, detail=f"Search provider returned HTTP {status}.") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Search provider network error: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Search failed: {exc}") from exc


@router.get("/history")
def get_search_history(
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    db: Annotated[Session, Depends(get_db)] = None,
) -> list[SearchHistoryItem]:
    service = SearchService(db)
    rows = service.list_history(limit=limit)
    return [SearchHistoryItem.model_validate(row) for row in rows]