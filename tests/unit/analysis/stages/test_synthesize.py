"""Unit tests for the synthesize stage (D4 contract)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from finwiz.analysis.stages._ledger import RunLedger
from finwiz.analysis.stages._resilience import StageContext
from finwiz.analysis.stages.synthesize import synthesize
from finwiz.schemas.hybrid_analysis import EnrichedAnalysis, QualitativeInsights, QuantitativeAnalysis
from finwiz.schemas.stage_contract import StageOutcome


def _make_ctx(tmp_path: Path, mocker: Any) -> StageContext:
    return StageContext(
        ticker="AAPL",
        run_id="r1",
        ledger=RunLedger(run_id="r1", artifact_dir=tmp_path),
        extras={"analysis_ctx": mocker.MagicMock(), "partial_result": mocker.MagicMock()},
    )


def test_synthesize_returns_ok(tmp_path: Path, mocker: Any) -> None:
    fake = EnrichedAnalysis.model_construct()
    mocker.patch(
        "finwiz.analysis.stages.synthesize._synthesize_inner",
        return_value=fake,
    )
    ctx = _make_ctx(tmp_path, mocker)
    result = synthesize(ctx, QuantitativeAnalysis.model_construct(), QualitativeInsights.model_construct(), {})
    assert result.provenance.outcome == StageOutcome.OK
    assert result.payload is fake


def test_synthesize_records_ledger_entry(tmp_path: Path, mocker: Any) -> None:
    mocker.patch(
        "finwiz.analysis.stages.synthesize._synthesize_inner",
        return_value=EnrichedAnalysis.model_construct(),
    )
    ctx = _make_ctx(tmp_path, mocker)
    synthesize(ctx, QuantitativeAnalysis.model_construct(), QualitativeInsights.model_construct(), {})
    assert any(e.stage == "synthesize" for e in ctx.ledger.entries)


def test_synthesize_failure_becomes_failed(tmp_path: Path, mocker: Any) -> None:
    mocker.patch(
        "finwiz.analysis.stages.synthesize._synthesize_inner",
        side_effect=ValueError("synth error"),
    )
    ctx = _make_ctx(tmp_path, mocker)
    result = synthesize(ctx, QuantitativeAnalysis.model_construct(), QualitativeInsights.model_construct(), {})
    assert result.payload is None
    assert result.provenance.outcome == StageOutcome.FAILED


def test_synthesize_marks_low_confidence_when_qualify_degraded(tmp_path: Path, mocker: Any) -> None:
    """When upstream qualify is DEGRADED, synthesize propagates confidence='low' onto partial_result."""
    from finwiz.flow_state_models import DeepAnalysisResult

    mocker.patch(
        "finwiz.analysis.stages.synthesize._synthesize_inner",
        return_value=EnrichedAnalysis.model_construct(),
    )
    partial = DeepAnalysisResult.model_construct(confidence="high")
    ctx = StageContext(
        ticker="AAPL",
        run_id="r1",
        ledger=RunLedger(run_id="r1", artifact_dir=tmp_path),
        extras={
            "analysis_ctx": mocker.MagicMock(),
            "partial_result": partial,
            "qualify_outcome": StageOutcome.DEGRADED,
        },
    )
    result = synthesize(ctx, QuantitativeAnalysis.model_construct(), QualitativeInsights.model_construct(), {})
    assert result.provenance.outcome == StageOutcome.OK
    assert result.payload is not None
    # The partial_result in ctx.extras should now carry confidence="low"
    updated_partial = ctx.extras["partial_result"]
    assert updated_partial.confidence == "low"


def test_synthesize_keeps_high_confidence_when_qualify_ok(tmp_path: Path, mocker: Any) -> None:
    """When qualify outcome is OK, synthesize leaves confidence='high' on partial_result."""
    from finwiz.flow_state_models import DeepAnalysisResult

    mocker.patch(
        "finwiz.analysis.stages.synthesize._synthesize_inner",
        return_value=EnrichedAnalysis.model_construct(),
    )
    partial = DeepAnalysisResult.model_construct(confidence="high")
    ctx = StageContext(
        ticker="AAPL",
        run_id="r1",
        ledger=RunLedger(run_id="r1", artifact_dir=tmp_path),
        extras={
            "analysis_ctx": mocker.MagicMock(),
            "partial_result": partial,
            "qualify_outcome": StageOutcome.OK,
        },
    )
    synthesize(ctx, QuantitativeAnalysis.model_construct(), QualitativeInsights.model_construct(), {})
    assert ctx.extras["partial_result"].confidence == "high"


class TestApplyStrategicRecomputeMissingFundamental:
    """A crypto holding with no fundamental component (C1: possible for the first
    time in production once market_cap/volume_24h/age_years became optional) must
    not have its final composite/grade/recommendation recomputed by plugging a
    neutral 0.5 into recompute_with_strategic's fixed 35%-weighted term — that
    would publish an unmeasured value as if it had been measured, the same harm
    ADR-014 removes elsewhere. The recompute must be skipped, keeping the primary
    composite score (already renormalized over the components that survived).
    """

    @staticmethod
    def _enriched_with_strategic_score(quant_fundamental: float | None) -> Any:
        from finwiz.schemas.hybrid_analysis.strategic import (
            StrategicAnalysis,
            SwotAnalysis,
        )

        qual = QualitativeInsights.model_construct(strategic_analysis=StrategicAnalysis(swot=SwotAnalysis(strategic_score=0.9)))
        quant = QuantitativeAnalysis.model_construct(fundamental_score=quant_fundamental)
        return EnrichedAnalysis.model_construct(
            qualitative=qual,
            quantitative=quant,
            final_score=0.64,
            final_grade="D",
            final_recommendation="HOLD",
        )

    def test_recompute_skipped_when_fundamental_is_none(self) -> None:
        from finwiz.analysis.stages.synthesize import _apply_strategic_recompute
        from finwiz.flow_state_models import DeepAnalysisResult

        result = DeepAnalysisResult.model_construct(
            ticker="ZZZ-USD",
            composite_score=0.64,
            grade="D",
            recommendation="HOLD",
            fundamental_score=None,
            technical_score=0.70,
            risk_score=0.50,
        )
        enriched = self._enriched_with_strategic_score(quant_fundamental=None)

        updated = _apply_strategic_recompute(result, enriched)

        # The primary composite/grade/recommendation are kept, not recomputed.
        assert updated.composite_score == 0.64
        assert updated.grade == "D"
        assert updated.recommendation == "HOLD"
        # enriched.final_* must not have been overwritten with a recomputed value
        # either — the mutation happens after the point this fix returns early.
        assert enriched.final_score == 0.64
        assert enriched.final_grade == "D"
        assert enriched.final_recommendation == "HOLD"

    def test_recompute_still_runs_when_fundamental_is_present(self) -> None:
        """Regression guard: the skip must be specific to a missing fundamental,
        not a blanket disabling of the strategic recompute.
        """
        from finwiz.analysis.stages.synthesize import _apply_strategic_recompute
        from finwiz.flow_state_models import DeepAnalysisResult

        result = DeepAnalysisResult.model_construct(
            ticker="AAPL",
            composite_score=0.60,
            grade="C",
            recommendation="HOLD",
            fundamental_score=0.70,
            technical_score=0.70,
            risk_score=0.50,
        )
        enriched = self._enriched_with_strategic_score(quant_fundamental=0.70)

        updated = _apply_strategic_recompute(result, enriched)

        # A real recompute happened: the composite moved off the primary 0.60
        # and enriched.final_* were updated to match.
        assert updated.composite_score != 0.60
        assert enriched.final_score == updated.composite_score
        assert enriched.final_grade == updated.grade
        assert enriched.final_recommendation == updated.recommendation
