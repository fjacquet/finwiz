"""Unit tests for GapProfileOrchestrator (Portfolio-Aware Opportunity Cascade)."""

from __future__ import annotations

import pytest

from finwiz.flow_state import FinwizState
from finwiz.flow_state_models import DeepAnalysisResult
from finwiz.orchestrators.gap_profile_orchestrator import GapProfileOrchestrator


def _dar(ticker: str, *, grade: str, risk_score: float | None, asset_class: str = "stock") -> DeepAnalysisResult:
    return DeepAnalysisResult(
        ticker=ticker,
        asset_class=asset_class,
        crew_name="test",
        composite_score=0.7,
        grade=grade,
        recommendation="HOLD",
        rationale="t",
        risk_score=risk_score,
        data_freshness_hours=1.0,
        confidence_level=0.9,
    )


@pytest.fixture(autouse=True)
def _no_network(mocker):
    """Stub batched market data so the orchestrator never hits yfinance."""
    mocker.patch(
        "finwiz.discovery.market_data.get_sectors",
        return_value={"AAPL": "Technology", "MSFT": "Technology", "JNJ": "Healthcare"},
    )
    mocker.patch(
        "finwiz.discovery.market_data.get_returns",
        return_value={"AAPL": [0.01, -0.01, 0.02], "MSFT": [0.0, 0.01, 0.0], "JNJ": [0.01, 0.0, -0.01]},
    )


@pytest.fixture
def state(tmp_path, mocker) -> FinwizState:
    # Redirect persistence into tmp so tests don't write into the repo.
    mocker.patch(
        "finwiz.orchestrators.gap_profile_orchestrator.GAP_PROFILE_PATH",
        tmp_path / "gap_profile.json",
    )
    s = FinwizState()
    s.deep_analysis_results = {
        "AAPL": _dar("AAPL", grade="A", risk_score=1.0),
        "MSFT": _dar("MSFT", grade="B", risk_score=2.0),
        "JNJ": _dar("JNJ", grade="D", risk_score=4.0),
    }
    return s


def test_empty_results_yields_empty_profile() -> None:
    s = FinwizState()
    s.deep_analysis_results = {}
    out = GapProfileOrchestrator(s).build_gap_profile()
    assert out["is_empty"] is True
    assert s.portfolio_gap_profile["is_empty"] is True


def test_builds_sector_weights_and_underweight(state: FinwizState) -> None:
    GapProfileOrchestrator(state).build_gap_profile()
    profile = state.portfolio_gap_profile
    assert profile["is_empty"] is False
    # 2/3 Technology, 1/3 Healthcare
    assert profile["sector_weights"]["Technology"] == pytest.approx(2 / 3)
    assert profile["sector_weights"]["Healthcare"] == pytest.approx(1 / 3)
    # baseline = 1/2; Healthcare (0.33) < 0.5 -> underweight
    assert "Healthcare" in profile["underweight_sectors"]


def test_underperformer_slots_from_low_grades(state: FinwizState) -> None:
    GapProfileOrchestrator(state).build_gap_profile()
    slots = state.portfolio_gap_profile["underperformer_slots"]
    tickers = {s["ticker"] for s in slots}
    assert tickers == {"JNJ"}  # only the D-grade holding
    assert slots[0]["sector"] == "Healthcare"


def test_mean_risk_normalized_to_low_risk_scale(state: FinwizState) -> None:
    GapProfileOrchestrator(state).build_gap_profile()
    # risk_scores 1,2,4 on 0-5 (5=high) -> low-risk 0.8,0.6,0.2 -> mean ~0.533
    assert state.portfolio_gap_profile["mean_risk_score"] == pytest.approx((0.8 + 0.6 + 0.2) / 3)


def test_build_is_fail_soft(state: FinwizState, mocker) -> None:
    mocker.patch.object(GapProfileOrchestrator, "_compute_profile", side_effect=RuntimeError("boom"))
    out = GapProfileOrchestrator(state).build_gap_profile()
    assert out["is_empty"] is True
    assert state.portfolio_gap_profile["is_empty"] is True
