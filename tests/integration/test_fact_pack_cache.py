"""Cost regression: verify cold/warm/stale live-fetch call counts.

Note the cost model this pins: `compose_fact_pack` (Task 8) builds a pack from
free structured sources (yfinance, a curated expense-ratio table) and calls
Perplexity only as a narrow gap-fill for equities with neither SEC filings nor
allowlisted wire news -- most holdings cost nothing regardless of cache state.
What this file actually regression-tests is unchanged by that: the 7-day cache
must still amortize the live-fetch call itself (whatever it costs) across
kickoffs -- cold run calls it once per holding, warm run calls it zero times.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from finwiz.cache.fact_pack_cache import FactPackCache
from finwiz.schemas.hybrid_analysis.fact_pack import EquityFacts, FactPack

pytestmark = pytest.mark.integration


def _build_fp(days_old: float = 0) -> FactPack:
    fetched = datetime.now(UTC) - timedelta(days=days_old)
    return FactPack(
        asset_class="stock",
        details=EquityFacts(business_summary="x", leadership="x", recent_events=[]),
        fetched_at=fetched,
        freshness=FactPack.derive_freshness(fetched),
        confidence=0.5,
        source_citations=[],
    )


class TestFactPackCacheCostRegression:
    """The 7-day cache should amortize the live-fetch call across kickoffs."""

    def test_cold_kickoff_calls_compose_fact_pack_per_holding(self, tmp_path: Path, mocker: Any) -> None:
        """First run (empty cache) calls compose_fact_pack once per holding."""
        from finwiz.analysis.stages.fact_pack import _fact_pack_inner

        cache = FactPackCache(cache_dir=tmp_path / "fact_packs")
        mocker.patch("finwiz.analysis.stages.fact_pack._get_cache", return_value=cache)

        spy = mocker.patch(
            "finwiz.analysis.stages.fact_pack.compose_fact_pack",
            return_value=_build_fp(days_old=0),
        )

        for ticker in ("AAPL", "MSFT", "GOOG"):
            _fact_pack_inner(ticker, f"{ticker} Inc.", "Tech", "Software", "stock")

        assert spy.call_count == 3

    def test_warm_kickoff_skips_compose_fact_pack(self, tmp_path: Path, mocker: Any) -> None:
        """Second run within 7d hits cache — zero live-fetch calls."""
        from finwiz.analysis.stages.fact_pack import _fact_pack_inner

        cache = FactPackCache(cache_dir=tmp_path / "fact_packs")
        # Pre-seed cache for all 3 tickers (days_old=0 → freshness="fresh")
        for ticker in ("AAPL", "MSFT", "GOOG"):
            cache.put(ticker, _build_fp(days_old=0))

        mocker.patch("finwiz.analysis.stages.fact_pack._get_cache", return_value=cache)
        spy = mocker.patch(
            "finwiz.analysis.stages.fact_pack.compose_fact_pack",
            return_value=_build_fp(days_old=0),
        )

        for ticker in ("AAPL", "MSFT", "GOOG"):
            _fact_pack_inner(ticker, f"{ticker} Inc.", "Tech", "Software", "stock")

        assert spy.call_count == 0  # All from cache

    def test_stale_kickoff_attempts_refresh(self, tmp_path: Path, mocker: Any) -> None:
        """Run after 7+ days hits stale cache — attempts refresh per holding."""
        from finwiz.analysis.stages.fact_pack import _fact_pack_inner

        cache = FactPackCache(cache_dir=tmp_path / "fact_packs")
        # Pre-seed with 10-day-old entries (stale freshness)
        for ticker in ("AAPL", "MSFT", "GOOG"):
            cache.put(ticker, _build_fp(days_old=10))

        mocker.patch("finwiz.analysis.stages.fact_pack._get_cache", return_value=cache)
        spy = mocker.patch(
            "finwiz.analysis.stages.fact_pack.compose_fact_pack",
            return_value=_build_fp(days_old=0),
        )

        for ticker in ("AAPL", "MSFT", "GOOG"):
            _fact_pack_inner(ticker, f"{ticker} Inc.", "Tech", "Software", "stock")

        assert spy.call_count == 3  # Stale → refresh attempted
