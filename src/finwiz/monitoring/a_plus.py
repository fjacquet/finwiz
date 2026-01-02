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
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Literal

from pydantic import BaseModel, Field

from finwiz.schemas.investment_discovery import APlusAnalysis, MarketRegime

if TYPE_CHECKING:
    from finwiz.utils.monitoring_alerts import AlertSeverity
from finwiz.schemas.portfolio_review import Grade
from finwiz.tools.a_plus_scoring_tool import APlusScoringTool
from finwiz.tools.logger import get_logger
from finwiz.tools.notification_service import NotificationService
from finwiz.utils.grading_system import score_to_grade
from finwiz.utils.monitoring import get_metrics_collector
from finwiz.utils.monitoring_alerts import AlertManager
from finwiz.utils.monitoring_metrics import MetricsCalculator, PerformanceMetrics

logger = get_logger(__name__)

# Global monitoring system instance
_monitoring_system: "APlusMonitoringSystem | None" = None


class MonitoredInvestment(BaseModel):
    """Tracking object for monitored A+ investments."""

    symbol: str = Field(..., description="Investment symbol")
    asset_type: Literal["etf", "stock", "crypto"] = Field(..., description="Type of asset")
    initial_grade: Grade = Field(..., description="Grade at time of addition")
    current_grade: Grade = Field(..., description="Current grade")
    initial_score: float = Field(..., ge=0.0, le=1.0, description="Score at time of addition")
    current_score: float = Field(..., ge=0.0, le=1.0, description="Current score")
    is_active: bool = Field(default=True, description="Whether investment is actively monitored")
    added_date: datetime = Field(default_factory=datetime.now, description="When added to monitoring")
    last_evaluated: datetime = Field(default_factory=datetime.now, description="Last evaluation timestamp")
    removal_reason: str | None = Field(None, description="Reason for removal if inactive")


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
        self.monitored_investments: dict[str, MonitoredInvestment] = {}
        self.investment_analyses: dict[str, APlusAnalysis] = {}
        self.alert_history: list[Any] = []

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
            grade_info = score_to_grade(initial_analysis.composite_score)
            monitored_investment = MonitoredInvestment(
                symbol=symbol,
                asset_type=asset_type,
                initial_grade=grade_info.grade,
                current_grade=grade_info.grade,
                initial_score=initial_analysis.composite_score,
                current_score=initial_analysis.composite_score,
                is_active=True,
                added_date=datetime.now(),
                last_evaluated=datetime.now(),
            )

            self.monitored_investments[symbol] = monitored_investment
            self.investment_analyses[symbol] = initial_analysis
            self.metrics_calculator.track_performance_event(monitored_investment, "initial_recommendation", initial_analysis.composite_score)

            logger.info(f"Added {symbol} to A+ monitoring system")

        except Exception as e:
            logger.error(f"Error adding {symbol} to monitoring: {e}")
            raise

    def remove_investment_from_monitor(self, symbol: str, reason: str) -> None:
        """Remove an investment from active monitoring."""
        if symbol not in self.monitored_investments:
            logger.warning(f"Investment {symbol} not found in monitoring system")
            return

        self.monitored_investments[symbol].is_active = False
        self.monitored_investments[symbol].removal_reason = reason
        logger.info(f"Removed {symbol} from active monitoring: {reason}")

    def get_active_investments(self) -> dict[str, MonitoredInvestment]:
        """Get dict of actively monitored investments."""
        return {symbol: inv for symbol, inv in self.monitored_investments.items() if inv.is_active}

    async def evaluate_investment(self, symbol: str, force_evaluation: bool = False) -> APlusAnalysis | None:
        """Evaluate an investment and update its grade (delegates to module)."""
        if symbol not in self.monitored_investments:
            logger.warning(f"Investment {symbol} not found in monitoring system")
            return None

        from finwiz.utils.a_plus_monitoring_evaluation import evaluate_single_investment

        monitored_inv = self.monitored_investments[symbol]
        new_analysis = await evaluate_single_investment(symbol, monitored_inv, self.scoring_tool, self.reevaluation_interval_hours, force_evaluation)

        if new_analysis:
            new_grade = new_analysis.candidate.grade
            if new_grade != monitored_inv.current_grade:
                await self._handle_grade_change(monitored_inv, monitored_inv.current_grade, new_grade, new_analysis)

            monitored_inv.current_grade = new_grade
            monitored_inv.current_score = new_analysis.composite_score
            monitored_inv.last_evaluated = datetime.now()
            self.investment_analyses[symbol] = new_analysis

        return new_analysis

    async def evaluate_all_investments(self, force_evaluation: bool = False) -> dict[str, APlusAnalysis]:
        """Evaluate all monitored investments."""
        results = {}
        for symbol in list(self.monitored_investments.keys()):
            if self.monitored_investments[symbol].is_active:
                analysis = await self.evaluate_investment(symbol, force_evaluation)
                if analysis is not None:
                    results[symbol] = analysis
        return results

    def _determine_alert_severity(self, previous_grade: str, current_grade: str, previous_score: float, current_score: float) -> "AlertSeverity":
        """Determine the severity of a grade degradation alert (delegates to module)."""
        from finwiz.utils.a_plus_monitoring_evaluation import determine_alert_severity

        result: AlertSeverity = determine_alert_severity(previous_grade, current_grade, previous_score, current_score)
        return result

    async def check_investment_grade(self, symbol: str) -> Grade | None:
        """Check current grade for a monitored investment."""
        if symbol not in self.monitored_investments:
            logger.warning(f"Investment {symbol} not found in monitoring system")
            return None

        from finwiz.utils.a_plus_monitoring_evaluation import check_grade_for_investment

        monitored_inv = self.monitored_investments[symbol]
        new_grade, new_analysis = await check_grade_for_investment(symbol, monitored_inv, self.scoring_tool)

        if new_grade is not None and new_analysis is not None:
            if new_grade != monitored_inv.current_grade:
                await self._handle_grade_change(monitored_inv, monitored_inv.current_grade, new_grade, new_analysis)

            monitored_inv.current_grade = new_grade
            monitored_inv.current_score = new_analysis.composite_score
            monitored_inv.last_evaluated = datetime.now()
            self.investment_analyses[symbol] = new_analysis

        return new_grade

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

            if previous_regime is not None:
                impact_assessment = await self._assess_regime_impact(previous_regime, new_regime)
                await self.alert_manager.generate_market_regime_alert(previous_regime, new_regime, impact_assessment)

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
                for symbol in list(self.monitored_investments.keys()):
                    await self.check_investment_grade(symbol)
                    await asyncio.sleep(1)

                metrics = await self.get_performance_metrics()
                logger.debug(f"Performance metrics: {metrics.total_recommendations} recommendations, {metrics.success_rate:.1f}% success rate")

                await asyncio.sleep(self.reevaluation_interval_hours * 3600)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)

        logger.info("A+ monitoring loop stopped")

    async def _handle_grade_change(
        self,
        monitored_inv: MonitoredInvestment,
        previous_grade: Grade,
        new_grade: Grade,
        analysis: APlusAnalysis,
    ) -> None:
        """Handle grade changes and generate appropriate alerts."""
        from finwiz.utils.monitoring_alerts import GradeDegradationAlert

        grade_values = {"A+": 4, "A": 3, "B+": 2, "B": 1, "C+": 0.5, "C": 0, "D": -1, "F": -2}

        if grade_values.get(new_grade, 0) < grade_values.get(previous_grade, 0):
            severity = self._determine_alert_severity(previous_grade, new_grade, monitored_inv.current_score, analysis.composite_score)

            alert = GradeDegradationAlert(
                symbol=monitored_inv.symbol,
                asset_type=monitored_inv.asset_type,
                previous_grade=previous_grade,
                current_grade=new_grade,
                previous_score=monitored_inv.current_score,
                current_score=analysis.composite_score,
                score_change=analysis.composite_score - monitored_inv.current_score,
                severity=severity,
                alert_timestamp=datetime.now(),
                degradation_reason="Grade degradation detected",
                recommendation="Review position",
            )

            self.alert_history.append(alert)
            await self.alert_manager.generate_grade_degradation_alert(monitored_inv, previous_grade, analysis)

        score_change = analysis.composite_score - monitored_inv.initial_score
        self.metrics_calculator.track_performance_event(monitored_inv, "grade_change", score_change)
        logger.info(f"Grade change for {monitored_inv.symbol}: {previous_grade} -> {new_grade}")

    async def _assess_regime_impact(self, previous_regime: MarketRegime, new_regime: MarketRegime) -> dict[str, Any]:
        """Assess the impact of market regime change (delegates to module)."""
        from finwiz.utils.a_plus_monitoring_regime import assess_regime_impact

        return await assess_regime_impact(previous_regime, new_regime, len(self.monitored_investments))

    async def _find_replacement_candidates(self, degraded_symbol: str, asset_type: str) -> list[str]:
        """Find replacement candidates for a degraded investment (delegates to module)."""
        from finwiz.utils.a_plus_monitoring_recommendations import find_replacement_candidates

        return await find_replacement_candidates(degraded_symbol, asset_type)

    def get_recent_alerts(self, hours: int = 24) -> list[Any]:
        """Get alerts from the last N hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [alert for alert in self.alert_history if alert.alert_timestamp >= cutoff_time]

    def get_degradation_alerts(self, hours_back: int = 24) -> list[Any]:
        """Alias for get_recent_alerts for backward compatibility."""
        return self.get_recent_alerts(hours=hours_back)

    def generate_performance_summary(self) -> dict[str, Any]:
        """Generate a performance summary (delegates to module)."""
        from finwiz.utils.a_plus_monitoring_recommendations import generate_performance_summary

        return generate_performance_summary(self.monitored_investments)

    def get_performance_summary(self) -> dict[str, Any]:
        """Alias for generate_performance_summary for backward compatibility."""
        return self.generate_performance_summary()

    def _analyze_degradation_factors(self, symbol: str, previous_score: float, current_score: float) -> list[str]:
        """Analyze factors contributing to grade degradation (delegates to module)."""
        from finwiz.utils.a_plus_monitoring_recommendations import analyze_degradation_factors

        return analyze_degradation_factors(symbol, previous_score, current_score)

    def _generate_recommended_actions(self, symbol: str, grade: str, degradation_factors: list[str]) -> list[str]:
        """Generate recommended actions (delegates to module)."""
        from finwiz.utils.a_plus_monitoring_recommendations import generate_recommended_actions

        return generate_recommended_actions(symbol, grade, degradation_factors)

    def _detect_significant_regime_change(self, old_regime: MarketRegime, new_regime: MarketRegime) -> bool:
        """Detect if a market regime change is significant (delegates to module)."""
        from finwiz.utils.a_plus_monitoring_regime import detect_significant_regime_change

        return detect_significant_regime_change(old_regime, new_regime)

    def _is_significant_regime_change(self, old_regime: MarketRegime, new_regime: MarketRegime) -> bool:
        """Alias for _detect_significant_regime_change for backward compatibility."""
        return self._detect_significant_regime_change(old_regime, new_regime)


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
