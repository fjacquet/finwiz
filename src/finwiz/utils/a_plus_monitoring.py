"""
A+ Investment Monitoring System for continuous grade maintenance and performance tracking.

This module provides comprehensive monitoring capabilities for A+ investments including:
- Continuous grade monitoring and degradation alerts
- Automatic re-evaluation triggers
- Performance tracking for A+ recommendations
- Trend analysis and criteria adjustment suggestions

Requirements addressed: 7.1, 7.2, 7.3 from investment discovery spec.
"""

import asyncio
from collections.abc import Callable
from datetime import datetime
from typing import Any, Literal

from finwiz.schemas.investment_discovery import APlusAnalysis, InvestmentCandidate, MarketRegime
from finwiz.schemas.portfolio_review import Grade
from finwiz.tools.a_plus_scoring_tool import APlusScoringTool
from finwiz.tools.logger import get_logger
from finwiz.tools.notification_service import NotificationService
from finwiz.utils.grading_system import score_to_grade
from finwiz.utils.monitoring import get_metrics_collector
from finwiz.utils.monitoring_alerts import (
    AlertManager,
)
from finwiz.utils.monitoring_metrics import MetricsCalculator, PerformanceMetrics

logger = get_logger(__name__)

# Global monitoring system instance
_monitoring_system: "APlusMonitoringSystem | None" = None


class APlusMonitoringSystem:
    """
    Comprehensive A+ investment monitoring system.

    Provides continuous monitoring of A+ investments with automated alerts,
    performance tracking, and re-evaluation triggers based on market conditions
    and fundamental changes.
    """

    def __init__(
        self,
        scoring_tool: APlusScoringTool | None = None,
        notification_service: NotificationService | None = None,
        alert_threshold_hours: int = 24,
        reevaluation_interval_hours: int = 168,  # Weekly
    ) -> None:
        """Initialize the A+ monitoring system."""
        self.scoring_tool = scoring_tool or APlusScoringTool()
        self.notification_service = notification_service or NotificationService()
        self.alert_threshold_hours = alert_threshold_hours
        self.reevaluation_interval_hours = reevaluation_interval_hours

        # Initialize component managers
        self.alert_manager = AlertManager(self.notification_service)
        self.metrics_calculator = MetricsCalculator()

        # Monitoring data structures
        self.monitored_investments: dict[str, InvestmentCandidate] = {}
        self.investment_analyses: dict[str, APlusAnalysis] = {}

        # Market regime tracking
        self.current_market_regime: MarketRegime | None = None
        self.regime_change_callbacks: list[Callable[[MarketRegime, MarketRegime], None]] = []

        # Metrics collector
        self.metrics_collector = get_metrics_collector()

        # Background monitoring task
        self._monitoring_task: asyncio.Task | None = None
        self._is_monitoring = False

        logger.info("A+ Monitoring System initialized")

    async def start_monitoring(self) -> None:
        """Start the background monitoring process."""
        if self._is_monitoring:
            logger.warning("Monitoring already started")
            return

        self._is_monitoring = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("A+ monitoring started")

    async def stop_monitoring(self) -> None:
        """Stop the background monitoring process."""
        self._is_monitoring = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("A+ monitoring stopped")

    def add_investment_to_monitor(
        self,
        symbol: str,
        asset_type: Literal["etf", "stock", "crypto"],
        initial_analysis: APlusAnalysis,
    ) -> None:
        """Add an A+ investment to the monitoring system."""
        try:
            # Create investment candidate
            candidate = InvestmentCandidate(
                symbol=symbol,
                asset_type=asset_type,
                current_grade=score_to_grade(initial_analysis.composite_score),
                analysis_date=datetime.now(),
                last_updated=datetime.now(),
            )

            # Store in monitoring system
            self.monitored_investments[symbol] = candidate
            self.investment_analyses[symbol] = initial_analysis

            # Track performance event
            self.metrics_calculator.track_performance_event(candidate, "initial_recommendation", initial_analysis.composite_score)

            logger.info(f"Added {symbol} to A+ monitoring system")

        except Exception as e:
            logger.error(f"Error adding {symbol} to monitoring: {e}")
            raise

    async def check_investment_grade(self, symbol: str) -> Grade | None:
        """Check current grade for a monitored investment."""
        if symbol not in self.monitored_investments:
            logger.warning(f"Investment {symbol} not found in monitoring system")
            return None

        try:
            candidate = self.monitored_investments[symbol]

            # Re-evaluate the investment
            new_analysis = await self.scoring_tool.analyze_investment(symbol, candidate.asset_type)
            new_grade = score_to_grade(new_analysis.composite_score)

            # Check for grade degradation
            if new_grade != candidate.current_grade:
                await self._handle_grade_change(candidate, candidate.current_grade, new_grade, new_analysis)

            # Update stored data
            candidate.current_grade = new_grade
            candidate.last_updated = datetime.now()
            self.investment_analyses[symbol] = new_analysis

            return new_grade

        except Exception as e:
            logger.error(f"Error checking grade for {symbol}: {e}")
            return None

    async def get_performance_metrics(self) -> PerformanceMetrics:
        """Get comprehensive performance metrics for all monitored investments."""
        candidates = list(self.monitored_investments.values())
        analyses = list(self.investment_analyses.values())

        return self.metrics_calculator.calculate_performance_metrics(candidates, analyses)

    async def get_alert_summary(self) -> dict[str, Any]:
        """Get summary of recent alerts."""
        return self.alert_manager.get_alert_summary()

    def register_regime_change_callback(self, callback: Callable[[MarketRegime, MarketRegime], None]) -> None:
        """Register a callback for market regime changes."""
        self.regime_change_callbacks.append(callback)
        logger.info("Registered market regime change callback")

    async def update_market_regime(self, new_regime: MarketRegime) -> None:
        """Update the current market regime and trigger callbacks."""
        if self.current_market_regime != new_regime:
            previous_regime = self.current_market_regime
            self.current_market_regime = new_regime

            # Generate market regime alert
            if previous_regime is not None:
                impact_assessment = await self._assess_regime_impact(previous_regime, new_regime)
                await self.alert_manager.generate_market_regime_alert(previous_regime, new_regime, impact_assessment)

            # Trigger callbacks
            for callback in self.regime_change_callbacks:
                try:
                    callback(previous_regime, new_regime)
                except Exception as e:
                    logger.error(f"Error in regime change callback: {e}")

            logger.info(f"Market regime updated: {previous_regime} -> {new_regime}")

    async def _monitoring_loop(self) -> None:
        """Run main monitoring loop in the background."""
        logger.info("Starting A+ monitoring loop")

        while self._is_monitoring:
            try:
                # Check all monitored investments
                for symbol in list(self.monitored_investments.keys()):
                    await self.check_investment_grade(symbol)

                    # Small delay between checks to avoid overwhelming APIs
                    await asyncio.sleep(1)

                # Calculate and log performance metrics
                metrics = await self.get_performance_metrics()
                total_recs = metrics.total_recommendations
                success_rate = metrics.success_rate
                logger.debug(f"Performance metrics: {total_recs} recommendations, {success_rate:.1f}% success rate")

                # Wait before next monitoring cycle
                await asyncio.sleep(self.reevaluation_interval_hours * 3600)  # Convert hours to seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying

        logger.info("A+ monitoring loop stopped")

    async def _handle_grade_change(
        self,
        candidate: InvestmentCandidate,
        previous_grade: Grade,
        new_grade: Grade,
        analysis: APlusAnalysis,
    ) -> None:
        """Handle grade changes and generate appropriate alerts."""
        # Check if this is a degradation
        grade_values = {Grade.A_PLUS: 4, Grade.A: 3, Grade.B_PLUS: 2, Grade.B: 1, Grade.C: 0}

        if grade_values.get(new_grade, 0) < grade_values.get(previous_grade, 0):
            # This is a degradation - generate alert
            await self.alert_manager.generate_grade_degradation_alert(candidate, previous_grade, analysis)

        # Track performance event
        score_change = analysis.composite_score - 0.8  # Simplified previous score estimation
        self.metrics_calculator.track_performance_event(candidate, "grade_change", score_change)

        logger.info(f"Grade change for {candidate.symbol}: {previous_grade.value} -> {new_grade.value}")

    async def _assess_regime_impact(self, previous_regime: MarketRegime, new_regime: MarketRegime) -> dict[str, Any]:
        """Assess the impact of market regime change on A+ investments."""
        # Simplified impact assessment
        impact_level = "medium"

        # High impact transitions
        if (previous_regime == MarketRegime.BULL_MARKET and new_regime == MarketRegime.BEAR_MARKET) or (
            previous_regime == MarketRegime.LOW_VOLATILITY and new_regime == MarketRegime.HIGH_VOLATILITY
        ):
            impact_level = "high"

        affected_investments = len(self.monitored_investments)

        return {
            "impact_level": impact_level,
            "affected_investments": affected_investments,
            "recommended_action": "Review all A+ positions for regime-specific risks",
            "assessment_timestamp": datetime.now(),
        }


def get_monitoring_system() -> APlusMonitoringSystem:
    """Get the global A+ monitoring system instance."""
    global _monitoring_system
    if _monitoring_system is None:
        _monitoring_system = APlusMonitoringSystem()
    return _monitoring_system


async def start_a_plus_monitoring() -> None:
    """Start the global A+ monitoring system."""
    monitoring_system = get_monitoring_system()
    await monitoring_system.start_monitoring()


async def stop_a_plus_monitoring() -> None:
    """Stop the global A+ monitoring system."""
    monitoring_system = get_monitoring_system()
    await monitoring_system.stop_monitoring()
