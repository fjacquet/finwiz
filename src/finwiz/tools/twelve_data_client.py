"""
Twelve Data API Client.

This module provides the HTTP client functionality for interacting with the Twelve Data API,
including authentication, rate limiting, caching, and error handling.
"""

from __future__ import annotations

import time
from typing import Any

from finwiz.config.endpoints import TWELVE_DATA_BASE
from finwiz.tools.api_key_validation import validate_api_key
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class TwelveDataClient:
    """
    HTTP client for Twelve Data API with rate limiting and caching.

    This class handles all the low-level API communication including:
    - Authentication with API keys
    - Rate limiting and retry logic
    - Response caching
    - Error handling and logging
    """

    def __init__(self) -> None:
        """Initialize the Twelve Data API client."""
        self.api_key = validate_api_key("TWELVE_DATA_API_KEY", self.__class__.__name__)
        self.base_url = TWELVE_DATA_BASE
        self._cache: dict[str, dict[str, Any]] = {}
        self.cache_ttl = 300  # 5 minutes cache
        self.timeout = 30

    def clear_cache(self) -> None:
        """Clear the API response cache."""
        self._cache.clear()
        logger.info("API cache cleared")

    def get_cache_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary containing cache statistics

        """
        current_time = time.time()
        valid_entries = 0
        expired_entries = 0

        for cache_entry in self._cache.values():
            if current_time - cache_entry["timestamp"] < self.cache_ttl:
                valid_entries += 1
            else:
                expired_entries += 1

        return {
            "total_entries": len(self._cache),
            "valid_entries": valid_entries,
            "expired_entries": expired_entries,
            "cache_ttl": self.cache_ttl,
        }
