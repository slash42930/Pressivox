"""Serper-backed Research (task-based) API endpoint."""
import json
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.serper_service import SerperService

router = APIRouter(prefix="/research", tags=["serper"])


class ResearchTaskRequest(BaseModel):
    """Request schema for /research/tasks endpoint."""

    query: str
    focus: str | None = None
    max_sources: int = 20


class ResearchTaskResponse(BaseModel):
    """Response schema for research task submission."""

    task_id: str
    status: str
    created_at: str


@router.post(
    "/tasks",
    responses={
        400: {"description": "Validation error"},
        502: {"description": "Task submission failed"},
    },
)
async def submit_research_task(
    payload: ResearchTaskRequest,
    db: Annotated[Session, Depends(get_db)],
) -> ResearchTaskResponse:
    """Submit a research task backed by Serper search."""
    try:
        service = SerperService()
        result = await service.submit_research_task(
            query=payload.query,
            focus=payload.focus,
            max_sources=payload.max_sources,
        )
        return ResearchTaskResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code if exc.response else 502
        body = ""
        if exc.response is not None:
            try:
                body = json.dumps(exc.response.json())[:500]
            except Exception:
                body = (exc.response.text or "")[:500]
        detail = f"Serper returned HTTP {status}: {body}" if body else f"Serper returned HTTP {status}."
        raise HTTPException(status_code=502, detail=detail) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Serper network error: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Task submission failed: {exc}") from exc


@router.get(
    "/tasks/{task_id}",
    responses={
        400: {"description": "Validation error"},
        404: {"description": "Task not found"},
        502: {"description": "Task retrieval failed"},
    },
)
async def get_research_task(
    task_id: Annotated[str, Path(description="Task ID returned by POST /research/tasks")],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Get research task status and results."""
    try:
        service = SerperService()
        result = await service.get_research_task(task_id=task_id)
        return result
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code if exc.response else 502
        raise HTTPException(status_code=502, detail=f"Serper returned HTTP {status}.") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Serper network error: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Task retrieval failed: {exc}") from exc
