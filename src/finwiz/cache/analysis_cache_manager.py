"""Analysis cache manager for deep portfolio analysis."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from finwiz.cache._helpers import (
    clear_stale_cache as _clear_stale_cache,
)
from finwiz.cache._helpers import (
    convert_to_crew_analysis_result,
    find_most_recent_cache,
    verify_cache_directory,
)
from finwiz.cache._helpers import (
    get_cache_stats as _get_cache_stats,
)
from finwiz.cache._helpers import (
    log_cache_stats as _log_cache_stats,
)
from finwiz.cache._models import CachedAnalysis, CrewAnalysisResult

logger = logging.getLogger(__name__)


class AnalysisCacheManager:
    """Manages caching of crew analysis results for portfolio holdings."""

    def __init__(self, cache_dir: str = "cache/portfolio_analysis", ttl_hours: int = 24) -> None:
        """Initialize cache manager.

        Args:
            cache_dir: Base directory for cache storage
            ttl_hours: Default time-to-live for cached data in hours

        Requirements: 17.9-17.10 (Cache Directory Verification)
        """
        self.cache_dir = Path(cache_dir)
        self.ttl_hours = ttl_hours
        self.cache_enabled = True
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.verify_cache_directory()
        self.stats = {"cache_hits": 0, "cache_misses": 0, "cache_stores": 0, "cache_cleanups": 0}
        logger.info(f"AnalysisCacheManager initialized: cache_dir={cache_dir}, ttl_hours={ttl_hours}, cache_enabled={self.cache_enabled}")

    def verify_cache_directory(self) -> bool:
        """Verify cache directory exists and is writable at startup."""
        return verify_cache_directory(self)

    def _get_cache_path(self, ticker: str, asset_class: str) -> Path:
        """Build cache file path: cache/portfolio_analysis/{asset_class}/{ticker}_{date}.json."""
        asset_dir = self.cache_dir / asset_class
        asset_dir.mkdir(exist_ok=True)
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"{ticker.upper()}_{date_str}.json"
        return asset_dir / filename

    def _find_most_recent_cache(self, ticker: str, asset_class: str) -> Path | None:
        """Return the freshest cache file for a ticker, or None."""
        return find_most_recent_cache(self.cache_dir, ticker, asset_class)

    def get_cached_analysis(self, ticker: str, asset_class: str) -> CachedAnalysis | None:
        """Retrieve cached analysis if it exists and is fresh.

        Requirements: 17.4-17.12 (Cache Loading and Logging)
        """
        try:
            cache_key = f"{ticker.upper()}_{asset_class.lower()}"
            logger.debug(f"🔍 Loading cache with key: {cache_key}")
            cache_path = self._get_cache_path(ticker, asset_class)

            if not cache_path.exists():
                recent_cache_path = self._find_most_recent_cache(ticker, asset_class)
                if not recent_cache_path:
                    expected_path = self._get_cache_path(ticker, asset_class)
                    logger.debug(f"❌ Cache miss: No cache file for {ticker} ({asset_class})\n   Expected path: {expected_path}\n   Searched directory: {expected_path.parent}")
                    self.stats["cache_misses"] += 1
                    return None
                cache_path = recent_cache_path

            logger.info(f"📂 Found cache file: {cache_path.name}")
            with open(cache_path, encoding="utf-8") as f:
                cache_data = json.load(f)

            cached_ticker = cache_data.get("ticker", "").upper()
            cached_asset_class = cache_data.get("asset_class", "").lower()
            if cached_ticker != ticker.upper() or cached_asset_class != asset_class.lower():
                logger.warning(f"⚠️  Cache key mismatch for {cache_path.name}: expected ({ticker.upper()}, {asset_class.lower()}), got ({cached_ticker}, {cached_asset_class})")
                self.stats["cache_misses"] += 1
                return None

            cached_analysis: CachedAnalysis = CachedAnalysis.model_validate(cache_data)
            age_hours = cached_analysis.age_hours
            logger.info(f"⏰ Cache age: {age_hours:.1f} hours (TTL: {self.ttl_hours}h)")

            if cached_analysis.is_fresh(self.ttl_hours):
                logger.info(f"✅ Using cached analysis for {ticker} (age: {age_hours:.1f}h, file: {cache_path.name})")
                self.stats["cache_hits"] += 1
                return cached_analysis
            logger.info(
                f"⏳ Cache stale: Cached analysis for {ticker} exceeded TTL (age: {age_hours:.1f}h, TTL: {self.ttl_hours}h, exceeded by: {age_hours - self.ttl_hours:.1f}h)"
            )
            cache_path.unlink()
            logger.debug(f"🗑️  Removed stale cache file: {cache_path.name}")
            self.stats["cache_misses"] += 1
            return None
        except Exception as e:
            logger.error(f"❌ Cache bypass for {ticker}: Error loading cache - {e}", exc_info=True)
            self.stats["cache_misses"] += 1
            return None

    def cache_analysis(self, ticker: str, asset_class: str, analysis: CrewAnalysisResult | Any) -> None:
        """Store analysis result in cache with reliability features.

        Requirements: 17.1-17.14 (Cache Reliability)
        """
        if not self.cache_enabled:
            logger.debug(f"⏭️  Caching disabled, skipping cache save for {ticker}")
            return
        try:
            if not isinstance(analysis, CrewAnalysisResult):
                analysis = convert_to_crew_analysis_result(analysis, ticker, asset_class)
            cache_path = self._get_cache_path(ticker, asset_class)
            cached_analysis = CachedAnalysis(ticker=ticker.upper(), asset_class=asset_class.lower(), cached_at=datetime.now(), analysis=analysis)
            logger.info(f"💾 Saving cache for {ticker} ({asset_class}) to {cache_path}")

            cache_data = cached_analysis.model_dump(mode="json")
            cache_data["_metadata"] = {
                "ticker": ticker.upper(),
                "asset_class": asset_class.lower(),
                "timestamp": datetime.now().isoformat(),
                "version": "1.0",
                "cache_manager_version": "2.0",
            }
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2, default=str)

            if not cache_path.exists():
                logger.error(f"❌ Cache write verification failed: File not found after write: {cache_path}")
                return

            try:
                with open(cache_path, encoding="utf-8") as f:
                    verification_data = json.load(f)
                if verification_data.get("ticker") != ticker.upper():
                    logger.error(f"❌ Cache validation failed: Ticker mismatch (expected: {ticker.upper()}, got: {verification_data.get('ticker')})")
                    cache_path.unlink()
                    return
                if verification_data.get("asset_class") != asset_class.lower():
                    logger.error(f"❌ Cache validation failed: Asset class mismatch (expected: {asset_class.lower()}, got: {verification_data.get('asset_class')})")
                    cache_path.unlink()
                    return
                file_size = cache_path.stat().st_size
                logger.info(f"✅ Cache saved and verified for {ticker} ({asset_class}): {cache_path.name} ({file_size} bytes)")
                self.stats["cache_stores"] += 1
            except json.JSONDecodeError as e:
                logger.error(f"❌ Cache write verification failed: Invalid JSON in {cache_path}: {e}")
                cache_path.unlink()
                return
        except Exception as e:
            logger.error(f"❌ Error caching analysis for {ticker}: {e}", exc_info=True)

    def _convert_to_crew_analysis_result(self, analysis: Any, ticker: str, asset_class: str) -> CrewAnalysisResult:
        """Backwards-compat shim — see _helpers.convert_to_crew_analysis_result."""
        return convert_to_crew_analysis_result(analysis, ticker, asset_class)

    def is_fresh(self, cached_at: datetime) -> bool:
        """Return True if `cached_at` is within the manager's TTL window."""
        age = datetime.now() - cached_at
        return age.total_seconds() < (self.ttl_hours * 3600)

    def clear_stale_cache(self) -> int:
        """Remove stale cache entries across all asset classes; return count."""
        return _clear_stale_cache(self)

    def get_cache_stats(self) -> dict[str, Any]:
        """Return hit/miss + size stats for the cache."""
        return _get_cache_stats(self)

    def log_cache_stats(self) -> None:
        """Log current cache statistics."""
        _log_cache_stats(self)


_cache_manager: AnalysisCacheManager | None = None


def get_analysis_cache_manager(ttl_hours: int | None = None) -> AnalysisCacheManager:
    """Return the process-wide AnalysisCacheManager (creates one on first call)."""
    global _cache_manager
    if _cache_manager is None or (ttl_hours is not None and _cache_manager.ttl_hours != ttl_hours):
        _cache_manager = AnalysisCacheManager(ttl_hours=ttl_hours or 24)
    return _cache_manager
