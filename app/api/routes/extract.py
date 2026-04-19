from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.extract import ExtractHistoryItem, ExtractRequest, ExtractResponse
from app.services.extraction_service import ExtractionService

router = APIRouter(prefix="/extract", tags=["extract"])


@router.post(
    "",
    responses={
        502: {
            "description": "Extraction failed",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Extraction failed: the target website blocked automated access."
                    }
                }
            },
        }
    },
)
async def extract_content(
    request: ExtractRequest,
    db: Annotated[Session, Depends(get_db)],
) -> ExtractResponse:
    service = ExtractionService(db)

    try:
        result = await service.extract_from_url(str(request.url))
        return ExtractResponse(**result)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 403:
            raise HTTPException(
                status_code=502,
                detail="Extraction failed: the target website blocked automated access.",
            ) from exc
        raise HTTPException(
            status_code=502,
            detail=f"Extraction failed: upstream returned HTTP {exc.response.status_code}.",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Extraction failed: {exc}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=f"Extraction failed: {exc}") from exc


@router.get("/history")
def get_extract_history(
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    db: Annotated[Session, Depends(get_db)] = None,
) -> list[ExtractHistoryItem]:
    service = ExtractionService(db)
    rows = service.list_history(limit=limit)
    return [ExtractHistoryItem.model_validate(row) for row in rows]