"""
Feedback Analytics Module.

Handles all statistical calculations and metrics for feedback analysis.
"""

from typing import Any

import pandas as pd

from finwiz.schemas.feedback import PerformanceFeedback, PerformanceOutcome, RecommendationOutcome, UserFeedback
from finwiz.schemas.portfolio_review import Grade


class FeedbackAnalytics:
    """Analytics engine for feedback data processing."""

    @staticmethod
    def calculate_acceptance_by_asset(feedback: list[UserFeedback]) -> dict[str, float]:
        """Calculate acceptance rates by asset type."""
        if not feedback:
            return {}

        # Convert to DataFrame for efficient groupby operations
        df = pd.DataFrame([{"asset_type": f.asset_type, "accepted": f.outcome == RecommendationOutcome.ACCEPTED} for f in feedback])

        # Use pandas groupby for efficient aggregation
        return df.groupby("asset_type")["accepted"].mean().to_dict()

    @staticmethod
    def calculate_acceptance_by_grade(feedback: list[UserFeedback]) -> dict[Grade, float]:
        """Calculate acceptance rates by grade."""
        if not feedback:
            return {}

        # Convert to DataFrame for efficient groupby operations
        df = pd.DataFrame([{"grade": f.recommended_grade, "accepted": f.outcome == RecommendationOutcome.ACCEPTED} for f in feedback])

        # Use pandas groupby for efficient aggregation
        return df.groupby("grade")["accepted"].mean().to_dict()

    @staticmethod
    def calculate_acceptance_trends(feedback: list[UserFeedback]) -> dict[str, float]:
        """Calculate acceptance rate trends over time."""
        if len(feedback) < 10:
            return {"trend": 0.0, "recent_rate": 0.0, "historical_rate": 0.0}

        # Convert to DataFrame and sort by timestamp
        df = pd.DataFrame([{"timestamp": f.timestamp, "accepted": f.outcome == RecommendationOutcome.ACCEPTED} for f in feedback]).sort_values("timestamp")

        midpoint = len(df) // 2

        # Use pandas Series.mean() for vectorized calculation
        recent_rate = df.iloc[midpoint:]["accepted"].mean()
        historical_rate = df.iloc[:midpoint]["accepted"].mean()

        return {
            "trend": recent_rate - historical_rate,
            "recent_rate": recent_rate,
            "historical_rate": historical_rate,
        }

    @staticmethod
    def calculate_performance_by_asset(performance: list[PerformanceFeedback]) -> dict[str, dict[str, float]]:
        """Calculate performance metrics by asset type."""
        if not performance:
            return {}

        # Convert to DataFrame with asset type inference
        data = []
        for p in performance:
            # Simple heuristic - could be improved
            if p.symbol.endswith("-USD") or p.symbol in ["BTC-USD", "ETH-USD"]:
                asset_type = "crypto"
            elif len(p.symbol) <= 4 and p.symbol.isupper():
                asset_type = "stock"
            else:
                asset_type = "etf"

            data.append(
                {
                    "asset_type": asset_type,
                    "absolute_return": p.absolute_return,
                    "alpha": p.alpha,
                    "outperformed": p.performance_outcome == PerformanceOutcome.OUTPERFORMED,
                    "grade_maintained": p.grade_maintained,
                }
            )

        df = pd.DataFrame(data)

        # Use pandas groupby for efficient aggregation
        result = {}
        for asset_type, group in df.groupby("asset_type"):
            result[asset_type] = {
                "avg_return": group["absolute_return"].mean(),
                "avg_alpha": group["alpha"].mean(),
                "outperformance_rate": group["outperformed"].mean(),
                "grade_maintenance_rate": group["grade_maintained"].mean(),
            }

        return result

    @staticmethod
    def identify_top_performers(performance: list[PerformanceFeedback]) -> list[dict[str, Any]]:
        """Identify top performing recommendations."""
        sorted_performance = sorted(performance, key=lambda p: p.alpha, reverse=True)

        return [
            {
                "symbol": p.symbol,
                "alpha": p.alpha,
                "absolute_return": p.absolute_return,
                "holding_period_days": p.holding_period_days,
                "grade_maintained": p.grade_maintained,
            }
            for p in sorted_performance[:5]
        ]

    @staticmethod
    def identify_underperformers(performance: list[PerformanceFeedback]) -> list[dict[str, Any]]:
        """Identify underperforming recommendations."""
        sorted_performance = sorted(performance, key=lambda p: p.alpha)

        return [
            {
                "symbol": p.symbol,
                "alpha": p.alpha,
                "absolute_return": p.absolute_return,
                "holding_period_days": p.holding_period_days,
                "grade_maintained": p.grade_maintained,
            }
            for p in sorted_performance[:5]
        ]

    @staticmethod
    def calculate_acceptance_rate(feedback: list[UserFeedback]) -> float:
        """Calculate acceptance rate for feedback list."""
        if not feedback:
            return 0.0

        # Use pandas Series for vectorized calculation
        accepted_series = pd.Series([f.outcome == RecommendationOutcome.ACCEPTED for f in feedback])
        return accepted_series.mean()

    @staticmethod
    def calculate_outperformance_rate(performance: list[PerformanceFeedback]) -> float:
        """Calculate outperformance rate for performance list."""
        if not performance:
            return 0.0

        # Use pandas Series for vectorized calculation
        outperformed_series = pd.Series([p.performance_outcome == PerformanceOutcome.OUTPERFORMED for p in performance])
        return outperformed_series.mean()
