from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_optional_current_user
from app.core.database import get_db
from app.models.user import User
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
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
) -> ExtractResponse:
    service = ExtractionService(db)

    try:
        result = await service.extract_from_url(
            str(request.url),
            user_id=current_user.id if current_user else None,
        )
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
        raise HTTPException(status_code=502, detail="Extraction network error. Try again later.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=502, detail="Extraction failed. Check the URL and try again.") from exc


@router.get("/history")
def get_extract_history(
    current_user: Annotated[User, Depends(get_current_user)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    db: Annotated[Session, Depends(get_db)] = None,
) -> list[ExtractHistoryItem]:
    service = ExtractionService(db)
    rows = service.list_history(limit=limit, user_id=current_user.id)
    return [ExtractHistoryItem.model_validate(row) for row in rows]