"""Cost regression: verify cold/warm/stale Perplexity call counts."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from finwiz.cache.fact_pack_cache import FactPackCache
from finwiz.schemas.hybrid_analysis.fact_pack import FactPack

pytestmark = pytest.mark.integration


def _build_fp(days_old: float = 0) -> FactPack:
    fetched = datetime.now(UTC) - timedelta(days=days_old)
    return FactPack(
        corporate_structure="x",
        recent_events=[],
        leadership="x",
        fetched_at=fetched,
        freshness=FactPack.derive_freshness(fetched),
        confidence=0.5,
        source_citations=[],
    )


class TestFactPackCacheCostRegression:
    """The 7-day cache should amortize Perplexity costs across kickoffs."""

    def test_cold_kickoff_calls_perplexity_per_holding(self, tmp_path: Path, mocker: Any) -> None:
        """First run (empty cache) calls Perplexity once per holding."""
        from finwiz.analysis.stages.fact_pack import _fact_pack_inner

        cache = FactPackCache(cache_dir=tmp_path / "fact_packs")
        mocker.patch("finwiz.analysis.stages.fact_pack._get_cache", return_value=cache)

        spy = mocker.patch(
            "finwiz.analysis.stages.fact_pack.fetch_fact_pack_sync",
            return_value=_build_fp(days_old=0),
        )

        for ticker in ("AAPL", "MSFT", "GOOG"):
            _fact_pack_inner(ticker, f"{ticker} Inc.", "Tech", "Software")

        assert spy.call_count == 3

    def test_warm_kickoff_skips_perplexity(self, tmp_path: Path, mocker: Any) -> None:
        """Second run within 7d hits cache — zero Perplexity calls."""
        from finwiz.analysis.stages.fact_pack import _fact_pack_inner

        cache = FactPackCache(cache_dir=tmp_path / "fact_packs")
        # Pre-seed cache for all 3 tickers (days_old=0 → freshness="fresh")
        for ticker in ("AAPL", "MSFT", "GOOG"):
            cache.put(ticker, _build_fp(days_old=0))

        mocker.patch("finwiz.analysis.stages.fact_pack._get_cache", return_value=cache)
        spy = mocker.patch(
            "finwiz.analysis.stages.fact_pack.fetch_fact_pack_sync",
            return_value=_build_fp(days_old=0),
        )

        for ticker in ("AAPL", "MSFT", "GOOG"):
            _fact_pack_inner(ticker, f"{ticker} Inc.", "Tech", "Software")

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
            "finwiz.analysis.stages.fact_pack.fetch_fact_pack_sync",
            return_value=_build_fp(days_old=0),
        )

        for ticker in ("AAPL", "MSFT", "GOOG"):
            _fact_pack_inner(ticker, f"{ticker} Inc.", "Tech", "Software")

        assert spy.call_count == 3  # Stale → refresh attempted
