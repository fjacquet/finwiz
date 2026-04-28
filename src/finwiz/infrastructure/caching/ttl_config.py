"""Centralized TTL configuration for all cache systems.

Provides type-aware TTL defaults and a registry that can be overridden via
environment variables. All cache consumers should use CacheTTLRegistry
instead of hardcoding TTL values.
"""

import os
from enum import StrEnum

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class CacheDataType(StrEnum):
    """Classification of cached data for TTL assignment."""

    MARKET_DATA = "market_data"  # Prices, quotes, intraday
    FUNDAMENTALS = "fundamentals"  # Earnings, ratios, balance sheet
    STATIC_REFERENCE = "static_reference"  # Sector info, industry averages
    CREW_OUTPUT = "crew_output"  # AI crew analysis results
    ANALYSIS_RESULT = "analysis_result"  # Computed analysis/scoring
    VALIDATION = "validation"  # Ticker validation, data checks
    FACT_PACK = "fact_pack"  # Verified corporate facts (v5.2), 7-day TTL


# Default TTLs in seconds
_DEFAULT_TTLS: dict[CacheDataType, int] = {
    CacheDataType.MARKET_DATA: 900,  # 15 minutes
    CacheDataType.FUNDAMENTALS: 86400,  # 24 hours
    CacheDataType.STATIC_REFERENCE: 604800,  # 7 days
    CacheDataType.CREW_OUTPUT: 86400,  # 24 hours
    CacheDataType.ANALYSIS_RESULT: 1800,  # 30 minutes
    CacheDataType.VALIDATION: 86400,  # 24 hours
    CacheDataType.FACT_PACK: 604800,  # 7 days
}

# Key pattern heuristics for automatic classification
_KEY_PATTERNS: list[tuple[list[str], CacheDataType]] = [
    (["price", "quote", "intraday", "market_data", "ticker_info"], CacheDataType.MARKET_DATA),
    (["fundamental", "earnings", "balance", "income", "ratio", "financials"], CacheDataType.FUNDAMENTALS),
    (["sector", "industry", "static", "reference", "benchmark"], CacheDataType.STATIC_REFERENCE),
    (["crew", "agent", "qualitative"], CacheDataType.CREW_OUTPUT),
    (["analysis", "scoring", "deep_analysis", "portfolio_analysis", "rebalancing"], CacheDataType.ANALYSIS_RESULT),
    (["validation", "ticker_validation", "check"], CacheDataType.VALIDATION),
    (["fact_pack", "fact-pack"], CacheDataType.FACT_PACK),
]


class CacheTTLRegistry:
    """Centralized registry for cache TTL values by data type.

    Supports environment variable overrides via CACHE_TTL_{TYPE} pattern.
    Example: CACHE_TTL_MARKET_DATA=600 sets market data TTL to 10 minutes.
    """

    def __init__(self) -> None:
        self._ttls: dict[CacheDataType, int] = dict(_DEFAULT_TTLS)
        self._load_env_overrides()

    def _load_env_overrides(self) -> None:
        """Load TTL overrides from environment variables."""
        for data_type in CacheDataType:
            env_key = f"CACHE_TTL_{data_type.value.upper()}"
            env_val = os.getenv(env_key)
            if env_val is not None:
                try:
                    ttl = int(env_val)
                    if ttl > 0:
                        self._ttls[data_type] = ttl
                        logger.info(f"Cache TTL override: {data_type.value}={ttl}s (from {env_key})")
                    else:
                        logger.warning(f"Ignoring non-positive TTL from {env_key}={env_val}")
                except ValueError:
                    logger.warning(f"Ignoring invalid TTL from {env_key}={env_val}")

    def get_ttl(self, data_type: CacheDataType) -> int:
        """Get TTL in seconds for a data type."""
        return self._ttls[data_type]

    def classify_key(self, key: str) -> CacheDataType:
        """Classify a cache key into a data type using pattern heuristics.

        Args:
            key: The cache key string to classify.

        Returns:
            Best-matching CacheDataType, defaults to ANALYSIS_RESULT.
        """
        key_lower = key.lower()
        for patterns, data_type in _KEY_PATTERNS:
            if any(p in key_lower for p in patterns):
                return data_type
        return CacheDataType.ANALYSIS_RESULT

    def get_ttl_for_key(self, key: str) -> int:
        """Get TTL for a cache key by auto-classifying it."""
        return self.get_ttl(self.classify_key(key))

    def get_all_ttls(self) -> dict[str, int]:
        """Get all current TTL values as a plain dict."""
        return {dt.value: ttl for dt, ttl in self._ttls.items()}


# Module-level singleton
_registry: CacheTTLRegistry | None = None


def get_ttl_registry() -> CacheTTLRegistry:
    """Get the global TTL registry singleton."""
    global _registry
    if _registry is None:
        _registry = CacheTTLRegistry()
    return _registry
