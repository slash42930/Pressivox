"""Shared API error mapping helpers."""

import httpx
from fastapi import HTTPException

DEFAULT_PROVIDER_LABEL = "Search provider"


def map_provider_error(
    exc: httpx.HTTPStatusError,
    provider_label: str = DEFAULT_PROVIDER_LABEL,
) -> HTTPException:
    """Convert upstream HTTP status errors to a stable API error payload."""
    status = exc.response.status_code if exc.response else 502
    return HTTPException(status_code=502, detail=f"{provider_label} returned HTTP {status}.")


def map_network_error(exc: httpx.HTTPError, provider_label: str = DEFAULT_PROVIDER_LABEL) -> HTTPException:
    """Convert upstream connectivity/timeouts to a stable API error payload."""
    if isinstance(exc, httpx.TimeoutException):
        return HTTPException(status_code=504, detail=f"{provider_label} timed out. Try again later.")
    return HTTPException(status_code=502, detail=f"{provider_label} network error. Try again later.")


def map_provider_data_error(provider_label: str = DEFAULT_PROVIDER_LABEL) -> HTTPException:
    """Convert upstream invalid payloads to a stable API error payload."""
    return HTTPException(
        status_code=502,
        detail=f"{provider_label} returned an invalid response.",
    )
