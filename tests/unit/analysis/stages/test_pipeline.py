"""End-to-end pipeline integration: 3 holdings — one OK, one DEGRADED, one FAILED."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from finwiz.analysis.stages import run_pipeline
from finwiz.analysis.stages._ledger import RunLedger
from finwiz.cache.fact_pack_cache import FactPackCache
from finwiz.flow_state_models import DeepAnalysisResult
from finwiz.schemas.hybrid_analysis import EnrichedAnalysis, QualitativeInsights, QuantitativeAnalysis


def _make_analysis_context(ticker: str, ledger: RunLedger) -> Any:
    """Build a minimal AnalysisContext with ledger threaded."""
    from finwiz.analysis.deep_analysis_pipeline import AnalysisContext

    return AnalysisContext(
        ticker=ticker,
        asset_class="etf",  # avoids strategic-research path
        company_name="Test",
        ledger=ledger,
        run_id=ledger.run_id,
    )


def test_three_holding_pipeline_ok_degraded_failed(tmp_path: Path, mocker: Any) -> None:
    """One OK, one DEGRADED (AI null), one FAILED (collect raises) — banner is amber.

    HAPPY_TKR:   all stages succeed → emit=OK, no degradation
    DEGRADED_TKR: _try_ai_qualify returns None → qualify=DEGRADED, emit=OK
    FAILED_TKR:  _collect_raw_data_inner raises + _build_verdict_inner raises → emit=FAILED

    Expected ledger counts:
      analyzed  == 1  (HAPPY_TKR: emit=OK, no degraded qualify)
      degraded  == 1  (DEGRADED_TKR: qualify=DEGRADED + emit=OK)
      failed    == 1  (FAILED_TKR: emit=FAILED, no emit=OK entry)
      total     == 3
    Expected banner: amber (degraded > 0 or failed > 0, and not 2*failed > total)
    """
    ledger = RunLedger(run_id="integ-e6", artifact_dir=tmp_path, total=3)

    # -- collect mock ----------------------------------------------------------
    # Raises for FAILED_TKR; returns raw data for the other two.
    def _collect_inner(ctx: Any, prefetched_data: Any = None) -> dict[str, Any]:
        if ctx.ticker == "FAILED_TKR":
            raise RuntimeError("data source down")
        return {"price_history": [1, 2, 3]}

    mocker.patch(
        "finwiz.analysis.stages.collect._collect_raw_data_inner",
        side_effect=_collect_inner,
    )

    # -- quantify mock ---------------------------------------------------------
    fake_partial = DeepAnalysisResult.model_construct(
        ticker="X",
        asset_class="etf",
        grade="B",
        composite_score=0.7,
        recommendation="HOLD",
    )
    fake_quant = QuantitativeAnalysis.model_construct()
    mocker.patch(
        "finwiz.analysis.stages.quantify._calculate_quantitative_inner",
        return_value=(fake_partial, fake_quant),
    )

    # -- qualify mock ----------------------------------------------------------
    # AI returns None for DEGRADED_TKR → qualify emits DEGRADED via python proxy.
    fake_ai_qual = QualitativeInsights.model_construct()
    fake_proxy_qual = QualitativeInsights.model_construct()

    def _ai_qualify(analysis_ctx: Any, quant: Any, raw_data: Any = None) -> QualitativeInsights | None:
        return None if analysis_ctx.ticker == "DEGRADED_TKR" else fake_ai_qual

    mocker.patch("finwiz.analysis.stages.qualify._try_ai_qualify", side_effect=_ai_qualify)
    mocker.patch("finwiz.analysis.stages.qualify._python_proxy_qualify", return_value=fake_proxy_qual)

    # -- synthesize mock -------------------------------------------------------
    fake_enriched = EnrichedAnalysis.model_construct()
    mocker.patch(
        "finwiz.analysis.stages.synthesize._synthesize_inner",
        return_value=fake_enriched,
    )

    # -- emit mock -------------------------------------------------------------
    # Raises for FAILED_TKR so emit records FAILED and no emit=OK entry is written.
    fake_verdict = DeepAnalysisResult.model_construct(
        ticker="X",
        asset_class="etf",
        grade="B",
        composite_score=0.7,
        recommendation="HOLD",
    )

    def _verdict_inner(ctx: Any, result: Any, enriched: Any, strategic: Any, processing_time: Any) -> tuple[Any, Any]:
        if ctx.ticker == "FAILED_TKR":
            raise RuntimeError("emit failure for FAILED_TKR")
        return fake_verdict, enriched

    mocker.patch(
        "finwiz.analysis.stages.emit._build_verdict_inner",
        side_effect=_verdict_inner,
    )

    # -- run pipeline for each ticker ------------------------------------------
    for ticker in ("HAPPY_TKR", "DEGRADED_TKR", "FAILED_TKR"):
        ctx = _make_analysis_context(ticker, ledger)
        run_pipeline(ctx)

    # -- assertions on ledger coverage -----------------------------------------
    summary = ledger.coverage()

    # HAPPY_TKR: clean analyzed (emit=OK, qualify=OK)
    assert summary.analyzed == 1, f"expected analyzed=1, got {summary.analyzed} (entries: {[(e.ticker, e.stage, e.outcome) for e in ledger.entries]})"

    # DEGRADED_TKR: qualify=DEGRADED + emit=OK
    assert summary.degraded == 1, f"expected degraded=1, got {summary.degraded}"

    # FAILED_TKR: emit=FAILED (no emit=OK entry in ledger)
    assert summary.failed == 1, f"expected failed=1, got {summary.failed}"

    assert summary.total == 3, f"expected total=3, got {summary.total}"

    # -- assertions on trust banner --------------------------------------------
    banner = ledger.to_banner()
    # degraded > 0 and failed > 0, but 2*failed(2) <= total(3) → amber
    assert banner.state == "amber", f"expected amber banner, got {banner.state!r}: {banner.message}"
    assert not banner.block_decisions, "amber banner must not block decisions"


def _empty_cache(tmp_path: Path, mocker: Any) -> FactPackCache:
    """Return an empty FactPackCache backed by tmp_path."""
    return FactPackCache(cache_dir=tmp_path / "fact_packs_empty")


def test_pipeline_short_circuits_when_fact_pack_fails(tmp_path: Path, mocker: Any) -> None:
    """When fact_pack returns FAILED, run_pipeline emits AnalysePending."""
    # Mock upstream stages to succeed
    mocker.patch(
        "finwiz.analysis.stages.collect._collect_raw_data_inner",
        return_value={"price_history": [1, 2]},
    )
    fake_partial = DeepAnalysisResult.model_construct(
        ticker="FAILED_FP_TKR",
        asset_class="etf",
        grade="B",
        composite_score=0.7,
        recommendation="HOLD",
    )
    fake_quant = QuantitativeAnalysis.model_construct()
    mocker.patch(
        "finwiz.analysis.stages.quantify._calculate_quantitative_inner",
        return_value=(fake_partial, fake_quant),
    )

    # Mock fact_pack to fail (no cache + Perplexity returns None)
    mocker.patch(
        "finwiz.analysis.stages.fact_pack._get_cache",
        return_value=_empty_cache(tmp_path, mocker),
    )
    mocker.patch(
        "finwiz.analysis.stages.fact_pack.fetch_fact_pack_sync",
        return_value=None,
    )

    ledger = RunLedger(run_id="fp-fail", artifact_dir=tmp_path / "ledger")
    ctx = _make_analysis_context("FAILED_FP_TKR", ledger)
    result, enriched = run_pipeline(ctx)

    # Pipeline halted — pending verdict
    assert result.grade == "N/A"
    assert "Analyse en attente" in result.rationale
