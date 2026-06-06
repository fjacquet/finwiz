"""
Monitoring Metrics for A+ Investment System.

This module provides performance tracking metrics and calculations
for A+ investment monitoring and analysis.
"""

from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any

from pydantic import BaseModel, Field

from finwiz.schemas.investment_discovery import APlusAnalysis, InvestmentCandidate
from finwiz.schemas.portfolio_review import Grade
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class PerformanceMetrics(BaseModel):
    """Performance tracking metrics for individual A+ investments."""

    # Investment identification
    symbol: str = Field(..., description="Investment symbol")
    asset_type: str = Field(..., description="Type of asset (stock, etf, crypto)")
    is_active: bool = Field(default=True, description="Whether investment is actively monitored")

    # Grade tracking
    recommendation_date: datetime = Field(..., description="Date of initial recommendation")
    initial_grade: str = Field(..., description="Initial grade at recommendation")
    current_grade: str = Field(..., description="Current grade")
    initial_score: float = Field(..., ge=0.0, le=1.0, description="Initial composite score")
    current_score: float = Field(..., ge=0.0, le=1.0, description="Current composite score")

    # Performance metrics
    total_return: float = Field(..., description="Total return since recommendation")
    annualized_return: float = Field(..., description="Annualized return")
    benchmark_return: float = Field(..., description="Benchmark return for comparison")
    alpha: float = Field(..., description="Excess return vs benchmark")
    sharpe_ratio: float = Field(..., description="Risk-adjusted return metric")
    max_drawdown: float = Field(..., description="Maximum drawdown experienced")

    # Metadata
    last_updated: datetime = Field(default_factory=datetime.now, description="Last metrics update")


class MetricsCalculator:
    """
    Calculator for A+ monitoring metrics.

    This class provides methods to calculate various performance and
    monitoring metrics for A+ investment recommendations.
    """

    def __init__(self) -> None:
        """Initialize the metrics calculator."""
        self.logger = get_logger(__name__)
        self._performance_history: deque = deque(maxlen=1000)
        self._grade_history: defaultdict = defaultdict(list)
        self._recommendation_history: list = []

    def calculate_performance_metrics(
        self,
        candidates: list[Any],
        analyses: list[APlusAnalysis],
        period_days: int = 30,
    ) -> PerformanceMetrics:
        """
        Calculate comprehensive performance metrics.

        Args:
            candidates: List of monitored investment objects
            analyses: List of A+ analyses
            period_days: Period for calculations in days

        Returns:
            PerformanceMetrics with calculated values

        """
        cutoff_date = datetime.now() - timedelta(days=period_days)

        # Filter recent data - use added_date for monitored investments
        recent_candidates = [c for c in candidates if hasattr(c, "added_date") and c.added_date >= cutoff_date]
        recent_analyses = [a for a in analyses if hasattr(a, "candidate") and a.candidate.discovery_date >= cutoff_date]

        # Basic counts
        total_recommendations = len(recent_analyses)
        active_positions = len([c for c in recent_candidates if c.current_grade == Grade.A_PLUS])

        # Performance calculations
        returns = [self._calculate_return(candidate) for candidate in recent_candidates]
        average_return = sum(returns) / len(returns) if returns else 0.0

        successful_recommendations = len([r for r in returns if r > 0])
        success_rate = (successful_recommendations / total_recommendations * 100) if total_recommendations > 0 else 0.0

        # Risk-adjusted metrics
        sharpe_ratio = self._calculate_sharpe_ratio(returns)

        # Grade distribution
        grade_distribution = self._calculate_grade_distribution(recent_candidates)

        # Degradation rate
        grade_degradation_rate = self._calculate_degradation_rate(recent_candidates, period_days)

        # Timing metrics
        average_hold_period = self._calculate_average_hold_period(recent_candidates)
        time_to_degradation = self._calculate_time_to_degradation(recent_candidates)

        # Market context
        market_correlation = self._calculate_market_correlation(returns)
        sector_performance = self._calculate_sector_performance(recent_candidates)

        return PerformanceMetrics(
            total_recommendations=total_recommendations,
            active_positions=active_positions,
            average_return=average_return,
            success_rate=success_rate,
            sharpe_ratio=sharpe_ratio,
            grade_distribution=grade_distribution,
            grade_degradation_rate=grade_degradation_rate,
            average_hold_period=average_hold_period,
            time_to_degradation=time_to_degradation,
            market_correlation=market_correlation,
            sector_performance=sector_performance,
            last_updated=datetime.now(),
            calculation_period_days=period_days,
        )

    def track_performance_event(self, monitored_inv: Any, event_type: str, value: float) -> None:
        """
        Track a performance event for metrics calculation.

        Args:
            monitored_inv: Monitored investment object
            event_type: Type of event (return, grade_change, etc.)
            value: Event value

        """
        event = {
            "timestamp": datetime.now(),
            "candidate_id": monitored_inv.symbol,
            "event_type": event_type,
            "value": value,
            "grade": monitored_inv.current_grade if hasattr(monitored_inv, "current_grade") else None,
        }

        self._performance_history.append(event)
        self.logger.debug(f"Tracked performance event: {event_type} for {monitored_inv.symbol}")

    def _calculate_return(self, monitored_inv: Any) -> float:
        """Calculate return for a monitored investment (simplified)."""
        # This is a simplified calculation - in practice would use actual price data
        base_return = 0.08  # 8% base return

        # Adjust based on grade
        current_grade = monitored_inv.current_grade if hasattr(monitored_inv, "current_grade") else Grade.B

        if current_grade == Grade.A_PLUS:
            return base_return * 1.2
        elif current_grade == Grade.A:
            return base_return * 1.0
        elif current_grade == Grade.B_PLUS:
            return base_return * 0.8
        else:
            return base_return * 0.6

    def _calculate_sharpe_ratio(self, returns: list[float]) -> float:
        """Calculate Sharpe ratio from returns."""
        if len(returns) < 2:
            return 0.0

        import statistics

        mean_return = statistics.mean(returns)
        std_return = statistics.stdev(returns) if len(returns) > 1 else 0.0
        risk_free_rate = 0.02  # 2% risk-free rate

        if std_return == 0:
            return 0.0

        return (mean_return - risk_free_rate) / std_return

    def _calculate_grade_distribution(self, candidates: list[Any]) -> dict[str, int]:
        """Calculate distribution of grades."""
        distribution = defaultdict(int)

        for candidate in candidates:
            current_grade = candidate.current_grade if hasattr(candidate, "current_grade") else None
            grade_str = current_grade.value if current_grade else "ungraded"
            distribution[grade_str] += 1

        return dict(distribution)

    def _calculate_degradation_rate(self, candidates: list[Any], period_days: int) -> float:
        """Calculate grade degradation rate."""
        # Simplified calculation - would need historical grade data
        a_plus_candidates = [c for c in candidates if hasattr(c, "current_grade") and c.current_grade == Grade.A_PLUS]

        if not a_plus_candidates:
            return 0.0

        # Estimate degradation rate (simplified)
        estimated_degradations = len(a_plus_candidates) * 0.1  # 10% degradation rate assumption
        monthly_rate = (estimated_degradations / len(a_plus_candidates)) * (30 / period_days)

        return monthly_rate

    def _calculate_average_hold_period(self, candidates: list[Any]) -> float:
        """Calculate average holding period."""
        # Simplified calculation - would need actual position data
        if not candidates:
            return 0.0

        # Estimate based on added dates
        hold_periods = []
        for candidate in candidates:
            if hasattr(candidate, "added_date"):
                days_since_added = (datetime.now() - candidate.added_date).days
                hold_periods.append(days_since_added)

        return sum(hold_periods) / len(hold_periods) if hold_periods else 0.0

    def _calculate_time_to_degradation(self, candidates: list[InvestmentCandidate]) -> float:
        """Calculate average time to grade degradation."""
        # Simplified calculation - would need historical degradation data
        return 45.0  # Placeholder: 45 days average

    def _calculate_market_correlation(self, returns: list[float]) -> float:
        """Calculate correlation with market."""
        # Simplified calculation - would need market data
        if len(returns) < 2:
            return 0.0

        # Placeholder correlation
        return 0.65  # Moderate positive correlation

    def _calculate_sector_performance(self, candidates: list[InvestmentCandidate]) -> dict[str, float]:
        """Calculate performance by sector."""
        sector_performance = defaultdict(list)

        for candidate in candidates:
            sector = getattr(candidate, "sector", "Unknown")
            performance = self._calculate_return(candidate)
            sector_performance[sector].append(performance)

        # Calculate average performance per sector
        return {sector: sum(performances) / len(performances) for sector, performances in sector_performance.items()}
