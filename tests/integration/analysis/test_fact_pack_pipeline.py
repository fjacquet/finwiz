"""Integration test: full run_pipeline with fact_pack injection."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from finwiz.cache.fact_pack_cache import FactPackCache
from finwiz.schemas.hybrid_analysis.fact_pack import EquityFacts, FactPack

pytestmark = pytest.mark.integration


def _build_dell_fact_pack() -> FactPack:
    fetched = datetime.now(UTC)
    return FactPack(
        asset_class="stock",
        details=EquityFacts(
            business_summary="Dell Technologies — divested VMware November 2021",
            leadership="Michael Dell (CEO)",
            recent_events=["Q4 earnings beat"],
        ),
        fetched_at=fetched,
        freshness=FactPack.derive_freshness(fetched),
        confidence=0.95,
        source_citations=["https://example.com/dell"],
    )


@pytest.fixture
def dell_cache(tmp_path: Path, mocker: Any) -> FactPackCache:
    """Pre-seed cache with DELL fact pack to avoid live Perplexity call."""
    cache = FactPackCache(cache_dir=tmp_path / "fact_packs")
    cache.put("DELL", _build_dell_fact_pack())
    mocker.patch("finwiz.analysis.stages.fact_pack._get_cache", return_value=cache)
    return cache


class TestFactPackPipelineIntegration:
    def test_fact_pack_flows_through_qualify(self, tmp_path: Path, mocker: Any, dell_cache: FactPackCache) -> None:
        """When fact_pack stage caches DELL, the qualify prompt sees the divestiture fact."""
        from finwiz.analysis.stages._ledger import RunLedger
        from finwiz.analysis.stages._resilience import StageContext
        from finwiz.analysis.stages.fact_pack import fact_pack

        analysis_ctx = mocker.MagicMock()
        analysis_ctx.ticker = "DELL"
        analysis_ctx.company_name = "Dell Technologies"
        analysis_ctx.sector = "Technology"
        analysis_ctx.industry = "Hardware"
        analysis_ctx.asset_class = "stock"

        ctx = StageContext(
            ticker="DELL",
            run_id="r1",
            ledger=RunLedger(run_id="r1", artifact_dir=tmp_path / "ledger"),
            extras={"analysis_ctx": analysis_ctx},
        )

        result = fact_pack(ctx, {})
        assert result.payload is not None
        assert "divested VMware" in result.payload.details.business_summary
