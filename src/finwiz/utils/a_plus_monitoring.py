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
from typing import Any, Literal

from pydantic import BaseModel, Field

from finwiz.schemas.investment_discovery import APlusAnalysis, MarketRegime
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
            # Create monitored investment tracking object
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

            # Store in monitoring system
            self.monitored_investments[symbol] = monitored_investment
            self.investment_analyses[symbol] = initial_analysis

            # Track performance event
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

        # Mark as inactive instead of deleting
        self.monitored_investments[symbol].is_active = False
        self.monitored_investments[symbol].removal_reason = reason

        logger.info(f"Removed {symbol} from active monitoring: {reason}")

    def get_active_investments(self) -> dict[str, MonitoredInvestment]:
        """Get dict of actively monitored investments."""
        return {symbol: inv for symbol, inv in self.monitored_investments.items() if inv.is_active}

    async def evaluate_investment(self, symbol: str, force_evaluation: bool = False) -> APlusAnalysis | None:
        """
        Evaluate an investment and update its grade.

        Args:
            symbol: Investment symbol to evaluate
            force_evaluation: If True, evaluate regardless of last evaluation time

        Returns:
            APlusAnalysis if evaluation was performed, None if skipped

        """
        if symbol not in self.monitored_investments:
            logger.warning(f"Investment {symbol} not found in monitoring system")
            return None

        monitored_inv = self.monitored_investments[symbol]

        # Check if evaluation is due
        if not force_evaluation:
            time_since_eval = (datetime.now() - monitored_inv.last_evaluated).total_seconds() / 3600
            if time_since_eval < self.reevaluation_interval_hours:
                logger.debug(f"Skipping evaluation for {symbol} - not due yet")
                return None

        try:
            # Use the scoring tool to get new analysis
            result = self.scoring_tool._run(symbol)

            # Convert to APlusAnalysis
            from finwiz.schemas.investment_discovery import InvestmentCandidate

            candidate = InvestmentCandidate(
                symbol=result["symbol"],
                name=result.get("name", result["symbol"]),
                asset_type=monitored_inv.asset_type,
                current_price=result.get("current_price", 100.0),  # Default price if not provided
                preliminary_score=result["composite_score"],
                final_score=result["composite_score"],
                grade=result["grade"],  # Grade is a Literal type, use string directly
                grade_description=f"Grade {result['grade']}",
                recommended_action="Monitor",
                data_source="scoring_tool",
            )

            analysis_summary = result.get("analysis_summary", {})
            component_scores = analysis_summary.get("component_scores", {})

            new_analysis = APlusAnalysis(
                candidate=candidate,
                fundamental_score=component_scores.get("fundamental", 0.8),
                technical_score=component_scores.get("technical", 0.8),
                quality_score=component_scores.get("quality", 0.8),
                risk_score=component_scores.get("risk", 0.8),
                composite_score=result["composite_score"],
                confidence_level=analysis_summary.get("confidence", 0.8),
                is_a_plus_candidate=result.get("is_a_plus_candidate", False),
                rationale=analysis_summary.get("top_strengths", []),
            )

            # Get new grade from the result (already a string)
            new_grade = result["grade"]

            # Check for grade degradation
            if new_grade != monitored_inv.current_grade:
                await self._handle_grade_change(monitored_inv, monitored_inv.current_grade, new_grade, new_analysis)

            # Update stored data
            monitored_inv.current_grade = new_grade
            monitored_inv.current_score = new_analysis.composite_score
            monitored_inv.last_evaluated = datetime.now()
            self.investment_analyses[symbol] = new_analysis

            return new_analysis

        except Exception as e:
            import traceback

            logger.error(f"Error evaluating {symbol}: {e}\n{traceback.format_exc()}")
            return None

    async def evaluate_all_investments(self, force_evaluation: bool = False) -> dict[str, APlusAnalysis]:
        """
        Evaluate all monitored investments.

        Args:
            force_evaluation: If True, evaluate all regardless of last evaluation time

        Returns:
            Dict mapping symbols to their analysis results

        """
        results = {}

        for symbol in list(self.monitored_investments.keys()):
            if self.monitored_investments[symbol].is_active:
                analysis = await self.evaluate_investment(symbol, force_evaluation)
                if analysis is not None:
                    results[symbol] = analysis

        return results

    def _determine_alert_severity(self, previous_grade: str, current_grade: str, previous_score: float, current_score: float) -> "AlertSeverity":
        """
        Determine the severity of a grade degradation alert.

        Args:
            previous_grade: Previous letter grade
            current_grade: Current letter grade
            previous_score: Previous composite score
            current_score: Current composite score

        Returns:
            AlertSeverity level

        """
        from finwiz.utils.monitoring_alerts import AlertSeverity

        # Grade value mapping
        grade_values = {"A+": 4, "A": 3, "B+": 2, "B": 1, "C+": 0.5, "C": 0, "D": -1, "F": -2}

        prev_value = grade_values.get(previous_grade, 0)
        curr_value = grade_values.get(current_grade, 0)
        grade_drop = prev_value - curr_value

        # Score drop
        score_drop = previous_score - current_score

        # Critical: A+ to B+ or worse, or massive score drop
        if (previous_grade == "A+" and grade_drop >= 2) or score_drop > 0.10:
            return AlertSeverity.CRITICAL

        # High: A+ to A, or large score drop with grade change
        if (previous_grade == "A+" and grade_drop >= 1) or (grade_drop > 0 and score_drop > 0.05):
            return AlertSeverity.HIGH

        # Medium: Moderate score drop (same grade or minor grade change)
        if score_drop > 0.05 or (grade_drop > 0 and score_drop > 0.02):
            return AlertSeverity.MEDIUM

        # Low: Minor changes
        if score_drop > 0.02:
            return AlertSeverity.LOW

        # No alert needed
        return AlertSeverity.LOW

    async def check_investment_grade(self, symbol: str) -> Grade | None:
        """Check current grade for a monitored investment."""
        if symbol not in self.monitored_investments:
            logger.warning(f"Investment {symbol} not found in monitoring system")
            return None

        try:
            monitored_inv = self.monitored_investments[symbol]

            # Re-evaluate the investment
            new_analysis = await self.scoring_tool.analyze_investment(symbol, monitored_inv.asset_type)
            grade_info = score_to_grade(new_analysis.composite_score)
            new_grade = grade_info.grade

            # Check for grade degradation
            if new_grade != monitored_inv.current_grade:
                await self._handle_grade_change(monitored_inv, monitored_inv.current_grade, new_grade, new_analysis)

            # Update stored data
            monitored_inv.current_grade = new_grade
            monitored_inv.current_score = new_analysis.composite_score
            monitored_inv.last_evaluated = datetime.now()
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
        monitored_inv: MonitoredInvestment,
        previous_grade: Grade,
        new_grade: Grade,
        analysis: APlusAnalysis,
    ) -> None:
        """Handle grade changes and generate appropriate alerts."""
        from finwiz.utils.monitoring_alerts import GradeDegradationAlert

        # Check if this is a degradation
        grade_values = {"A+": 4, "A": 3, "B+": 2, "B": 1, "C+": 0.5, "C": 0, "D": -1, "F": -2}

        if grade_values.get(new_grade, 0) < grade_values.get(previous_grade, 0):
            # This is a degradation - determine severity
            severity = self._determine_alert_severity(
                previous_grade,
                new_grade,
                monitored_inv.current_score,
                analysis.composite_score,
            )

            # Create alert object
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

            # Store alert in history
            self.alert_history.append(alert)

            # Generate alert through alert manager
            await self.alert_manager.generate_grade_degradation_alert(monitored_inv, previous_grade, analysis)

        # Track performance event
        score_change = analysis.composite_score - monitored_inv.initial_score
        self.metrics_calculator.track_performance_event(monitored_inv, "grade_change", score_change)

        logger.info(f"Grade change for {monitored_inv.symbol}: {previous_grade} -> {new_grade}")

    async def _assess_regime_impact(self, previous_regime: MarketRegime, new_regime: MarketRegime) -> dict[str, Any]:
        """Assess the impact of market regime change on A+ investments."""
        # Simplified impact assessment
        impact_level = "medium"

        # High impact transitions (compare regime_type strings)
        if (previous_regime.regime_type == "bull" and new_regime.regime_type == "bear") or (
            previous_regime.market_stress_level == "low" and new_regime.market_stress_level == "high"
        ):
            impact_level = "high"

        affected_investments = len(self.monitored_investments)

        return {
            "impact_level": impact_level,
            "affected_investments": affected_investments,
            "recommended_action": "Review all A+ positions for regime-specific risks",
            "assessment_timestamp": datetime.now(),
        }

    async def _find_replacement_candidates(self, degraded_symbol: str, asset_type: str) -> list[str]:
        """
        Find replacement candidates for a degraded investment.

        Args:
            degraded_symbol: Symbol of the degraded investment
            asset_type: Type of asset (stock, etf, crypto)

        Returns:
            List of candidate symbols (excluding the degraded symbol)

        """
        # Mock implementation - in production, this would query the A+ discovery system
        candidates = []

        if asset_type == "etf":
            candidates = ["VOO", "VTI", "SPY", "IVV", "SCHX"]
        elif asset_type == "stock":
            candidates = ["MSFT", "GOOGL", "AMZN", "NVDA", "META"]
        elif asset_type == "crypto":
            candidates = ["BTC", "ETH", "SOL", "AVAX", "MATIC"]

        # Remove the degraded symbol from candidates
        return [c for c in candidates if c != degraded_symbol]

    def get_recent_alerts(self, hours: int = 24) -> list[Any]:
        """
        Get alerts from the last N hours.

        Args:
            hours: Number of hours to look back

        Returns:
            List of recent alerts

        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [alert for alert in self.alert_history if alert.alert_timestamp >= cutoff_time]

    def get_degradation_alerts(self, hours_back: int = 24) -> list[Any]:
        """Alias for get_recent_alerts for backward compatibility."""
        return self.get_recent_alerts(hours=hours_back)

    def generate_performance_summary(self) -> dict[str, Any]:
        """
        Generate a performance summary for all monitored investments.

        Returns:
            Dictionary containing performance metrics and statistics

        """
        if not self.monitored_investments:
            return {
                "total_investments": 0,
                "summary": "No investments currently monitored",
            }

        active_investments = [inv for inv in self.monitored_investments.values() if inv.is_active]

        # Count A+ investments
        a_plus_count = sum(1 for inv in active_investments if (inv.current_grade.value if hasattr(inv.current_grade, "value") else str(inv.current_grade)) == "A+")

        # Count degraded investments (grade lower than initial)
        degraded_count = sum(
            1
            for inv in active_investments
            if (inv.current_grade.value if hasattr(inv.current_grade, "value") else str(inv.current_grade))
            != (inv.initial_grade.value if hasattr(inv.initial_grade, "value") else str(inv.initial_grade))
        )

        # Calculate A+ percentage
        a_plus_percentage = (a_plus_count / len(active_investments) * 100) if active_investments else 0.0

        # Determine monitoring health
        if a_plus_percentage >= 80:
            monitoring_health = "excellent"
        elif a_plus_percentage >= 60:
            monitoring_health = "good"
        elif a_plus_percentage >= 40:
            monitoring_health = "needs_attention"
        else:
            monitoring_health = "poor"

        return {
            "total_investments": len(self.monitored_investments),
            "a_plus_count": a_plus_count,
            "degraded_count": degraded_count,
            "a_plus_percentage": a_plus_percentage,
            "monitoring_health": monitoring_health,
        }

    def get_performance_summary(self) -> dict[str, Any]:
        """Alias for generate_performance_summary for backward compatibility."""
        return self.generate_performance_summary()

    def _analyze_degradation_factors(self, symbol: str, previous_score: float, current_score: float) -> list[str]:
        """
        Analyze factors contributing to grade degradation.

        Args:
            symbol: Investment symbol
            previous_score: Previous composite score
            current_score: Current composite score

        Returns:
            List of degradation factors

        """
        factors = []
        score_drop = previous_score - current_score

        if score_drop >= 0.15:
            factors.append("Significant fundamental deterioration")
        elif score_drop >= 0.05:
            factors.append("Moderate performance decline")

        # Add general factors
        factors.append(f"Score decreased by {score_drop:.2%}")

        return factors

    def _generate_recommended_actions(self, symbol: str, grade: str, degradation_factors: list[str]) -> list[str]:
        """
        Generate recommended actions based on grade and degradation factors.

        Args:
            symbol: Investment symbol
            grade: Current grade
            degradation_factors: List of degradation factors

        Returns:
            List of recommended actions

        """
        actions = []

        if grade == "F":
            actions.append(f"Consider immediate exit from {symbol}")
            actions.append("Review portfolio allocation")
        elif grade == "D":
            actions.append(f"Consider position reduction in {symbol}")
            actions.append("Monitor closely for further degradation")
        elif grade in ["B+", "B", "B-"]:
            actions.append(f"Maintain position in {symbol} but monitor closely")
            actions.append("Review quarterly performance")
        else:
            actions.append(f"Continue monitoring {symbol}")

        return actions

    def _detect_significant_regime_change(self, old_regime: MarketRegime, new_regime: MarketRegime) -> bool:
        """
        Detect if a market regime change is significant enough to trigger alerts.

        Args:
            old_regime: Previous market regime
            new_regime: New market regime

        Returns:
            True if change is significant

        """
        # Check regime type change
        if old_regime.regime_type != new_regime.regime_type:
            return True

        # Check stress level change
        if old_regime.market_stress_level != new_regime.market_stress_level:
            return True

        # Check VIX level change (>=10 point swing)
        if abs(old_regime.vix_level - new_regime.vix_level) >= 10.0:
            return True

        return False

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
