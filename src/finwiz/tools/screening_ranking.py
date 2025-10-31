"""
Ranking algorithms for market screening candidates.

This module contains scoring and ranking algorithms used to evaluate
and rank investment candidates during market screening operations.
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from finwiz.tools.a_plus_scoring_tool import APlusScoringTool


class ScreeningCandidate(BaseModel):
    """A candidate investment from screening."""

    symbol: str
    name: str
    asset_type: Literal["etf", "stock", "crypto"]
    preliminary_score: float = Field(ge=0.0, le=1.0)
    meets_a_plus_criteria: bool
    key_metrics: dict[str, Any] = Field(default_factory=dict)
    screening_rationale: str
    data_source: str
    screened_at: datetime


class ScreeningRanking:
    """Ranking algorithms for screening candidates."""

    def __init__(self) -> None:
        """Initialize screening ranking."""
        self._a_plus_scorer = APlusScoringTool()

    def score_candidates(self, candidates: list[dict[str, Any]], asset_type: str, min_score: float, detailed_analysis: bool) -> list[ScreeningCandidate]:
        """Score filtered candidates using A+ scoring."""
        scored_candidates = []

        for candidate in candidates:
            try:
                symbol = candidate["symbol"]
                market_data = candidate["market_data"]

                # Calculate preliminary score
                if detailed_analysis:
                    # Use full A+ scoring tool
                    score_result = self._a_plus_scorer._run(
                        symbol=symbol,
                        asset_type=asset_type,
                        fundamental_data=market_data,
                        market_context={},
                    )
                    preliminary_score = score_result.get("composite_score", 0.5)
                else:
                    # Use simplified scoring for efficiency
                    preliminary_score = self.calculate_preliminary_score(market_data, asset_type)

                # Determine if meets A+ criteria
                meets_a_plus = preliminary_score >= min_score

                # Generate screening rationale
                from finwiz.tools.screening_utils import ScreeningUtils

                utils = ScreeningUtils()
                rationale = utils.generate_screening_rationale(market_data, asset_type, preliminary_score, meets_a_plus)

                # Extract key metrics
                key_metrics = utils.extract_key_metrics(market_data, asset_type)

                # Create candidate object
                screening_candidate = ScreeningCandidate(
                    symbol=symbol,
                    name=market_data.get("name", symbol),
                    asset_type=asset_type,
                    preliminary_score=preliminary_score,
                    meets_a_plus_criteria=meets_a_plus,
                    key_metrics=key_metrics,
                    screening_rationale=rationale,
                    data_source=market_data.get("source", "Market Data"),
                    screened_at=datetime.now(),
                )

                scored_candidates.append(screening_candidate)

            except Exception:
                # Skip candidates that fail scoring
                continue

        return scored_candidates

    def calculate_preliminary_score(self, market_data: dict[str, Any], asset_type: str) -> float:
        """Calculate simplified preliminary score for efficiency."""
        try:
            if asset_type == "etf":
                return self._score_etf_preliminary(market_data)
            elif asset_type == "stock":
                return self._score_stock_preliminary(market_data)
            elif asset_type == "crypto":
                return self._score_crypto_preliminary(market_data)
            else:
                return 0.5

        except Exception:
            return 0.5

    def _score_etf_preliminary(self, data: dict[str, Any]) -> float:
        """Calculate preliminary ETF score."""
        score = 0.0

        # Expense ratio (40% weight)
        expense_ratio = data.get("expense_ratio", 0.5)
        if expense_ratio <= 0.05:
            score += 0.4
        elif expense_ratio <= 0.15:
            score += 0.3
        elif expense_ratio <= 0.25:
            score += 0.2

        # AUM (30% weight)
        aum = data.get("aum", 0)
        if aum >= 10e9:
            score += 0.3
        elif aum >= 1e9:
            score += 0.2
        elif aum >= 500e6:
            score += 0.1

        # Tracking error (20% weight)
        tracking_error = data.get("tracking_error", 0.01)
        if tracking_error <= 0.001:
            score += 0.2
        elif tracking_error <= 0.002:
            score += 0.15
        elif tracking_error <= 0.005:
            score += 0.1

        # History (10% weight)
        history_years = data.get("history_years", 0)
        if history_years >= 10:
            score += 0.1
        elif history_years >= 5:
            score += 0.075
        elif history_years >= 3:
            score += 0.05

        return min(score, 1.0)

    def _score_stock_preliminary(self, data: dict[str, Any]) -> float:
        """Calculate preliminary stock score."""
        score = 0.0

        # ROE (30% weight)
        roe = data.get("roe", 0.1)
        if roe >= 0.25:
            score += 0.3
        elif roe >= 0.20:
            score += 0.25
        elif roe >= 0.15:
            score += 0.15

        # Revenue growth (25% weight)
        revenue_growth = data.get("revenue_growth", 0.05)
        if revenue_growth >= 0.20:
            score += 0.25
        elif revenue_growth >= 0.15:
            score += 0.2
        elif revenue_growth >= 0.10:
            score += 0.15

        # Debt management (20% weight)
        debt_to_equity = data.get("debt_to_equity", 0.5)
        if debt_to_equity <= 0.2:
            score += 0.2
        elif debt_to_equity <= 0.3:
            score += 0.15
        elif debt_to_equity <= 0.5:
            score += 0.1

        # Market cap (15% weight)
        market_cap = data.get("market_cap", 0)
        if market_cap >= 100e9:
            score += 0.15
        elif market_cap >= 10e9:
            score += 0.12
        elif market_cap >= 1e9:
            score += 0.08

        # Free cash flow (10% weight)
        if data.get("fcf_positive", False) and data.get("fcf_growing", False):
            score += 0.1
        elif data.get("fcf_positive", False):
            score += 0.05

        return min(score, 1.0)

    def _score_crypto_preliminary(self, data: dict[str, Any]) -> float:
        """Calculate preliminary crypto score."""
        score = 0.0

        # Market cap (35% weight)
        market_cap = data.get("market_cap", 0)
        if market_cap >= 100e9:
            score += 0.35
        elif market_cap >= 50e9:
            score += 0.3
        elif market_cap >= 10e9:
            score += 0.2

        # Daily volume (25% weight)
        daily_volume = data.get("daily_volume", 0)
        if daily_volume >= 2e9:
            score += 0.25
        elif daily_volume >= 1e9:
            score += 0.2
        elif daily_volume >= 500e6:
            score += 0.15

        # Age/Maturity (20% weight)
        age_months = data.get("age_months", 0)
        if age_months >= 60:
            score += 0.2
        elif age_months >= 36:
            score += 0.15
        elif age_months >= 24:
            score += 0.1

        # Institutional adoption (10% weight)
        if data.get("institutional_adoption", False):
            score += 0.1

        # Real utility (10% weight)
        if data.get("real_utility", False):
            score += 0.1

        return min(score, 1.0)
