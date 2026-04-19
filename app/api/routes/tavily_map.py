"""Tavily Map API endpoint."""
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.tavily_service import TavilyService

router = APIRouter(prefix="/map", tags=["tavily"])


class MapRequest(BaseModel):
    """Request schema for Tavily /map endpoint."""

    url: HttpUrl
    max_depth: int = 1
    max_results: int = 50
    include_subdomains: bool = True


@router.post(
    "",
    responses={
        400: {"description": "Validation error"},
        502: {"description": "Map retrieval failed"},
    },
)
async def get_map(
    payload: MapRequest,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Retrieve map data from Tavily."""
    try:
        service = TavilyService()
        result = await service.map(
            url=str(payload.url),
            max_depth=payload.max_depth,
            max_results=payload.max_results,
            include_subdomains=payload.include_subdomains,
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code if exc.response else 502
        raise HTTPException(status_code=502, detail=f"Tavily returned HTTP {status}.") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Tavily network error: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Map retrieval failed: {exc}") from exc
