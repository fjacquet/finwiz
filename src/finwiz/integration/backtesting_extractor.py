"""
Backtesting Data Extractor for extracting performance metrics from discovery crew validation results.

This module provides extraction logic for backtesting performance metrics including
annualized returns, Sharpe ratios, max drawdown, win rates, and regime-specific performance.
"""

import logging
from typing import Any

from pydantic import BaseModel, Field

from finwiz.schemas.investment_discovery import ValidationResult


class BacktestingMetrics(BaseModel):
    """Backtesting performance metrics from discovery crew validation."""

    annualized_return: float = Field(..., description="Annualized return percentage")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    max_drawdown: float = Field(..., le=0, description="Maximum drawdown percentage")
    win_rate: float = Field(..., ge=0, le=1, description="Win rate percentage")
    sortino_ratio: float | None = Field(None, description="Sortino ratio")
    calmar_ratio: float | None = Field(None, description="Calmar ratio")
    backtest_period_years: int = Field(..., ge=1, description="Years of backtesting data")
    total_trades: int | None = Field(None, description="Total number of trades")


class RegimePerformance(BaseModel):
    """Performance metrics for a specific market regime."""

    regime_type: str = Field(..., description="Market regime type (bull/bear/sideways/volatile)")
    annualized_return: float = Field(..., description="Annualized return in this regime")
    sharpe_ratio: float = Field(..., description="Sharpe ratio in this regime")
    max_drawdown: float = Field(..., le=0, description="Maximum drawdown in this regime")
    win_rate: float = Field(..., ge=0, le=1, description="Win rate in this regime")
    consistency_score: float = Field(..., ge=0, le=1, description="Performance consistency")


class RiskAdjustedMetrics(BaseModel):
    """Risk-adjusted performance metrics."""

    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    sortino_ratio: float = Field(..., description="Sortino ratio")
    calmar_ratio: float = Field(..., description="Calmar ratio")
    information_ratio: float | None = Field(None, description="Information ratio")
    alpha: float | None = Field(None, description="Alpha")
    beta: float | None = Field(None, description="Beta")


class BacktestingSummary(BaseModel):
    """Summary of backtesting results across all A+ candidates."""

    total_candidates_tested: int = Field(..., ge=0, description="Total candidates tested")
    average_metrics: BacktestingMetrics = Field(..., description="Average metrics across all candidates")
    regime_performance: dict[str, RegimePerformance] = Field(
        default_factory=dict, description="Performance by market regime"
    )
    best_performer: str = Field(..., description="Symbol of best performer")
    worst_performer: str = Field(..., description="Symbol of worst performer")


class BacktestingDataExtractor:
    """
    Extracts backtesting performance metrics from discovery crew validation results.

    This class provides methods to extract and structure backtesting data including
    annualized returns, risk-adjusted metrics, regime-specific performance, and
    comprehensive summaries for report integration.
    """

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """
        Initialize the backtesting data extractor.

        Args:
            logger: Optional logger instance for logging operations

        """
        self.logger = logger or logging.getLogger(__name__)
        self.logger.info("BacktestingDataExtractor initialized")

    def extract_backtesting_metrics(self, validation_result: ValidationResult) -> BacktestingMetrics | None:
        """
        Extract backtesting performance metrics from validation result.

        Args:
            validation_result: ValidationResult containing backtesting data

        Returns:
            BacktestingMetrics with extracted performance data, or None if unavailable

        """
        try:
            # Extract core metrics from validation result
            metrics = BacktestingMetrics(
                annualized_return=self._calculate_average_return(validation_result),
                sharpe_ratio=validation_result.average_sharpe_ratio,
                max_drawdown=validation_result.average_max_drawdown,
                win_rate=self._calculate_win_rate(validation_result),
                sortino_ratio=validation_result.average_sortino_ratio,
                calmar_ratio=self._calculate_calmar_ratio(validation_result),
                backtest_period_years=validation_result.backtest_period_years,
                total_trades=self._extract_total_trades(validation_result),
            )

            self.logger.info(
                f"Extracted backtesting metrics: {metrics.annualized_return:.2f}% return, "
                f"Sharpe {metrics.sharpe_ratio:.2f}"
            )
            return metrics

        except Exception as e:
            self.logger.error(f"Failed to extract backtesting metrics: {e}")
            return None

    def extract_regime_performance(self, validation_result: ValidationResult) -> dict[str, RegimePerformance]:
        """
        Extract performance metrics for each market regime from validation results.

        Args:
            validation_result: ValidationResult containing regime-specific data

        Returns:
            Dictionary mapping regime type to RegimePerformance metrics

        """
        regime_performance: dict[str, RegimePerformance] = {}

        try:
            # Extract regime-specific performance from validation details
            for regime in validation_result.market_regimes_tested:
                regime_data = self._extract_regime_data(validation_result, regime)

                if regime_data:
                    regime_performance[regime] = RegimePerformance(
                        regime_type=regime,
                        annualized_return=regime_data.get("annualized_return", 0.0),
                        sharpe_ratio=regime_data.get("sharpe_ratio", 0.0),
                        max_drawdown=regime_data.get("max_drawdown", 0.0),
                        win_rate=regime_data.get("win_rate", 0.0),
                        consistency_score=self._calculate_consistency_score(regime_data),
                    )

            self.logger.info(f"Extracted regime performance for {len(regime_performance)} regimes")
            return regime_performance

        except Exception as e:
            self.logger.error(f"Failed to extract regime performance: {e}")
            return {}

    def extract_risk_adjusted_metrics(self, validation_result: ValidationResult) -> RiskAdjustedMetrics | None:
        """
        Extract risk-adjusted performance metrics (Sharpe, Sortino, Calmar ratios).

        Args:
            validation_result: ValidationResult containing risk-adjusted metrics

        Returns:
            RiskAdjustedMetrics with extracted data, or None if unavailable

        """
        try:
            metrics = RiskAdjustedMetrics(
                sharpe_ratio=validation_result.average_sharpe_ratio,
                sortino_ratio=validation_result.average_sortino_ratio,
                calmar_ratio=self._calculate_calmar_ratio(validation_result),
                information_ratio=self._extract_information_ratio(validation_result),
                alpha=self._extract_alpha(validation_result),
                beta=self._extract_beta(validation_result),
            )

            self.logger.info(
                f"Extracted risk-adjusted metrics: Sharpe {metrics.sharpe_ratio:.2f}, "
                f"Sortino {metrics.sortino_ratio:.2f}"
            )
            return metrics

        except Exception as e:
            self.logger.error(f"Failed to extract risk-adjusted metrics: {e}")
            return None

    def get_performance_summary(
        self, validation_results: list[ValidationResult]
    ) -> BacktestingSummary | None:
        """
        Generate comprehensive backtesting summary across all validation results.

        Args:
            validation_results: List of ValidationResult objects to summarize

        Returns:
            BacktestingSummary with aggregated metrics, or None if unavailable

        """
        if not validation_results:
            self.logger.warning("No validation results provided for summary")
            return None

        try:
            # Aggregate metrics across all validation results
            total_candidates = sum(vr.total_candidates for vr in validation_results)
            avg_metrics = self._aggregate_metrics(validation_results)
            regime_perf = self._aggregate_regime_performance(validation_results)
            best, worst = self._identify_best_worst_performers(validation_results)

            summary = BacktestingSummary(
                total_candidates_tested=total_candidates,
                average_metrics=avg_metrics,
                regime_performance=regime_perf,
                best_performer=best,
                worst_performer=worst,
            )

            self.logger.info(
                f"Generated backtesting summary for {total_candidates} candidates "
                f"across {len(validation_results)} validation results"
            )
            return summary

        except Exception as e:
            self.logger.error(f"Failed to generate performance summary: {e}")
            return None

    # Private helper methods

    def _calculate_average_return(self, validation_result: ValidationResult) -> float:
        """Calculate average annualized return from validation details."""
        if not validation_result.validation_details:
            return 0.0

        returns = [
            detail.get("annualized_return", 0.0)
            for detail in validation_result.validation_details
            if "annualized_return" in detail
        ]

        return sum(returns) / len(returns) if returns else 0.0

    def _calculate_win_rate(self, validation_result: ValidationResult) -> float:
        """Calculate average win rate from validation details."""
        if not validation_result.validation_details:
            return 0.0

        win_rates = [
            detail.get("win_rate", 0.0)
            for detail in validation_result.validation_details
            if "win_rate" in detail
        ]

        return sum(win_rates) / len(win_rates) if win_rates else 0.0

    def _calculate_calmar_ratio(self, validation_result: ValidationResult) -> float:
        """Calculate Calmar ratio (return / abs(max_drawdown))."""
        avg_return = self._calculate_average_return(validation_result)
        max_dd = abs(validation_result.average_max_drawdown)

        return avg_return / max_dd if max_dd > 0 else 0.0

    def _extract_total_trades(self, validation_result: ValidationResult) -> int | None:
        """Extract total number of trades from validation details."""
        if not validation_result.validation_details:
            return None

        trades = [
            detail.get("total_trades", 0)
            for detail in validation_result.validation_details
            if "total_trades" in detail
        ]

        return sum(trades) if trades else None

    def _extract_regime_data(self, validation_result: ValidationResult, regime: str) -> dict[str, Any] | None:
        """Extract performance data for a specific market regime."""
        for detail in validation_result.validation_details:
            regime_data = detail.get("regime_performance", {})
            if regime in regime_data:
                return regime_data[regime]

        return None

    def _calculate_consistency_score(self, regime_data: dict[str, Any]) -> float:
        """Calculate consistency score for regime performance."""
        # Consistency based on win rate and Sharpe ratio stability
        win_rate = regime_data.get("win_rate", 0.0)
        sharpe = regime_data.get("sharpe_ratio", 0.0)

        # Simple consistency metric: average of normalized win rate and Sharpe
        normalized_sharpe = min(sharpe / 2.0, 1.0) if sharpe > 0 else 0.0
        return (win_rate + normalized_sharpe) / 2.0

    def _extract_information_ratio(self, validation_result: ValidationResult) -> float | None:
        """Extract information ratio from validation details."""
        for detail in validation_result.validation_details:
            if "information_ratio" in detail:
                return detail["information_ratio"]
        return None

    def _extract_alpha(self, validation_result: ValidationResult) -> float | None:
        """Extract alpha from validation details."""
        for detail in validation_result.validation_details:
            if "alpha" in detail:
                return detail["alpha"]
        return None

    def _extract_beta(self, validation_result: ValidationResult) -> float | None:
        """Extract beta from validation details."""
        for detail in validation_result.validation_details:
            if "beta" in detail:
                return detail["beta"]
        return None

    def _aggregate_metrics(self, validation_results: list[ValidationResult]) -> BacktestingMetrics:
        """Aggregate metrics across multiple validation results."""
        total_candidates = sum(vr.total_candidates for vr in validation_results)

        # Handle case with no candidates
        if total_candidates == 0:
            return BacktestingMetrics(
                annualized_return=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                win_rate=0.0,
                sortino_ratio=0.0,
                calmar_ratio=0.0,
                backtest_period_years=validation_results[0].backtest_period_years if validation_results else 5,
                total_trades=None,
            )

        # Weighted average based on number of candidates
        avg_return = sum(
            self._calculate_average_return(vr) * vr.total_candidates for vr in validation_results
        ) / total_candidates

        avg_sharpe = sum(vr.average_sharpe_ratio * vr.total_candidates for vr in validation_results) / total_candidates

        avg_drawdown = (
            sum(vr.average_max_drawdown * vr.total_candidates for vr in validation_results) / total_candidates
        )

        avg_sortino = (
            sum(vr.average_sortino_ratio * vr.total_candidates for vr in validation_results) / total_candidates
        )

        avg_win_rate = sum(
            self._calculate_win_rate(vr) * vr.total_candidates for vr in validation_results
        ) / total_candidates

        # Use the most common backtest period
        backtest_years = max(vr.backtest_period_years for vr in validation_results)

        return BacktestingMetrics(
            annualized_return=avg_return,
            sharpe_ratio=avg_sharpe,
            max_drawdown=avg_drawdown,
            win_rate=avg_win_rate,
            sortino_ratio=avg_sortino,
            calmar_ratio=avg_return / abs(avg_drawdown) if avg_drawdown != 0 else 0.0,
            backtest_period_years=backtest_years,
            total_trades=None,  # Not aggregated
        )

    def _aggregate_regime_performance(
        self, validation_results: list[ValidationResult]
    ) -> dict[str, RegimePerformance]:
        """Aggregate regime performance across multiple validation results."""
        regime_data: dict[str, list[dict[str, Any]]] = {}

        # Collect all regime data
        for vr in validation_results:
            regime_perf = self.extract_regime_performance(vr)
            for regime, perf in regime_perf.items():
                if regime not in regime_data:
                    regime_data[regime] = []
                regime_data[regime].append(perf.model_dump())

        # Average across all results
        aggregated: dict[str, RegimePerformance] = {}
        for regime, perfs in regime_data.items():
            if perfs:
                aggregated[regime] = RegimePerformance(
                    regime_type=regime,
                    annualized_return=sum(p["annualized_return"] for p in perfs) / len(perfs),
                    sharpe_ratio=sum(p["sharpe_ratio"] for p in perfs) / len(perfs),
                    max_drawdown=sum(p["max_drawdown"] for p in perfs) / len(perfs),
                    win_rate=sum(p["win_rate"] for p in perfs) / len(perfs),
                    consistency_score=sum(p["consistency_score"] for p in perfs) / len(perfs),
                )

        return aggregated

    def _identify_best_worst_performers(self, validation_results: list[ValidationResult]) -> tuple[str, str]:
        """Identify best and worst performers by Sharpe ratio."""
        all_candidates: list[tuple[str, float]] = []

        for vr in validation_results:
            for detail in vr.validation_details:
                symbol = detail.get("symbol", "UNKNOWN")
                sharpe = detail.get("sharpe_ratio", 0.0)
                all_candidates.append((symbol, sharpe))

        if not all_candidates:
            return ("UNKNOWN", "UNKNOWN")

        # Sort by Sharpe ratio
        all_candidates.sort(key=lambda x: x[1], reverse=True)

        best = all_candidates[0][0]
        worst = all_candidates[-1][0]

        return (best, worst)
