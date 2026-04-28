"""Tests for the fact_pack stage (v5.2)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from finwiz.analysis.stages._ledger import RunLedger
from finwiz.analysis.stages._resilience import StageContext
from finwiz.analysis.stages.fact_pack import fact_pack
from finwiz.cache.fact_pack_cache import FactPackCache
from finwiz.schemas.hybrid_analysis.fact_pack import FactPack
from finwiz.schemas.stage_contract import StageOutcome


def _build_fp(days_old: float = 0) -> FactPack:
    fetched = datetime.now(UTC) - timedelta(days=days_old)
    return FactPack(
        corporate_structure="Independent — divested VMware Nov 2021",
        recent_events=[],
        leadership="Michael Dell (CEO)",
        fetched_at=fetched,
        freshness=FactPack.derive_freshness(fetched),
        confidence=0.9,
        source_citations=[],
    )


def _build_ctx(tmp_path: Path, mocker: Any, ticker: str = "DELL") -> StageContext:
    """StageContext with a real (per-test) FactPackCache and a mocked AnalysisContext."""
    analysis_ctx = mocker.MagicMock()
    analysis_ctx.ticker = ticker
    analysis_ctx.company_name = "Dell Technologies"
    analysis_ctx.sector = "Technology"
    analysis_ctx.industry = "Hardware"
    return StageContext(
        ticker=ticker,
        run_id="r1",
        ledger=RunLedger(run_id="r1", artifact_dir=tmp_path / "ledger"),
        extras={"analysis_ctx": analysis_ctx},
    )


@pytest.fixture
def patched_cache(tmp_path: Path, mocker: Any) -> FactPackCache:
    """Replace the module-level _cache with a tmp-path-scoped cache."""
    cache = FactPackCache(cache_dir=tmp_path / "fact_packs")
    mocker.patch("finwiz.analysis.stages.fact_pack._get_cache", return_value=cache)
    return cache


class TestFactPackStage:
    def test_cache_fresh_returns_ok_no_perplexity_call(self, tmp_path: Path, mocker: Any, patched_cache: FactPackCache) -> None:
        patched_cache.put("DELL", _build_fp(days_old=0))
        spy = mocker.patch(
            "finwiz.analysis.stages.fact_pack.fetch_fact_pack_sync",
            return_value=_build_fp(),
        )
        ctx = _build_ctx(tmp_path, mocker)
        result = fact_pack(ctx, {})
        assert result.provenance.outcome == StageOutcome.OK
        assert result.payload is not None
        assert result.payload.freshness == "fresh"
        spy.assert_not_called()

    def test_cache_miss_fetches_and_caches(self, tmp_path: Path, mocker: Any, patched_cache: FactPackCache) -> None:
        mocker.patch(
            "finwiz.analysis.stages.fact_pack.fetch_fact_pack_sync",
            return_value=_build_fp(days_old=0),
        )
        ctx = _build_ctx(tmp_path, mocker)
        result = fact_pack(ctx, {})
        assert result.provenance.outcome == StageOutcome.OK
        assert result.payload is not None
        # Cache should now have the entry
        assert patched_cache.get("DELL") is not None

    def test_cache_stale_perplexity_fails_returns_ok_with_stale_payload(self, tmp_path: Path, mocker: Any, patched_cache: FactPackCache) -> None:
        # Seed a stale (10d old) cache
        stale = _build_fp(days_old=10)
        patched_cache.put("DELL", stale)
        # Perplexity fails
        mocker.patch(
            "finwiz.analysis.stages.fact_pack.fetch_fact_pack_sync",
            return_value=None,
        )
        ctx = _build_ctx(tmp_path, mocker)
        result = fact_pack(ctx, {})
        # OK outcome — staleness is a PAYLOAD field, not a stage outcome
        assert result.provenance.outcome == StageOutcome.OK
        assert result.payload is not None
        assert result.payload.freshness == "stale"

    def test_no_cache_perplexity_fails_returns_failed(self, tmp_path: Path, mocker: Any, patched_cache: FactPackCache) -> None:
        # No cache; Perplexity also fails
        mocker.patch(
            "finwiz.analysis.stages.fact_pack.fetch_fact_pack_sync",
            return_value=None,
        )
        ctx = _build_ctx(tmp_path, mocker)
        result = fact_pack(ctx, {})
        assert result.provenance.outcome == StageOutcome.FAILED
        assert result.payload is None
        assert "DELL" in (result.provenance.reason or "")

    def test_cache_stale_live_fetch_succeeds_returns_fresh(self, tmp_path: Path, mocker: Any, patched_cache: FactPackCache) -> None:
        # Stale cached + Perplexity returns new
        patched_cache.put("DELL", _build_fp(days_old=10))
        mocker.patch(
            "finwiz.analysis.stages.fact_pack.fetch_fact_pack_sync",
            return_value=_build_fp(days_old=0),  # fresh
        )
        ctx = _build_ctx(tmp_path, mocker)
        result = fact_pack(ctx, {})
        assert result.provenance.outcome == StageOutcome.OK
        assert result.payload is not None
        assert result.payload.freshness == "fresh"

    def test_ledger_records_fact_pack_entry(self, tmp_path: Path, mocker: Any, patched_cache: FactPackCache) -> None:
        mocker.patch(
            "finwiz.analysis.stages.fact_pack.fetch_fact_pack_sync",
            return_value=_build_fp(days_old=0),
        )
        ctx = _build_ctx(tmp_path, mocker)
        fact_pack(ctx, {})
        assert any(e.stage == "fact_pack" for e in ctx.ledger.entries)
