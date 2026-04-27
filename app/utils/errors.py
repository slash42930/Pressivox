"""Standardized error handling and sanitization for Serper API operations."""

import logging
from typing import Tuple

import httpx

logger = logging.getLogger(__name__)


def sanitize_error_response(error_body: str, max_length: int = 100) -> str:
    """
    Sanitize error messages to prevent information leakage.

    Args:
        error_body: Raw error body from API
        max_length: Maximum characters to return

    Returns:
        Sanitized error message safe for clients
    """
    if not error_body:
        return "An error occurred with the external API."

    # Remove potentially sensitive fields
    sanitized = error_body.replace("Authorization", "***").replace("X-API-KEY", "***")

    # Truncate to prevent leaking details
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "..."

    return sanitized or "An error occurred with the external API."


def handle_serper_api_error(
    exc: Exception, operation: str = "Serper API", log_details: bool = True
) -> Tuple[int, str]:
    """
    Convert Serper API exceptions to HTTP response details.

    Args:
        exc: The exception to handle
        operation: Name of the operation (for user-facing message)
        log_details: If True, log full error details for debugging

    Returns:
        Tuple of (HTTP status code, user-facing error message)
    """
    if log_details:
        logger.error(f"{operation} error: {str(exc)}", exc_info=True)

    if isinstance(exc, ValueError):
        return 400, f"Invalid request: {str(exc)}"

    if isinstance(exc, httpx.HTTPStatusError):
        status_code = exc.response.status_code if exc.response else 502
        if status_code == 401:
            return 401, "Invalid API credentials."
        if status_code == 429:
            return 429, "Rate limit exceeded. Try again later."
        if status_code >= 500:
            return 502, f"{operation} service error. Try again later."
        return 502, f"{operation} returned error. Contact support."

    if isinstance(exc, (httpx.ConnectError, httpx.TimeoutException)):
        return 503, f"{operation} unavailable. Try again later."

    if isinstance(exc, httpx.RequestError):
        return 502, f"{operation} request failed. Try again later."

    return 500, f"{operation} failed. Contact support with your request ID."
