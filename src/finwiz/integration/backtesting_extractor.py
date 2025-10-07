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

    annualized_return: float | None = Field(None, description="Annualized return percentage")
    sharpe_ratio: float | None = Field(None, description="Sharpe ratio")
    sortino_ratio: float | None = Field(None, description="Sortino ratio")
    calmar_ratio: float | None = Field(None, description="Calmar ratio")
    max_drawdown: float | None = Field(None, description="Maximum drawdown percentage")
    win_rate: float | None = Field(None, description="Win rate percentage")
    backtest_period_years: int | None = Field(None, ge=1, description="Years of backtesting data")
    total_trades: int | None = Field(None, description="Total number of trades")


class RegimePerformance(BaseModel):
    """Performance metrics for a specific market regime."""

    regime_type: str = Field(..., description="Market regime type (bull/bear/sideways/volatile)")
    annualized_return: float | None = Field(None, description="Annualized return in this regime")
    sharpe_ratio: float | None = Field(None, description="Sharpe ratio in this regime")
    max_drawdown: float | None = Field(None, description="Maximum drawdown in this regime")
    win_rate: float | None = Field(None, description="Win rate in this regime")
    consistency_score: float | None = Field(None, description="Performance consistency")


class RiskAdjustedMetrics(BaseModel):
    """Risk-adjusted performance metrics."""

    sharpe_ratio: float | None = Field(None, description="Sharpe ratio")
    sortino_ratio: float | None = Field(None, description="Sortino ratio")
    calmar_ratio: float | None = Field(None, description="Calmar ratio")
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
            # Extract core metrics from validation result, using None for unavailable metrics
            annualized_return = self._safe_extract_float(
                self._calculate_average_return(validation_result), "annualized_return"
            )
            sharpe_ratio = self._safe_extract_float(
                validation_result.average_sharpe_ratio, "sharpe_ratio"
            )
            sortino_ratio = self._safe_extract_float(
                validation_result.average_sortino_ratio, "sortino_ratio"
            )
            max_drawdown = self._safe_extract_float(
                validation_result.average_max_drawdown, "max_drawdown"
            )
            win_rate = self._safe_extract_float(
                self._calculate_win_rate(validation_result), "win_rate"
            )
            calmar_ratio = self._safe_extract_float(
                self._calculate_calmar_ratio(validation_result), "calmar_ratio"
            )
            
            metrics = BacktestingMetrics(
                annualized_return=annualized_return,
                sharpe_ratio=sharpe_ratio,
                sortino_ratio=sortino_ratio,
                calmar_ratio=calmar_ratio,
                max_drawdown=max_drawdown,
                win_rate=win_rate,
                backtest_period_years=validation_result.backtest_period_years,
                total_trades=self._extract_total_trades(validation_result),
            )

            # Log which metrics are available and which are missing
            available = [k for k, v in metrics.model_dump().items() if v is not None]
            missing = [k for k, v in metrics.model_dump().items() if v is None]
            
            self.logger.info(f"Extracted backtesting metrics: {len(available)} available, {len(missing)} missing")
            if available:
                self.logger.info(f"Available metrics: {', '.join(available)}")
            if missing:
                self.logger.warning(f"Missing metrics: {', '.join(missing)}")
            
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
            sharpe = self._safe_extract_float(validation_result.average_sharpe_ratio, "sharpe_ratio")
            sortino = self._safe_extract_float(validation_result.average_sortino_ratio, "sortino_ratio")
            calmar = self._safe_extract_float(self._calculate_calmar_ratio(validation_result), "calmar_ratio")
            
            metrics = RiskAdjustedMetrics(
                sharpe_ratio=sharpe,
                sortino_ratio=sortino,
                calmar_ratio=calmar,
                information_ratio=self._extract_information_ratio(validation_result),
                alpha=self._extract_alpha(validation_result),
                beta=self._extract_beta(validation_result),
            )

            # Log which metrics are available
            available = [k for k, v in metrics.model_dump().items() if v is not None]
            missing = [k for k, v in metrics.model_dump().items() if v is None]
            
            if available:
                self.logger.info(f"Extracted risk-adjusted metrics: {', '.join(available)}")
            if missing:
                self.logger.warning(f"Missing risk-adjusted metrics: {', '.join(missing)}")
            
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

    def get_available_metrics(self, metrics: BacktestingMetrics | None) -> dict[str, Any]:
        """
        Get dictionary of available metrics with None for missing values.

        Args:
            metrics: BacktestingMetrics object or None

        Returns:
            Dictionary with all metric keys, None for unavailable metrics

        """
        if metrics is None:
            self.logger.warning("No backtesting metrics available")
            return {
                "annualized_return": None,
                "sharpe_ratio": None,
                "sortino_ratio": None,
                "calmar_ratio": None,
                "max_drawdown": None,
                "win_rate": None,
                "backtest_period_years": None,
                "total_trades": None,
            }
        
        return metrics.model_dump()

    def format_for_display(self, metrics: BacktestingMetrics | None) -> str:
        """
        Format backtesting metrics for display in reports.

        Shows actual values when available, "Not calculated" for None values.

        Args:
            metrics: BacktestingMetrics object or None

        Returns:
            Formatted string for report display

        """
        if metrics is None:
            return "Backtesting data not available"
        
        lines = []
        
        # Annualized Return
        if metrics.annualized_return is not None:
            lines.append(f"Annualized Return: {metrics.annualized_return:.2f}%")
        else:
            lines.append("Annualized Return: Not calculated")
        
        # Sharpe Ratio
        if metrics.sharpe_ratio is not None:
            lines.append(f"Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
        else:
            lines.append("Sharpe Ratio: Not calculated")
        
        # Sortino Ratio
        if metrics.sortino_ratio is not None:
            lines.append(f"Sortino Ratio: {metrics.sortino_ratio:.2f}")
        else:
            lines.append("Sortino Ratio: Not calculated")
        
        # Calmar Ratio
        if metrics.calmar_ratio is not None:
            lines.append(f"Calmar Ratio: {metrics.calmar_ratio:.2f}")
        else:
            lines.append("Calmar Ratio: Not calculated")
        
        # Max Drawdown
        if metrics.max_drawdown is not None:
            lines.append(f"Max Drawdown: {metrics.max_drawdown:.2f}%")
        else:
            lines.append("Max Drawdown: Not calculated")
        
        # Win Rate
        if metrics.win_rate is not None:
            lines.append(f"Win Rate: {metrics.win_rate * 100:.2f}%")
        else:
            lines.append("Win Rate: Not calculated")
        
        # Backtest Period
        if metrics.backtest_period_years is not None:
            lines.append(f"Backtest Period: {metrics.backtest_period_years} years")
        else:
            lines.append("Backtest Period: Not specified")
        
        # Total Trades
        if metrics.total_trades is not None:
            lines.append(f"Total Trades: {metrics.total_trades}")
        else:
            lines.append("Total Trades: Not calculated")
        
        return "\n".join(lines)

    # Private helper methods

    def _safe_extract_float(self, value: Any, metric_name: str) -> float | None:
        """
        Safely extract float value, returning None if unavailable or invalid.

        Args:
            value: Value to extract
            metric_name: Name of the metric for logging

        Returns:
            Float value or None if unavailable

        """
        if value is None:
            self.logger.debug(f"Metric '{metric_name}' is None")
            return None
        
        # Check for string placeholders that should be None
        if isinstance(value, str):
            self.logger.warning(
                f"Metric '{metric_name}' is a string ('{value}'), converting to None"
            )
            return None
        
        try:
            float_value = float(value)
            # Check for NaN or infinite values
            if not (-1e10 < float_value < 1e10):
                self.logger.warning(
                    f"Metric '{metric_name}' has invalid value {float_value}, converting to None"
                )
                return None
            return float_value
        except (ValueError, TypeError) as e:
            self.logger.warning(
                f"Could not convert metric '{metric_name}' to float: {e}, returning None"
            )
            return None

    def _calculate_average_return(self, validation_result: ValidationResult) -> float | None:
        """Calculate average annualized return from validation details."""
        if not validation_result.validation_details:
            self.logger.debug("No validation details available for average return calculation")
            return None

        returns = [
            detail.get("annualized_return")
            for detail in validation_result.validation_details
            if "annualized_return" in detail and detail.get("annualized_return") is not None
        ]

        if not returns:
            self.logger.debug("No annualized return values found in validation details")
            return None
        
        return sum(returns) / len(returns)

    def _calculate_win_rate(self, validation_result: ValidationResult) -> float | None:
        """Calculate average win rate from validation details."""
        if not validation_result.validation_details:
            self.logger.debug("No validation details available for win rate calculation")
            return None

        win_rates = [
            detail.get("win_rate")
            for detail in validation_result.validation_details
            if "win_rate" in detail and detail.get("win_rate") is not None
        ]

        if not win_rates:
            self.logger.debug("No win rate values found in validation details")
            return None
        
        return sum(win_rates) / len(win_rates)

    def _calculate_calmar_ratio(self, validation_result: ValidationResult) -> float | None:
        """Calculate Calmar ratio (return / abs(max_drawdown))."""
        avg_return = self._calculate_average_return(validation_result)
        max_dd = validation_result.average_max_drawdown
        
        if avg_return is None or max_dd is None:
            self.logger.debug("Cannot calculate Calmar ratio: missing return or drawdown data")
            return None
        
        abs_max_dd = abs(max_dd)
        if abs_max_dd == 0:
            self.logger.debug("Cannot calculate Calmar ratio: max drawdown is zero")
            return None
        
        return avg_return / abs_max_dd

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
            self.logger.warning("No candidates to aggregate metrics from")
            return BacktestingMetrics(
                annualized_return=None,
                sharpe_ratio=None,
                sortino_ratio=None,
                calmar_ratio=None,
                max_drawdown=None,
                win_rate=None,
                backtest_period_years=validation_results[0].backtest_period_years if validation_results else None,
                total_trades=None,
            )

        # Weighted average based on number of candidates, handling None values
        returns = [
            (self._calculate_average_return(vr), vr.total_candidates)
            for vr in validation_results
            if self._calculate_average_return(vr) is not None
        ]
        avg_return = (
            sum(r * c for r, c in returns) / sum(c for _, c in returns)
            if returns else None
        )

        sharpes = [
            (vr.average_sharpe_ratio, vr.total_candidates)
            for vr in validation_results
            if vr.average_sharpe_ratio is not None
        ]
        avg_sharpe = (
            sum(s * c for s, c in sharpes) / sum(c for _, c in sharpes)
            if sharpes else None
        )

        drawdowns = [
            (vr.average_max_drawdown, vr.total_candidates)
            for vr in validation_results
            if vr.average_max_drawdown is not None
        ]
        avg_drawdown = (
            sum(d * c for d, c in drawdowns) / sum(c for _, c in drawdowns)
            if drawdowns else None
        )

        sortinos = [
            (vr.average_sortino_ratio, vr.total_candidates)
            for vr in validation_results
            if vr.average_sortino_ratio is not None
        ]
        avg_sortino = (
            sum(s * c for s, c in sortinos) / sum(c for _, c in sortinos)
            if sortinos else None
        )

        win_rates = [
            (self._calculate_win_rate(vr), vr.total_candidates)
            for vr in validation_results
            if self._calculate_win_rate(vr) is not None
        ]
        avg_win_rate = (
            sum(w * c for w, c in win_rates) / sum(c for _, c in win_rates)
            if win_rates else None
        )

        # Calculate Calmar ratio if we have both return and drawdown
        calmar = None
        if avg_return is not None and avg_drawdown is not None and avg_drawdown != 0:
            calmar = avg_return / abs(avg_drawdown)

        # Use the most common backtest period
        backtest_years = max(
            (vr.backtest_period_years for vr in validation_results if vr.backtest_period_years is not None),
            default=None
        )

        return BacktestingMetrics(
            annualized_return=avg_return,
            sharpe_ratio=avg_sharpe,
            sortino_ratio=avg_sortino,
            calmar_ratio=calmar,
            max_drawdown=avg_drawdown,
            win_rate=avg_win_rate,
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
