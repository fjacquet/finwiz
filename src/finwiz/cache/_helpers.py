"""Helper functions for AnalysisCacheManager.

Extracted from analysis_cache_manager.py to keep that file under the
300-line cap. These functions take the manager (or its internal state)
explicitly so the main class stays a thin coordinator.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from finwiz.cache._models import CachedAnalysis, CrewAnalysisResult

if TYPE_CHECKING:
    from finwiz.cache.analysis_cache_manager import AnalysisCacheManager

logger = logging.getLogger(__name__)


def verify_cache_directory(manager: AnalysisCacheManager) -> bool:
    """Ensure the cache dir exists and is writable; flip cache_enabled if not."""
    try:
        if not manager.cache_dir.exists():
            logger.warning(f"⚠️  Cache directory does not exist: {manager.cache_dir}\n   Attempting to create...")
            manager.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Created cache directory: {manager.cache_dir}")

        test_file = manager.cache_dir / ".write_test"
        try:
            test_file.write_text("test")
            test_file.unlink()
            logger.info(f"✅ Cache directory is writable: {manager.cache_dir}")
            manager.cache_enabled = True
            return True
        except (PermissionError, OSError) as e:
            logger.warning(
                f"⚠️  Cache directory is not writable: {manager.cache_dir}\n"
                f"   Error: {e}\n"
                f"   Caching will be disabled for this session.\n"
                f"   Fix: Check directory permissions or set CACHE_DIR to a writable location."
            )
            manager.cache_enabled = False
            return False
    except Exception as e:
        logger.error(f"❌ Failed to verify cache directory: {e}\n   Caching will be disabled for this session.", exc_info=True)
        manager.cache_enabled = False
        return False


def find_most_recent_cache(cache_dir: Path, ticker: str, asset_class: str) -> Path | None:
    """Return the freshest cache file for ticker/asset_class, or None."""
    asset_dir = cache_dir / asset_class
    if not asset_dir.exists():
        return None
    cache_files = list(asset_dir.glob(f"{ticker.upper()}_*.json"))
    if not cache_files:
        return None
    return max(cache_files, key=lambda f: f.stat().st_mtime)


def convert_to_crew_analysis_result(analysis: Any, ticker: str, asset_class: str) -> CrewAnalysisResult:
    """Coerce a dict / Pydantic / DeepAnalysisResult into CrewAnalysisResult.

    `quality_score` is preserved when present in the source dict — earlier
    versions hard-coded it to None, silently dropping the field on
    cache round-trips.
    """
    if isinstance(analysis, dict):
        return CrewAnalysisResult(
            ticker=ticker.upper(),
            asset_class=asset_class.lower(),
            crew_name=analysis.get("crew_name", "deep_analysis"),
            analyzed_at=datetime.fromisoformat(analysis["analysis_timestamp"]) if "analysis_timestamp" in analysis else datetime.now(),
            fundamental_score=analysis.get("fundamental_score"),
            technical_score=analysis.get("technical_score"),
            quality_score=analysis.get("quality_score"),
            risk_score=analysis.get("risk_score"),
            composite_score=analysis["composite_score"],
            grade=analysis["grade"],
            metrics={
                "data_freshness_hours": analysis.get("data_freshness_hours", 0.0),
                "confidence_level": analysis.get("confidence_level", 0.0),
                "warnings": analysis.get("warnings", []),
                "cached": analysis.get("cached", False),
            },
            raw_output=analysis,
        )
    if hasattr(analysis, "model_dump"):
        return convert_to_crew_analysis_result(analysis.model_dump(), ticker, asset_class)
    return cast(CrewAnalysisResult, analysis)


def clear_stale_cache(manager: AnalysisCacheManager) -> int:
    """Walk the cache dir and remove entries past their TTL; return removed count.

    Only removes files for confirmed corruption (JSONDecodeError or Pydantic
    ValidationError) or genuine staleness. Transient I/O failures
    (PermissionError, OSError) are logged as warnings but the file is left
    intact so a temporary glitch doesn't silently delete user data.
    """
    from pydantic import ValidationError

    removed_count = 0
    try:
        for asset_dir in manager.cache_dir.iterdir():
            if not asset_dir.is_dir():
                continue
            for cache_file in asset_dir.glob("*.json"):
                try:
                    with open(cache_file, encoding="utf-8") as f:
                        cache_data = json.load(f)
                    cached_analysis = CachedAnalysis.model_validate(cache_data)
                except (json.JSONDecodeError, ValidationError) as e:
                    # Confirmed corruption — safe to delete
                    logger.warning(f"Removing corrupted cache file {cache_file}: {e}")
                    try:
                        cache_file.unlink()
                        removed_count += 1
                    except OSError as unlink_err:
                        logger.warning(f"Could not unlink corrupted cache {cache_file}: {unlink_err}")
                    continue
                except (PermissionError, OSError) as e:
                    # Transient I/O — leave the file alone
                    logger.warning(f"Skipping cache file {cache_file} due to I/O error: {e}")
                    continue
                if not cached_analysis.is_fresh(manager.ttl_hours):
                    try:
                        cache_file.unlink()
                        removed_count += 1
                        logger.debug(f"Removed stale cache: {cache_file.name} (age: {cached_analysis.age_hours:.1f}h)")
                    except OSError as unlink_err:
                        logger.warning(f"Could not unlink stale cache {cache_file}: {unlink_err}")
        if removed_count > 0:
            logger.info(f"Cache cleanup completed: removed {removed_count} stale entries")
            manager.stats["cache_cleanups"] += removed_count
        else:
            logger.debug("Cache cleanup completed: no stale entries found")
    except Exception as e:
        logger.error(f"Error during cache cleanup: {e}")
    return removed_count


def get_cache_stats(manager: AnalysisCacheManager) -> dict[str, Any]:
    """Return hit/miss + size stats for the cache."""
    total_requests = manager.stats["cache_hits"] + manager.stats["cache_misses"]
    hit_rate = (manager.stats["cache_hits"] / total_requests * 100) if total_requests > 0 else 0
    cache_file_count = 0
    cache_size_mb: float = 0.0
    try:
        for asset_dir in manager.cache_dir.iterdir():
            if asset_dir.is_dir():
                for cache_file in asset_dir.glob("*.json"):
                    cache_file_count += 1
                    cache_size_mb += cache_file.stat().st_size / (1024 * 1024)
    except Exception as e:
        logger.warning(f"Error calculating cache stats: {e}")
    return {
        "cache_hits": manager.stats["cache_hits"],
        "cache_misses": manager.stats["cache_misses"],
        "cache_stores": manager.stats["cache_stores"],
        "cache_cleanups": manager.stats["cache_cleanups"],
        "hit_rate_percent": round(hit_rate, 1),
        "total_requests": total_requests,
        "cache_file_count": cache_file_count,
        "cache_size_mb": round(cache_size_mb, 2),
        "ttl_hours": manager.ttl_hours,
        "cache_dir": str(manager.cache_dir),
    }


def log_cache_stats(manager: AnalysisCacheManager) -> None:
    """Log a one-line summary of cache stats."""
    stats = get_cache_stats(manager)
    logger.info("Cache Statistics:")
    logger.info(f"  Hit Rate: {stats['hit_rate_percent']}% ({stats['cache_hits']}/{stats['total_requests']})")
    logger.info(f"  Cache Files: {stats['cache_file_count']}")
    logger.info(f"  Cache Size: {stats['cache_size_mb']} MB")
    logger.info(f"  Stores: {stats['cache_stores']}, Cleanups: {stats['cache_cleanups']}")
