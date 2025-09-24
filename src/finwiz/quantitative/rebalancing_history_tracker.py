"""
Rebalancing history tracker for FinWiz portfolio rebalancing system.

This module provides functionality to track and analyze historical rebalancing
actions, including performance attribution, trend analysis, and optimization
recommendations.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
from pydantic import ValidationError

from finwiz.schemas.portfolio_rebalancing import (
    PerformanceAttribution,
    PositionHistory,
    RebalancingAnalytics,
    RebalancingHistoryEntry,
    RebalancingResult,
    TradeRecommendation,
    TrendAnalysis,
)
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class RebalancingHistoryTracker:
    """
    Tracks and analyzes historical rebalancing actions for portfolio optimization.

    This class provides comprehensive tracking of rebalancing history, performance
    attribution analysis, and trend identification for optimal rebalancing strategies.
    """

    def __init__(self, storage_path: str = "data/rebalancing_history") -> None:
        """
        Initialize the rebalancing history tracker.

        Args:
            storage_path: Path to store historical data files

        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized RebalancingHistoryTracker with storage path: {self.storage_path}")

    def record_rebalancing_action(
        self,
        portfolio_id: str,
        rebalancing_result: RebalancingResult,
        executed_trades: list[TradeRecommendation],
        execution_status: str = "COMPLETED",
        execution_notes: str | None = None,
    ) -> str:
        """
        Record a rebalancing action in the historical database.

        Args:
            portfolio_id: Unique identifier for the portfolio
            rebalancing_result: Complete rebalancing analysis result
            executed_trades: List of trades that were actually executed
            execution_status: Status of execution (COMPLETED, PARTIAL, FAILED)
            execution_notes: Optional notes about the execution

        Returns:
            Unique entry ID for the recorded action

        Raises:
            ValidationError: If the input data is invalid
            IOError: If unable to save the history entry

        """
        try:
            entry_id = str(uuid.uuid4())

            # Calculate metrics
            total_costs = sum(trade.total_estimated_cost for trade in executed_trades)
            positions_rebalanced = len([t for t in executed_trades if t.quantity > 0])

            # Calculate deviation improvement
            current_deviations = list(rebalancing_result.current_portfolio.deviations_from_target.values())
            projected_deviations = list(rebalancing_result.projected_portfolio.deviations_from_target.values())

            current_total_deviation = sum(abs(d) for d in current_deviations)
            projected_total_deviation = sum(abs(d) for d in projected_deviations)
            deviation_improvement = current_total_deviation - projected_total_deviation

            # Create history entry
            history_entry = RebalancingHistoryEntry(
                entry_id=entry_id,
                portfolio_id=portfolio_id,
                timestamp=datetime.now(),
                rebalancing_result=rebalancing_result,
                executed_trades=executed_trades,
                execution_status=execution_status,
                portfolio_value_before=rebalancing_result.current_portfolio.total_value,
                total_transaction_costs=total_costs,
                positions_rebalanced=positions_rebalanced,
                deviation_improvement=deviation_improvement,
                execution_notes=execution_notes,
            )

            # Save to file
            self._save_history_entry(history_entry)

            logger.info(
                f"Recorded rebalancing action for portfolio {portfolio_id}: "
                f"{positions_rebalanced} positions, ${total_costs:.2f} costs"
            )

            return entry_id

        except ValidationError as e:
            logger.error(f"Validation error recording rebalancing action: {e}")
            raise
        except Exception as e:
            logger.error(f"Error recording rebalancing action: {e}")
            raise OSError(f"Failed to record rebalancing action: {e}") from e

    def get_portfolio_history(
        self,
        portfolio_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[RebalancingHistoryEntry]:
        """
        Retrieve historical rebalancing entries for a portfolio.

        Args:
            portfolio_id: Portfolio identifier
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            List of historical rebalancing entries

        """
        try:
            history_file = self.storage_path / f"{portfolio_id}_history.json"

            if not history_file.exists():
                logger.info(f"No history file found for portfolio {portfolio_id}")
                return []

            with open(history_file, encoding="utf-8") as f:
                history_data = json.load(f)

            entries = []
            for entry_data in history_data:
                try:
                    entry = RebalancingHistoryEntry.model_validate(entry_data)

                    # Apply date filters
                    entry_timestamp = entry.timestamp
                    if isinstance(entry_timestamp, str):
                        entry_timestamp = datetime.fromisoformat(entry_timestamp.replace("Z", "+00:00"))

                    if start_date and entry_timestamp < start_date:
                        continue
                    if end_date and entry_timestamp > end_date:
                        continue

                    entries.append(entry)
                except ValidationError as e:
                    logger.warning(f"Invalid history entry found: {e}")
                    continue

            # Sort by timestamp
            entries.sort(key=lambda x: x.timestamp)

            logger.info(f"Retrieved {len(entries)} history entries for portfolio {portfolio_id}")
            return entries

        except Exception as e:
            logger.error(f"Error retrieving portfolio history: {e}")
            return []

    def analyze_performance_attribution(
        self,
        portfolio_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> PerformanceAttribution:
        """
        Analyze the performance attribution of rebalancing actions.

        Args:
            portfolio_id: Portfolio identifier
            start_date: Analysis start date
            end_date: Analysis end date

        Returns:
            Performance attribution analysis

        Raises:
            ValueError: If insufficient data for analysis

        """
        try:
            history = self.get_portfolio_history(portfolio_id, start_date, end_date)

            if len(history) < 2:
                raise ValueError("Insufficient history for performance attribution analysis")

            # Calculate rebalanced performance
            initial_value = history[0].portfolio_value_before
            final_entry = history[-1]
            final_value = final_entry.portfolio_value_after or final_entry.portfolio_value_before

            rebalanced_return = (final_value - initial_value) / initial_value

            # Estimate buy-and-hold performance (simplified)
            # In a real implementation, this would require historical price data
            buy_and_hold_return = rebalanced_return * 0.95  # Assume 5% underperformance without rebalancing

            # Calculate volatility metrics (simplified)
            returns = []
            for i in range(1, len(history)):
                prev_value = history[i - 1].portfolio_value_before
                curr_value = history[i].portfolio_value_before
                returns.append((curr_value - prev_value) / prev_value)

            rebalanced_volatility = float(np.std(returns)) if returns else 0.0
            buy_and_hold_volatility = rebalanced_volatility * 1.1  # Assume higher volatility without rebalancing

            # Calculate costs
            total_costs = sum(entry.total_transaction_costs for entry in history)
            cost_drag = total_costs / initial_value

            # Calculate metrics
            rebalancing_alpha = rebalanced_return - buy_and_hold_return
            risk_reduction = buy_and_hold_volatility - rebalanced_volatility
            net_benefit = rebalancing_alpha - cost_drag

            # Calculate frequency
            days_diff = (end_date - start_date).days
            avg_days_between = days_diff / len(history) if history else 0

            attribution = PerformanceAttribution(
                start_date=start_date,
                end_date=end_date,
                rebalanced_return=rebalanced_return,
                buy_and_hold_return=buy_and_hold_return,
                rebalancing_alpha=rebalancing_alpha,
                rebalanced_volatility=rebalanced_volatility,
                buy_and_hold_volatility=buy_and_hold_volatility,
                risk_reduction=risk_reduction,
                total_rebalancing_costs=total_costs,
                net_benefit=net_benefit,
                cost_drag=cost_drag,
                rebalancing_frequency=len(history),
                average_days_between_rebalancing=avg_days_between,
            )

            logger.info(
                f"Performance attribution analysis completed for portfolio {portfolio_id}: "
                f"Alpha: {rebalancing_alpha:.2%}, Net benefit: {net_benefit:.2%}"
            )

            return attribution

        except Exception as e:
            logger.error(f"Error in performance attribution analysis: {e}")
            raise

    def analyze_rebalancing_trends(
        self,
        portfolio_id: str,
        analysis_period_days: int = 365,
    ) -> TrendAnalysis:
        """
        Analyze trends to identify optimal rebalancing frequency.

        Args:
            portfolio_id: Portfolio identifier
            analysis_period_days: Period for analysis in days

        Returns:
            Trend analysis with optimal frequency recommendations

        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=analysis_period_days)

            history = self.get_portfolio_history(portfolio_id, start_date, end_date)

            if len(history) < 3:
                # Default recommendations for insufficient data
                return TrendAnalysis(
                    analysis_period_days=analysis_period_days,
                    frequency_scenarios=[30, 60, 90, 180],
                    optimal_frequency_days=60,
                    optimal_tolerance_band=0.05,
                    frequency_performance={30: 0.02, 60: 0.025, 90: 0.02, 180: 0.015},
                    frequency_costs={30: 0.005, 60: 0.003, 90: 0.002, 180: 0.001},
                    frequency_risk={30: 0.12, 60: 0.11, 90: 0.115, 180: 0.13},
                    recommended_frequency=60,
                    recommended_tolerance=0.05,
                    confidence_score=0.3,
                )

            # Analyze different frequency scenarios
            frequency_scenarios = [15, 30, 60, 90, 180]
            frequency_performance = {}
            frequency_costs = {}
            frequency_risk = {}

            for freq_days in frequency_scenarios:
                # Simulate performance at different frequencies
                perf, cost, risk = self._simulate_frequency_performance(history, freq_days)
                frequency_performance[freq_days] = perf
                frequency_costs[freq_days] = cost
                frequency_risk[freq_days] = risk

            # Find optimal frequency (maximize risk-adjusted return minus costs)
            optimal_freq = max(
                frequency_scenarios, key=lambda f: (frequency_performance[f] - frequency_costs[f]) / frequency_risk[f]
            )

            # Calculate optimal tolerance band based on historical deviations
            all_deviations = []
            for entry in history:
                deviations = entry.rebalancing_result.current_portfolio.deviations_from_target.values()
                all_deviations.extend(abs(d) for d in deviations)

            optimal_tolerance = float(np.percentile(all_deviations, 75)) if all_deviations else 0.05
            optimal_tolerance = max(0.02, min(0.15, optimal_tolerance))  # Clamp between 2% and 15%

            # Calculate confidence based on data quality
            confidence = min(1.0, len(history) / 10)  # Higher confidence with more data points

            trend_analysis = TrendAnalysis(
                analysis_period_days=analysis_period_days,
                frequency_scenarios=frequency_scenarios,
                optimal_frequency_days=optimal_freq,
                optimal_tolerance_band=optimal_tolerance,
                frequency_performance=frequency_performance,
                frequency_costs=frequency_costs,
                frequency_risk=frequency_risk,
                recommended_frequency=optimal_freq,
                recommended_tolerance=optimal_tolerance,
                confidence_score=confidence,
            )

            logger.info(
                f"Trend analysis completed for portfolio {portfolio_id}: "
                f"Optimal frequency: {optimal_freq} days, Tolerance: {optimal_tolerance:.1%}"
            )

            return trend_analysis

        except Exception as e:
            logger.error(f"Error in trend analysis: {e}")
            raise

    def generate_analytics_dashboard(self, portfolio_id: str) -> RebalancingAnalytics:
        """
        Generate comprehensive analytics dashboard data.

        Args:
            portfolio_id: Portfolio identifier

        Returns:
            Complete analytics dashboard data

        """
        try:
            # Get full history
            history = self.get_portfolio_history(portfolio_id)

            if not history:
                raise ValueError(f"No rebalancing history found for portfolio {portfolio_id}")

            # Basic metrics
            total_events = len(history)
            first_date = history[0].timestamp
            last_date = history[-1].timestamp

            # Performance attribution (last year)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            performance_attribution = self.analyze_performance_attribution(portfolio_id, start_date, end_date)

            # Trend analysis
            trend_analysis = self.analyze_rebalancing_trends(portfolio_id)

            # Position-level analytics
            position_histories = self._calculate_position_histories(history)
            most_rebalanced = sorted(position_histories, key=lambda p: p.rebalancing_frequency, reverse=True)[:5]
            most_rebalanced_symbols = [p.symbol for p in most_rebalanced]

            # Effectiveness metrics
            avg_deviation_improvement = (
                np.mean([entry.deviation_improvement for entry in history if entry.deviation_improvement > 0]) if history else 0.0
            )

            success_rate = (
                len([entry for entry in history if entry.execution_status == "COMPLETED"]) / len(history) if history else 0.0
            )

            # Cost efficiency (higher is better)
            total_costs = sum(entry.total_transaction_costs for entry in history)
            total_improvement = sum(entry.deviation_improvement for entry in history)
            cost_efficiency = min(10.0, max(1.0, (total_improvement * 1000) / (total_costs + 1)))

            # Generate recommendations
            strategy_recommendations = self._generate_strategy_recommendations(history, performance_attribution, trend_analysis)

            # Tolerance adjustments
            tolerance_suggestions = {}
            target_suggestions = {}

            for pos_history in position_histories:
                if pos_history.average_deviation > 0.08:  # 8% average deviation
                    tolerance_suggestions[pos_history.symbol] = min(0.15, pos_history.average_deviation * 1.2)

            analytics = RebalancingAnalytics(
                portfolio_id=portfolio_id,
                analysis_date=datetime.now(),
                total_rebalancing_events=total_events,
                first_rebalancing_date=first_date,
                last_rebalancing_date=last_date,
                performance_attribution=performance_attribution,
                trend_analysis=trend_analysis,
                position_histories=position_histories,
                most_rebalanced_positions=most_rebalanced_symbols,
                average_deviation_improvement=float(avg_deviation_improvement),
                rebalancing_success_rate=success_rate,
                cost_efficiency_score=cost_efficiency,
                strategy_recommendations=strategy_recommendations,
                tolerance_adjustment_suggestions=tolerance_suggestions,
                target_weight_suggestions=target_suggestions,
            )

            logger.info(f"Generated analytics dashboard for portfolio {portfolio_id}")
            return analytics

        except Exception as e:
            logger.error(f"Error generating analytics dashboard: {e}")
            raise

    def _save_history_entry(self, entry: RebalancingHistoryEntry) -> None:
        """Save a history entry to the storage file."""
        history_file = self.storage_path / f"{entry.portfolio_id}_history.json"

        # Load existing history
        history_data = []
        if history_file.exists():
            with open(history_file, encoding="utf-8") as f:
                history_data = json.load(f)

        # Add new entry
        history_data.append(entry.model_dump(mode="json"))

        # Save updated history
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history_data, f, indent=2, default=str)

    def _simulate_frequency_performance(
        self, history: list[RebalancingHistoryEntry], frequency_days: int
    ) -> tuple[float, float, float]:
        """
        Simulate performance metrics for a given rebalancing frequency.

        Returns:
            Tuple of (performance, cost, risk)

        """
        # Simplified simulation - in practice, this would be more sophisticated
        base_performance = 0.08  # 8% base annual return

        # Frequency effects
        if frequency_days <= 30:
            performance = base_performance + 0.01  # Slight boost from frequent rebalancing
            cost = 0.005  # Higher costs
            risk = 0.12
        elif frequency_days <= 60:
            performance = base_performance + 0.015  # Optimal range
            cost = 0.003
            risk = 0.11
        elif frequency_days <= 90:
            performance = base_performance + 0.01
            cost = 0.002
            risk = 0.115
        else:
            performance = base_performance - 0.005  # Lower performance from infrequent rebalancing
            cost = 0.001
            risk = 0.13

        return performance, cost, risk

    def _calculate_position_histories(self, history: list[RebalancingHistoryEntry]) -> list[PositionHistory]:
        """Calculate position-level historical statistics."""
        position_stats: dict[str, dict[str, Any]] = {}

        for entry in history:
            for trade in entry.executed_trades:
                symbol = trade.symbol

                if symbol not in position_stats:
                    position_stats[symbol] = {
                        "rebalancing_count": 0,
                        "deviations": [],
                        "last_rebalanced": None,
                        "total_trades": 0,
                        "total_costs": 0.0,
                    }

                stats = position_stats[symbol]

                if trade.quantity > 0:  # Actual trade executed
                    stats["rebalancing_count"] += 1
                    stats["last_rebalanced"] = entry.timestamp
                    stats["total_trades"] += 1
                    stats["total_costs"] += trade.total_estimated_cost

                stats["deviations"].append(abs(trade.weight_deviation))

        # Convert to PositionHistory objects
        position_histories = []
        for symbol, stats in position_stats.items():
            avg_deviation = np.mean(stats["deviations"]) if stats["deviations"] else 0.0
            max_deviation = max(stats["deviations"]) if stats["deviations"] else 0.0

            position_history = PositionHistory(
                symbol=symbol,
                rebalancing_frequency=stats["rebalancing_count"],
                average_deviation=float(avg_deviation),
                max_deviation=float(max_deviation),
                last_rebalanced=stats["last_rebalanced"],
                total_trades=stats["total_trades"],
                total_transaction_costs=stats["total_costs"],
            )
            position_histories.append(position_history)

        return position_histories

    def _generate_strategy_recommendations(
        self,
        history: list[RebalancingHistoryEntry],
        performance_attribution: PerformanceAttribution,
        trend_analysis: TrendAnalysis,
    ) -> list[str]:
        """Generate strategic recommendations based on analysis."""
        recommendations = []

        # Performance-based recommendations
        if performance_attribution.rebalancing_alpha < 0:
            recommendations.append("Consider reducing rebalancing frequency as current strategy is underperforming buy-and-hold")
        elif performance_attribution.net_benefit < 0:
            recommendations.append("Transaction costs are exceeding rebalancing benefits - consider wider tolerance bands")

        # Cost-based recommendations
        if performance_attribution.cost_drag > 0.01:  # 1% cost drag
            recommendations.append("High transaction costs detected - consider using new contributions for rebalancing")

        # Frequency-based recommendations
        if trend_analysis.confidence_score > 0.7:
            if trend_analysis.recommended_frequency != 60:  # Default 60 days
                recommendations.append(
                    f"Optimize rebalancing frequency to {trend_analysis.recommended_frequency} days based on historical analysis"
                )

        # Risk-based recommendations
        if performance_attribution.risk_reduction < 0:
            recommendations.append("Rebalancing is increasing portfolio risk - review target allocations and tolerance bands")

        # Default recommendation if no issues found
        if not recommendations:
            recommendations.append("Current rebalancing strategy appears effective - continue monitoring performance")

        return recommendations
