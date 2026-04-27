"""Centralized validation utilities for configuration and API keys."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class MissingAPIKeyError(ValueError):
    """Raised when a required API key is missing or invalid."""

    pass


def validate_serper_api_key(
    api_key: Optional[str], env: str = "development", raise_on_missing: bool = True
) -> bool:
    """
    Validate Serper API key configuration.

    Args:
        api_key: The API key value to validate
        env: Environment (development or production)
        raise_on_missing: If True, raise on validation failure; if False, return bool

    Returns:
        True if valid, False if invalid (when raise_on_missing=False)

    Raises:
        MissingAPIKeyError: If key is missing, empty, or still contains placeholder
                           (only if raise_on_missing=True)
    """
    is_valid = api_key and api_key.strip() and api_key != "replace_me" and len(api_key) >= 10

    if not is_valid and raise_on_missing:
        error_msg = (
            "SERPER_API_KEY is missing or not configured. "
            "Set SERPER_API_KEY in your .env file to a valid Serper API key. "
            "Get one from https://serper.dev"
        )
        logger.error(error_msg)
        raise MissingAPIKeyError(error_msg)

    return is_valid
