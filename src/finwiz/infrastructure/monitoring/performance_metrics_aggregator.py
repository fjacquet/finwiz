"""
Performance Metrics Aggregator for aggregating backtesting metrics across asset types and regimes.

This module provides aggregation logic for performance metrics including asset type breakdowns,
regime-specific analysis, and portfolio-level impact calculations.
"""

import logging
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from finwiz.orchestrators.extraction.backtesting import (
    BacktestingDataExtractor,
    RegimePerformance,
)
from finwiz.schemas.investment_discovery import ValidationResult


class PerformanceMetrics(BaseModel):
    """Aggregated performance metrics for a specific category."""

    asset_type: Literal["etf", "stock", "crypto", "all"] = Field(description="Asset type category")
    count: int = Field(ge=0, description="Number of candidates in this category")
    average_return: float = Field(description="Average annualized return percentage")
    average_sharpe: float = Field(description="Average Sharpe ratio")
    average_max_drawdown: float = Field(le=0, description="Average maximum drawdown percentage")
    average_win_rate: float = Field(ge=0, le=1, description="Average win rate")
    best_performer: str | None = Field(None, description="Symbol of best performer in category")
    worst_performer: str | None = Field(None, description="Symbol of worst performer in category")


class PortfolioImpactMetrics(BaseModel):
    """Portfolio-level impact metrics from A+ opportunities."""

    expected_grade_improvement: float = Field(description="Expected grade improvement percentage")
    expected_return_improvement: float = Field(description="Expected return improvement percentage")
    risk_impact: Literal["reduced", "neutral", "increased"] = Field(description="Impact on portfolio risk")
    diversification_impact: Literal["improved", "neutral", "reduced"] = Field(description="Impact on portfolio diversification")
    implementation_complexity: Literal["low", "medium", "high"] = Field(description="Complexity of implementing recommendations")
    total_opportunities: int = Field(ge=0, description="Total number of A+ opportunities")
    high_confidence_count: int = Field(ge=0, description="Number of high-confidence opportunities (Sharpe > 1.5)")


class PerformanceReport(BaseModel):
    """Comprehensive performance report aggregating all metrics."""

    by_asset_type: dict[str, PerformanceMetrics] = Field(description="Metrics aggregated by asset type")
    by_regime: dict[str, PerformanceMetrics] = Field(description="Metrics aggregated by market regime")
    portfolio_impact: PortfolioImpactMetrics = Field(description="Portfolio-level impact assessment")
    top_opportunities: list[str] = Field(description="Top 5 opportunities by composite score")
    report_timestamp: datetime = Field(description="When this report was generated")
    total_candidates_analyzed: int = Field(ge=0, description="Total number of candidates analyzed")
    data_quality_score: float = Field(ge=0, le=1, description="Overall data quality score")


class PerformanceMetricsAggregator:
    """
    Aggregates performance metrics across asset types and market regimes.

    This class provides methods to aggregate backtesting metrics by asset type,
    market regime, and calculate portfolio-level impact from A+ opportunities.
    """

    def __init__(self, backtesting_extractor: BacktestingDataExtractor, logger: logging.Logger | None = None) -> None:
        """
        Initialize the performance metrics aggregator.

        Args:
            backtesting_extractor: BacktestingDataExtractor instance for extracting metrics
            logger: Optional logger instance for logging operations

        """
        self.backtesting_extractor = backtesting_extractor
        self.logger = logger or logging.getLogger(__name__)
        self.logger.info("PerformanceMetricsAggregator initialized")

    def aggregate_by_asset_type(self, validation_results: list[ValidationResult], asset_type_map: dict[str, str]) -> dict[str, PerformanceMetrics]:
        """
        Aggregate performance metrics by asset type (ETF, stock, crypto).

        Args:
            validation_results: List of ValidationResult objects to aggregate
            asset_type_map: Dictionary mapping symbols to asset types

        Returns:
            Dictionary mapping asset type to PerformanceMetrics

        """
        self.logger.info(f"Aggregating metrics by asset type for {len(validation_results)} validation results")

        # Group validation results by asset type
        grouped_results: dict[str, list[ValidationResult]] = {"etf": [], "stock": [], "crypto": []}

        for vr in validation_results:
            for detail in vr.validation_details:
                symbol = detail.get("symbol", "UNKNOWN")
                asset_type = asset_type_map.get(symbol, "stock")  # Default to stock if unknown

                if asset_type in grouped_results:
                    # Create a single-candidate validation result for this symbol
                    single_vr = self._create_single_validation_result(vr, detail)
                    grouped_results[asset_type].append(single_vr)

        # Aggregate metrics for each asset type
        aggregated: dict[str, PerformanceMetrics] = {}

        for asset_type, results in grouped_results.items():
            if results:
                metrics = self._aggregate_validation_results(results, asset_type)
                aggregated[asset_type] = metrics
                self.logger.info(f"Aggregated {len(results)} candidates for {asset_type}: avg return {metrics.average_return:.2f}%, Sharpe {metrics.average_sharpe:.2f}")

        # Add "all" category with overall metrics
        if validation_results:
            all_metrics = self._aggregate_validation_results(validation_results, "all")
            aggregated["all"] = all_metrics

        return aggregated

    def aggregate_by_regime(self, validation_results: list[ValidationResult]) -> dict[str, PerformanceMetrics]:
        """
        Aggregate performance metrics by market regime (bull, bear, sideways).

        Args:
            validation_results: List of ValidationResult objects to aggregate

        Returns:
            Dictionary mapping regime type to PerformanceMetrics

        """
        self.logger.info(f"Aggregating metrics by regime for {len(validation_results)} validation results")

        # Extract regime performance from all validation results
        all_regime_data: dict[str, list[RegimePerformance]] = {}

        for vr in validation_results:
            regime_perf = self.backtesting_extractor.extract_regime_performance(vr)

            for regime, perf in regime_perf.items():
                if regime not in all_regime_data:
                    all_regime_data[regime] = []
                all_regime_data[regime].append(perf)

        # Aggregate metrics for each regime
        aggregated: dict[str, PerformanceMetrics] = {}

        for regime, perfs in all_regime_data.items():
            if perfs:
                metrics = self._aggregate_regime_performances(perfs, regime)
                aggregated[regime] = metrics
                self.logger.info(f"Aggregated {len(perfs)} candidates for {regime} regime: avg return {metrics.average_return:.2f}%, Sharpe {metrics.average_sharpe:.2f}")

        return aggregated

    def calculate_portfolio_impact(self, validation_results: list[ValidationResult], current_portfolio_grade: float = 0.70) -> PortfolioImpactMetrics:
        """
        Calculate portfolio-level impact metrics from A+ opportunities.

        Args:
            validation_results: List of ValidationResult objects
            current_portfolio_grade: Current portfolio grade (0.0 to 1.0)

        Returns:
            PortfolioImpactMetrics with impact assessment

        """
        self.logger.info(f"Calculating portfolio impact for {len(validation_results)} validation results")

        if not validation_results:
            return self._create_empty_portfolio_impact()

        # Extract all candidate metrics
        all_candidates: list[dict] = []
        for vr in validation_results:
            all_candidates.extend(vr.validation_details)

        total_opportunities = len(all_candidates)
        high_confidence_count = sum(1 for c in all_candidates if c.get("sharpe_ratio", 0) > 1.5)

        # Calculate expected improvements
        avg_return = sum(c.get("annualized_return", 0) for c in all_candidates) / max(total_opportunities, 1)
        avg_sharpe = sum(c.get("sharpe_ratio", 0) for c in all_candidates) / max(total_opportunities, 1)
        avg_drawdown = sum(c.get("max_drawdown", 0) for c in all_candidates) / max(total_opportunities, 1)

        # Estimate grade improvement (A+ candidates should improve grade)
        # Assume A+ candidates have grade ~0.85-0.95
        expected_new_grade = 0.90
        grade_improvement = ((expected_new_grade - current_portfolio_grade) / current_portfolio_grade) * 100

        # Estimate return improvement
        # Assume current portfolio return is market average (~10%)
        current_return = 10.0
        return_improvement = ((avg_return - current_return) / current_return) * 100

        # Assess risk impact based on Sharpe ratio
        risk_impact: Literal["reduced", "neutral", "increased"]
        if avg_sharpe > 1.2:
            risk_impact = "reduced"
        elif avg_sharpe > 0.8:
            risk_impact = "neutral"
        else:
            risk_impact = "increased"

        # Assess diversification impact
        # More opportunities generally improve diversification
        diversification_impact: Literal["improved", "neutral", "reduced"]
        if total_opportunities >= 5:
            diversification_impact = "improved"
        elif total_opportunities >= 2:
            diversification_impact = "neutral"
        else:
            diversification_impact = "reduced"

        # Assess implementation complexity
        implementation_complexity: Literal["low", "medium", "high"]
        if total_opportunities <= 3:
            implementation_complexity = "low"
        elif total_opportunities <= 7:
            implementation_complexity = "medium"
        else:
            implementation_complexity = "high"

        impact = PortfolioImpactMetrics(
            expected_grade_improvement=grade_improvement,
            expected_return_improvement=return_improvement,
            risk_impact=risk_impact,
            diversification_impact=diversification_impact,
            implementation_complexity=implementation_complexity,
            total_opportunities=total_opportunities,
            high_confidence_count=high_confidence_count,
        )

        self.logger.info(f"Portfolio impact: {grade_improvement:.1f}% grade improvement, {return_improvement:.1f}% return improvement, {total_opportunities} opportunities")

        return impact

    def generate_performance_report(
        self,
        validation_results: list[ValidationResult],
        asset_type_map: dict[str, str],
        current_portfolio_grade: float = 0.70,
    ) -> PerformanceReport:
        """
        Generate comprehensive performance report with all aggregations.

        Args:
            validation_results: List of ValidationResult objects
            asset_type_map: Dictionary mapping symbols to asset types
            current_portfolio_grade: Current portfolio grade (0.0 to 1.0)

        Returns:
            PerformanceReport with complete analysis

        """
        self.logger.info(f"Generating performance report for {len(validation_results)} validation results")

        # Aggregate by asset type and regime
        by_asset_type = self.aggregate_by_asset_type(validation_results, asset_type_map)
        by_regime = self.aggregate_by_regime(validation_results)

        # Calculate portfolio impact
        portfolio_impact = self.calculate_portfolio_impact(validation_results, current_portfolio_grade)

        # Identify top opportunities by composite score
        top_opportunities = self._identify_top_opportunities(validation_results, top_n=5)

        # Calculate data quality score
        data_quality = self._calculate_data_quality_score(validation_results)

        # Count total candidates
        total_candidates = sum(vr.total_candidates for vr in validation_results)

        report = PerformanceReport(
            by_asset_type=by_asset_type,
            by_regime=by_regime,
            portfolio_impact=portfolio_impact,
            top_opportunities=top_opportunities,
            report_timestamp=datetime.now(),
            total_candidates_analyzed=total_candidates,
            data_quality_score=data_quality,
        )

        self.logger.info(f"Performance report generated: {total_candidates} candidates, {len(top_opportunities)} top opportunities, quality score {data_quality:.2f}")

        return report

    # Private helper methods

    def _create_single_validation_result(self, vr: ValidationResult, detail: dict[str, Any]) -> ValidationResult:
        """Create a single-candidate validation result from a detail entry."""
        return ValidationResult(
            total_candidates=1,
            passed_validation=1 if detail.get("passed", True) else 0,
            failed_validation=0 if detail.get("passed", True) else 1,
            average_sharpe_ratio=detail.get("sharpe_ratio", 0.0),
            average_sortino_ratio=detail.get("sortino_ratio", 0.0),
            average_max_drawdown=detail.get("max_drawdown", 0.0),
            backtest_period_years=vr.backtest_period_years,
            market_regimes_tested=vr.market_regimes_tested,
            validation_details=[detail],
        )

    def _aggregate_validation_results(self, validation_results: list[ValidationResult], category: str) -> PerformanceMetrics:
        """Aggregate validation results into PerformanceMetrics."""
        if not validation_results:
            return PerformanceMetrics(
                asset_type=category,  # type: ignore
                count=0,
                average_return=0.0,
                average_sharpe=0.0,
                average_max_drawdown=0.0,
                average_win_rate=0.0,
            )

        # Extract all candidate details
        all_candidates: list[tuple[str, dict]] = []
        for vr in validation_results:
            for detail in vr.validation_details:
                symbol = detail.get("symbol", "UNKNOWN")
                all_candidates.append((symbol, detail))

        count = len(all_candidates)

        # Calculate averages
        avg_return = sum(d.get("annualized_return", 0) for _, d in all_candidates) / max(count, 1)
        avg_sharpe = sum(d.get("sharpe_ratio", 0) for _, d in all_candidates) / max(count, 1)
        avg_drawdown = sum(d.get("max_drawdown", 0) for _, d in all_candidates) / max(count, 1)
        avg_win_rate = sum(d.get("win_rate", 0) for _, d in all_candidates) / max(count, 1)

        # Identify best and worst performers by Sharpe ratio
        sorted_candidates = sorted(all_candidates, key=lambda x: x[1].get("sharpe_ratio", 0), reverse=True)
        best_performer = sorted_candidates[0][0] if sorted_candidates else None
        worst_performer = sorted_candidates[-1][0] if sorted_candidates else None

        return PerformanceMetrics(
            asset_type=category,  # type: ignore
            count=count,
            average_return=avg_return,
            average_sharpe=avg_sharpe,
            average_max_drawdown=avg_drawdown,
            average_win_rate=avg_win_rate,
            best_performer=best_performer,
            worst_performer=worst_performer,
        )

    def _aggregate_regime_performances(self, regime_perfs: list[RegimePerformance], regime: str) -> PerformanceMetrics:
        """Aggregate regime performances into PerformanceMetrics."""
        count = len(regime_perfs)

        avg_return = sum(p.annualized_return or 0.0 for p in regime_perfs) / count
        avg_sharpe = sum(p.sharpe_ratio or 0.0 for p in regime_perfs) / count
        avg_drawdown = sum(p.max_drawdown or 0.0 for p in regime_perfs) / count
        avg_win_rate = sum(p.win_rate or 0.0 for p in regime_perfs) / count

        # For regime aggregation, we don't track individual performers
        return PerformanceMetrics(
            asset_type="all",
            count=count,
            average_return=avg_return,
            average_sharpe=avg_sharpe,
            average_max_drawdown=avg_drawdown,
            average_win_rate=avg_win_rate,
        )

    def _create_empty_portfolio_impact(self) -> PortfolioImpactMetrics:
        """Create empty portfolio impact metrics when no data is available."""
        return PortfolioImpactMetrics(
            expected_grade_improvement=0.0,
            expected_return_improvement=0.0,
            risk_impact="neutral",
            diversification_impact="neutral",
            implementation_complexity="low",
            total_opportunities=0,
            high_confidence_count=0,
        )

    def _identify_top_opportunities(self, validation_results: list[ValidationResult], top_n: int = 5) -> list[str]:
        """Identify top N opportunities by composite score (Sharpe ratio * return)."""
        all_candidates: list[tuple[str, float]] = []

        for vr in validation_results:
            for detail in vr.validation_details:
                symbol = detail.get("symbol", "UNKNOWN")
                sharpe = detail.get("sharpe_ratio", 0.0)
                ret = detail.get("annualized_return", 0.0)

                # Composite score: Sharpe ratio weighted by return
                composite_score = sharpe * (1 + ret / 100)
                all_candidates.append((symbol, composite_score))

        # Sort by composite score and take top N
        sorted_candidates = sorted(all_candidates, key=lambda x: x[1], reverse=True)
        top_symbols = [symbol for symbol, _ in sorted_candidates[:top_n]]

        return top_symbols

    def _calculate_data_quality_score(self, validation_results: list[ValidationResult]) -> float:
        """Calculate overall data quality score based on validation results."""
        if not validation_results:
            return 0.0

        # Quality factors:
        # 1. Validation pass rate
        # 2. Completeness of data (presence of all metrics)
        # 3. Consistency across regimes

        total_candidates = sum(vr.total_candidates for vr in validation_results)
        passed_candidates = sum(vr.passed_validation for vr in validation_results)

        # Validation pass rate (0-0.4 weight)
        pass_rate = passed_candidates / max(total_candidates, 1)
        pass_score = pass_rate * 0.4

        # Data completeness (0-0.3 weight)
        completeness_scores = []
        for vr in validation_results:
            for detail in vr.validation_details:
                required_fields = ["annualized_return", "sharpe_ratio", "max_drawdown", "win_rate"]
                present_fields = sum(1 for field in required_fields if field in detail)
                completeness_scores.append(present_fields / len(required_fields))

        avg_completeness = sum(completeness_scores) / max(len(completeness_scores), 1)
        completeness_score = avg_completeness * 0.3

        # Regime consistency (0-0.3 weight)
        # Check if multiple regimes were tested
        regime_counts = [len(vr.market_regimes_tested) for vr in validation_results]
        avg_regimes = sum(regime_counts) / max(len(regime_counts), 1)
        regime_score = min(avg_regimes / 3.0, 1.0) * 0.3  # Normalize to 3 regimes

        total_score = pass_score + completeness_score + regime_score

        return min(total_score, 1.0)
