"""Tavily Research (task-based) API endpoint."""
from typing import Annotated

import httpx
from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel, Field

from app.api.error_utils import map_network_error, map_provider_data_error, map_provider_error
from app.services.tavily_service import ProviderResponseError, TavilyService

router = APIRouter(prefix="/research", tags=["tavily"])


class ResearchTaskRequest(BaseModel):
    """Request schema for Tavily /research/tasks endpoint."""

    query: str
    focus: str | None = None
    max_sources: int = 20


class ResearchTaskResponse(BaseModel):
    """Response schema for research task submission."""

    task_id: str
    status: str
    created_at: str


class ResearchTaskStatusResponse(BaseModel):
    task_id: str
    status: str
    is_terminal: bool
    result_count: int = 0
    result_sources: list[dict] = Field(default_factory=list)
    error_message: str | None = None


@router.post(
    "/tasks",
    responses={
        400: {"description": "Validation error"},
        502: {"description": "Task submission failed"},
    },
)
async def submit_research_task(
    payload: ResearchTaskRequest,
) -> ResearchTaskResponse:
    """Submit a research task to Tavily."""
    try:
        service = TavilyService()
        result = await service.submit_research_task(
            query=payload.query,
            focus=payload.focus,
            max_sources=payload.max_sources,
        )
        return ResearchTaskResponse(**result)
    except ProviderResponseError as exc:
        raise map_provider_data_error(provider_label="Tavily") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        raise map_provider_error(exc, provider_label="Tavily") from exc
    except httpx.HTTPError as exc:
        raise map_network_error(exc, provider_label="Tavily") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Task submission failed.") from exc


@router.get(
    "/tasks/{task_id}",
    responses={
        400: {"description": "Validation error"},
        404: {"description": "Task not found"},
        502: {"description": "Task retrieval failed"},
    },
)
async def get_research_task(
    task_id: Annotated[str, Path(description="Task ID from Tavily")],
) -> ResearchTaskStatusResponse:
    """Get research task status and results from Tavily."""
    try:
        service = TavilyService()
        result = await service.get_research_task(task_id=task_id)
        return result
    except ProviderResponseError as exc:
        raise map_provider_data_error(provider_label="Tavily") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code if exc.response else 502
        if status == 404:
            raise HTTPException(
                status_code=404,
                detail=f"Task {task_id} not found.",
            ) from exc
        raise map_provider_error(exc, provider_label="Tavily") from exc
    except httpx.HTTPError as exc:
        raise map_network_error(exc, provider_label="Tavily") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Task retrieval failed.") from exc
