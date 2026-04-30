"""Unit tests for merge.py — ADR-011 price_targets propagation."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest

from finwiz.orchestrators.portfolio_review.merge import merge_deep_analysis_from_flow_state
from finwiz.schemas.common import RiskAssessmentStandardized
from finwiz.schemas.portfolio_review import HoldingDecision, PriceTargets

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _stub_decision(ticker: str = "ASML") -> HoldingDecision:
    """Return a minimal, valid HoldingDecision with defaults for all required fields."""
    return HoldingDecision(
        asset_class="stock",
        name="ASML Holding NV",
        ticker=ticker,
        currency="EUR",
        decision="KEEP",
        composite_score=0.6,
        grade="D",
        grade_description="Placeholder",
        recommended_action="Analyse en attente",
        risk=RiskAssessmentStandardized(
            score=3.0,
            level="Medium",
        ),
    )


class _FakeFlowState:
    """Minimal flow-state stub accepted by merge_deep_analysis_from_flow_state."""

    def __init__(self, deep_analysis_results: dict[str, Any], portfolio_alternatives: dict[str, Any] | None = None) -> None:
        self.deep_analysis_results = deep_analysis_results
        self.portfolio_alternatives = portfolio_alternatives or {}


# ---------------------------------------------------------------------------
# Tests: basic merge (smoke tests)
# ---------------------------------------------------------------------------


def test_merge_returns_decisions_unchanged_when_no_results() -> None:
    """When deep_analysis_results is empty, decisions come back unmodified."""
    decisions = [_stub_decision()]
    flow_state = _FakeFlowState({})
    merged = merge_deep_analysis_from_flow_state(decisions, flow_state)
    assert len(merged) == 1
    assert merged[0].ticker == "ASML"


def test_merge_sets_grade_na_when_ticker_missing() -> None:
    """A ticker absent from deep_analysis_results gets grade='N/A' (DELL-panic fix).

    The map must be non-empty (otherwise merge returns early); ASML is missing
    while a different ticker (MSFT) is present so the else-branch runs for ASML.
    """
    from finwiz.flow_state_models import DeepAnalysisResult

    decisions = [_stub_decision()]
    other = DeepAnalysisResult.model_construct(
        ticker="MSFT",
        asset_class="stock",
        crew_name="stock_crew",
        composite_score=0.9,
        grade="A+",
        recommendation="BUY",
        rationale="great",
        confidence="high",
        cached=False,
    )
    # MSFT result present, but ASML is absent — should trigger N/A branch
    flow_state = _FakeFlowState({"MSFT": other})
    merged = merge_deep_analysis_from_flow_state(decisions, flow_state)
    assert merged[0].grade == "N/A"
    assert merged[0].composite_score == 0.0


def test_merge_sets_grade_from_deep_result() -> None:
    """When deep result exists, grade and composite_score are copied through."""
    from finwiz.flow_state_models import DeepAnalysisResult

    decisions = [_stub_decision()]
    good = DeepAnalysisResult.model_construct(
        ticker="ASML",
        asset_class="stock",
        crew_name="stock_crew",
        composite_score=0.85,
        grade="A",
        recommendation="BUY",
        rationale="ok",
        confidence="high",
        cached=False,
    )
    flow_state = _FakeFlowState({"ASML": good})
    merged = merge_deep_analysis_from_flow_state(decisions, flow_state)
    assert merged[0].grade == "A"
    assert merged[0].composite_score == pytest.approx(0.85)


# ---------------------------------------------------------------------------
# Tests: ADR-011 price_targets propagation
# ---------------------------------------------------------------------------


def test_merge_propagates_price_targets() -> None:
    """ADR-011: merge.py copies deep_result.price_targets onto decision.price_targets."""
    from finwiz.flow_state_models import DeepAnalysisResult

    decisions = [_stub_decision()]
    pt = PriceTargets(
        current_price=100.0,
        currency="USD",
        buy_target_primary=120.0,
        sell_target_primary=85.0,
        buy_rationale="r1",
        sell_rationale="r2",
        data_as_of=datetime.now(tz=UTC),
    )
    good = DeepAnalysisResult.model_construct(
        ticker="ASML",
        asset_class="stock",
        crew_name="test",
        composite_score=0.85,
        grade="A",
        recommendation="BUY",
        rationale="ok",
        confidence="high",
        cached=False,
        price_targets=pt,
    )
    flow_state = _FakeFlowState({"ASML": good})
    merged = merge_deep_analysis_from_flow_state(decisions, flow_state)
    assert merged[0].price_targets is not None
    assert merged[0].price_targets.buy_target_primary == 120.0
    assert merged[0].price_targets.sell_target_primary == 85.0


def test_merge_handles_missing_price_targets_gracefully() -> None:
    """If deep_result has no price_targets, decision.price_targets stays None — no crash."""
    from finwiz.flow_state_models import DeepAnalysisResult

    decisions = [_stub_decision()]
    good = DeepAnalysisResult.model_construct(
        ticker="ASML",
        asset_class="stock",
        crew_name="test",
        composite_score=0.85,
        grade="A",
        recommendation="BUY",
        rationale="ok",
        confidence="high",
        cached=False,
        # NOTE: no price_targets attribute set
    )
    flow_state = _FakeFlowState({"ASML": good})
    merged = merge_deep_analysis_from_flow_state(decisions, flow_state)
    assert merged[0].price_targets is None  # default from HoldingDecision


def test_merge_propagates_price_targets_with_none_explicitly() -> None:
    """If deep_result.price_targets is explicitly None, decision.price_targets stays None."""
    from finwiz.flow_state_models import DeepAnalysisResult

    decisions = [_stub_decision()]
    good = DeepAnalysisResult.model_construct(
        ticker="ASML",
        asset_class="stock",
        crew_name="test",
        composite_score=0.85,
        grade="A",
        recommendation="BUY",
        rationale="ok",
        confidence="high",
        cached=False,
        price_targets=None,
    )
    flow_state = _FakeFlowState({"ASML": good})
    merged = merge_deep_analysis_from_flow_state(decisions, flow_state)
    assert merged[0].price_targets is None
