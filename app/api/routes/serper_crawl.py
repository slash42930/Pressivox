"""Serper-backed Crawl API endpoint."""
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.serper_service import SerperService

router = APIRouter(prefix="/crawl", tags=["serper"])


class CrawlRequest(BaseModel):
    """Request schema for /crawl endpoint."""

    urls: list[str]
    max_pages: int = 10
    include_raw_content: bool = False
    include_images: bool = False


@router.post(
    "",
    responses={
        400: {"description": "Validation error"},
        502: {"description": "Crawl failed"},
    },
)
async def crawl_urls(
    payload: CrawlRequest,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Extract content from a list of URLs using Serper-backed crawl."""
    try:
        service = SerperService()
        result = await service.crawl(
            urls=payload.urls,
            max_pages=payload.max_pages,
            include_raw_content=payload.include_raw_content,
            include_images=payload.include_images,
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code if exc.response else 502
        raise HTTPException(status_code=502, detail=f"Serper returned HTTP {status}.") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Serper network error: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Crawl failed: {exc}") from exc
