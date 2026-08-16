"""Fact pack stage (v5.2) — fetches verified corporate facts.

Always returns OK with a FactPack payload, OR FAILED if no cache and live fetch fails.
Staleness is a payload field (`freshness="stale"`), NOT a stage outcome — the
DEGRADED outcome stays reserved for `qualify` per the v5.1 trust-spine invariant.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from finwiz.analysis.fact_pack_research import fetch_fact_pack_sync
from finwiz.analysis.stages._resilience import StageContext, TransientStageError, stage
from finwiz.cache.fact_pack_cache import FactPackCache
from finwiz.schemas.hybrid_analysis.fact_pack import FactPack

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Single shared cache instance for the process. Tests inject their own via
# `_get_cache()` patching when needed.
_cache: FactPackCache | None = None


def _get_cache() -> FactPackCache:
    global _cache
    if _cache is None:
        _cache = FactPackCache()
    return _cache


def _fact_pack_inner(
    ticker: str,
    company_name: str,
    sector: str | None,
    industry: str | None,
) -> FactPack:
    """Fact pack lookup with cache + live-fetch fallback.

    Behavior:
      1. Cache fresh (<3d) or recent (3-7d) → return cached
      2. Cache stale (7-14d):
           live fetch succeeds → cache.put(new); return new (freshness=fresh)
           live fetch fails    → return cached (freshness=stale)
      3. Cache miss:
           live fetch succeeds → cache.put(new); return new
           live fetch fails    → raise TransientStageError → @stage retries once, then records FAILED

    The freshness label on the returned payload is the only signal — the stage
    outcome is always OK or FAILED.
    """
    cache = _get_cache()
    cached = cache.get(ticker)
    if cached is not None and cached.freshness in ("fresh", "recent"):
        logger.debug(f"fact_pack cache hit ({cached.freshness}) for {ticker}")
        return cached

    # Try live fetch (cache stale or miss)
    fetched = fetch_fact_pack_sync(ticker, company_name, sector, industry)
    if fetched is not None:
        cache.put(ticker, fetched)
        logger.info(f"fact_pack fetched for {ticker} (freshness={fetched.freshness})")
        return fetched

    # Live fetch failed — fall back to stale cache if available
    if cached is not None:
        logger.warning(f"fact_pack live fetch failed for {ticker}; using stale cache (fetched_at={cached.fetched_at})")
        return cached

    # No cache and no live data — TransientStageError (not plain RuntimeError) so the
    # @stage decorator's declared retry can actually reach this failure; see
    # _resilience._is_transient. Still recorded as FAILED once retries are exhausted.
    raise TransientStageError(f"fact_pack unavailable for {ticker}: no cache and Perplexity fetch failed")


@stage(name="fact_pack", timeout_s=60, retries=1)
def fact_pack(ctx: StageContext, raw_data: dict) -> FactPack:
    """Stage entry: returns FactPack or raises (which @stage captures as FAILED).

    The decorator wraps the bare return into StageResult[FactPack].
    """
    analysis_ctx = ctx.extras["analysis_ctx"]
    ticker = analysis_ctx.ticker
    company_name = analysis_ctx.company_name
    sector = getattr(analysis_ctx, "sector", None) or raw_data.get("sector")
    industry = getattr(analysis_ctx, "industry", None) or raw_data.get("industry")
    return _fact_pack_inner(ticker, company_name, sector, industry)
