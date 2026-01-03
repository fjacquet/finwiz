"""
Twelve Data API Client.

This module provides the HTTP client functionality for interacting with the Twelve Data API,
including authentication, rate limiting, caching, and error handling.
"""

from __future__ import annotations

import os
import time
from typing import Any

import aiohttp

from finwiz.infrastructure.resilience.rate_limiter import APIProvider, with_rate_limit
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
        self.api_key = os.getenv("TWELVE_DATA_API_KEY")
        if not self.api_key:
            logger.warning("TWELVE_DATA_API_KEY not found in environment variables")

        self.base_url = "https://api.twelvedata.com"
        self._cache: dict[str, dict[str, Any]] = {}
        self.cache_ttl = 300  # 5 minutes cache
        self.timeout = 30

    async def make_api_call(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        """
        Make API call to Twelve Data with rate limiting and error handling.

        Args:
            endpoint: API endpoint to call
            params: Query parameters for the API call

        Returns:
            Dictionary containing the API response data

        Raises:
            ValueError: If API key is not configured
            RuntimeError: If API returns an error response

        """
        if not self.api_key:
            raise ValueError("TWELVE_DATA_API_KEY environment variable not set")

        # Add API key to parameters
        params["apikey"] = self.api_key

        # Check cache first
        cache_key = f"{endpoint}_{hash(str(sorted(params.items())))}"
        if cache_key in self._cache:
            cache_entry = self._cache[cache_key]
            if time.time() - cache_entry["timestamp"] < self.cache_ttl:
                logger.debug(f"Using cached data for {endpoint}")
                cached_data: dict[str, Any] = cache_entry["data"]
                return cached_data

        url = f"{self.base_url}/{endpoint}"

        async def make_request() -> dict[str, Any]:
            """Make the actual HTTP request."""
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=self.timeout)) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise RuntimeError(f"API error {response.status}: {error_text}")

                    data = await response.json()

                    # Check for API error in response
                    if "status" in data and data["status"] == "error":
                        raise RuntimeError(f"API error: {data.get('message', 'Unknown error')}")

                    # Cache successful response
                    self._cache[cache_key] = {"data": data, "timestamp": time.time()}

                    result: dict[str, Any] = data
                    return result

        # Use centralized rate limiting
        try:
            result: dict[str, Any] = await with_rate_limit(APIProvider.TWELVE_DATA, make_request, endpoint=endpoint)
            return result
        except Exception as e:
            logger.error(f"Error fetching {endpoint} data: {e}")
            raise

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

    def cleanup_expired_cache(self) -> int:
        """
        Remove expired entries from cache.

        Returns:
            Number of entries removed

        """
        current_time = time.time()
        expired_keys = []

        for key, cache_entry in self._cache.items():
            if current_time - cache_entry["timestamp"] >= self.cache_ttl:
                expired_keys.append(key)

        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            logger.debug(f"Removed {len(expired_keys)} expired cache entries")

        return len(expired_keys)
