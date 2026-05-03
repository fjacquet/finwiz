"""Quantify stage attaches price_targets when price_history is available (ADR-011)."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from finwiz.analysis.deep_analysis_pipeline import AnalysisContext
from finwiz.analysis.stages.quantify import calculate_quantitative
from finwiz.flow_state_models import DeepAnalysisResult


class _FakeScorer:
    """Stand-in for DeepAnalysisScorer to avoid heavy real-data setup."""

    def calculate_composite_score(self, ticker: str, asset_class: str, raw: dict[str, Any]) -> DeepAnalysisResult:
        return DeepAnalysisResult.model_construct(
            ticker=ticker,
            asset_class=asset_class,
            crew_name="test",
            composite_score=0.7,
            grade="B",
            recommendation="HOLD",
            rationale="placeholder rationale long enough",
            risk_details={},
            fundamental_score=0.7,
            technical_score=0.7,
            risk_score=2.0,
            fundamental_details={},
            technical_details={},
            data_freshness_hours=0.5,
            confidence_level=0.9,
            warnings=[],
            data_quality=None,
            lineage=None,
            cached=False,
        )


def test_quantify_attaches_price_targets_when_history_available(mocker: Any) -> None:
    """When raw_data carries price_history + current_price, quantify attaches PriceTargets."""
    mocker.patch(
        "finwiz.scoring.deep_analysis_scorer.DeepAnalysisScorer",
        _FakeScorer,
    )
    end = pd.Timestamp.now().normalize()
    idx = pd.bdate_range(end=end, periods=250)
    prices = pd.Series(np.linspace(100.0, 130.0, len(idx)), index=idx, dtype=float)
    raw = {"current_price": 130.0, "price_history": prices}
    ctx = AnalysisContext(ticker="AAPL", asset_class="stock", company_name="Apple")
    _result, quant = calculate_quantitative(ctx, raw)
    assert quant.price_targets is not None
    assert quant.price_targets.buy_target_primary > 130.0
    assert quant.price_targets.sell_target_primary < 130.0


def test_quantify_no_price_targets_when_history_missing(mocker: Any) -> None:
    """When raw_data has no price_history, price_targets remains None — never crashes."""
    mocker.patch(
        "finwiz.scoring.deep_analysis_scorer.DeepAnalysisScorer",
        _FakeScorer,
    )
    raw = {"current_price": 130.0}  # no price_history key
    ctx = AnalysisContext(ticker="AAPL", asset_class="stock", company_name="Apple")
    _result, quant = calculate_quantitative(ctx, raw)
    assert quant.price_targets is None


def test_quantify_no_price_targets_when_current_price_missing(mocker: Any) -> None:
    """Without current_price the helper returns None — quantify must not crash."""
    mocker.patch(
        "finwiz.scoring.deep_analysis_scorer.DeepAnalysisScorer",
        _FakeScorer,
    )
    end = pd.Timestamp.now().normalize()
    idx = pd.bdate_range(end=end, periods=250)
    prices = pd.Series(np.linspace(100.0, 130.0, len(idx)), index=idx, dtype=float)
    raw = {"price_history": prices}  # no current_price
    ctx = AnalysisContext(ticker="AAPL", asset_class="stock", company_name="Apple")
    _result, quant = calculate_quantitative(ctx, raw)
    assert quant.price_targets is None


def test_quantify_swallows_tactical_pricing_failures(mocker: Any) -> None:
    """If tactical_pricing raises (any reason), quantify continues with price_targets=None."""
    mocker.patch(
        "finwiz.scoring.deep_analysis_scorer.DeepAnalysisScorer",
        _FakeScorer,
    )
    mocker.patch(
        "finwiz.quantitative.tactical_pricing.compute_tactical_pricing",
        side_effect=RuntimeError("simulated pricing crash"),
    )
    end = pd.Timestamp.now().normalize()
    idx = pd.bdate_range(end=end, periods=250)
    prices = pd.Series(np.linspace(100.0, 130.0, len(idx)), index=idx, dtype=float)
    raw = {"current_price": 130.0, "price_history": prices}
    ctx = AnalysisContext(ticker="AAPL", asset_class="stock", company_name="Apple")
    _result, quant = calculate_quantitative(ctx, raw)
    assert quant.price_targets is None  # graceful degradation, no exception
