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
from collections import defaultdict, deque
from collections.abc import Callable
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field

from finwiz.schemas.investment_discovery import APlusAnalysis, InvestmentCandidate, MarketRegime
from finwiz.schemas.portfolio_review import Grade
from finwiz.tools.a_plus_scoring_tool import APlusScoringTool
from finwiz.tools.logger import get_logger
from finwiz.tools.notification_service import NotificationService
from finwiz.utils.grading_system import score_to_grade
from finwiz.utils.monitoring import get_metrics_collector

logger = get_logger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels for A+ monitoring."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MonitoringEvent(Enum):
    """Types of monitoring events."""

    GRADE_DEGRADATION = "grade_degradation"
    PERFORMANCE_DECLINE = "performance_decline"
    CRITERIA_CHANGE = "criteria_change"
    MARKET_REGIME_SHIFT = "market_regime_shift"
    RECOMMENDATION_UPDATE = "recommendation_update"


class GradeDegradationAlert(BaseModel):
    """Alert for A+ grade degradation."""

    symbol: str = Field(..., description="Investment symbol")
    asset_type: Literal["etf", "stock", "crypto"] = Field(..., description="Asset type")
    previous_grade: Grade = Field(..., description="Previous grade")
    current_grade: Grade = Field(..., description="Current grade")
    previous_score: float = Field(..., ge=0.0, le=1.0, description="Previous composite score")
    current_score: float = Field(..., ge=0.0, le=1.0, description="Current composite score")
    score_change: float = Field(..., description="Change in score (negative for degradation)")
    degradation_factors: list[str] = Field(default_factory=list, description="Factors causing degradation")
    severity: AlertSeverity = Field(..., description="Alert severity level")
    alert_timestamp: datetime = Field(default_factory=datetime.now, description="When alert was generated")
    recommended_actions: list[str] = Field(default_factory=list, description="Recommended actions")
    replacement_candidates: list[str] = Field(default_factory=list, description="Alternative investment suggestions")


class PerformanceMetrics(BaseModel):
    """Performance tracking metrics for A+ investments."""

    symbol: str = Field(..., description="Investment symbol")
    asset_type: Literal["etf", "stock", "crypto"] = Field(..., description="Asset type")
    recommendation_date: datetime = Field(..., description="When investment was recommended")
    initial_grade: Grade = Field(..., description="Grade when first recommended")
    current_grade: Grade = Field(..., description="Current grade")
    initial_score: float = Field(..., ge=0.0, le=1.0, description="Initial A+ score")
    current_score: float = Field(..., ge=0.0, le=1.0, description="Current A+ score")

    # Performance tracking
    total_return: float = Field(..., description="Total return since recommendation")
    annualized_return: float = Field(..., description="Annualized return")
    benchmark_return: float = Field(..., description="Benchmark return for comparison")
    alpha: float = Field(..., description="Alpha vs benchmark")
    sharpe_ratio: float = Field(..., description="Risk-adjusted return metric")
    max_drawdown: float = Field(..., le=0.0, description="Maximum drawdown experienced")

    # Grade maintenance
    days_as_a_plus: int = Field(default=0, description="Days maintained A+ grade")
    grade_changes: list[dict[str, Any]] = Field(default_factory=list, description="History of grade changes")
    last_evaluation: datetime = Field(default_factory=datetime.now, description="Last evaluation timestamp")

    # Status flags
    is_active: bool = Field(default=True, description="Whether still being monitored")
    needs_reevaluation: bool = Field(default=False, description="Whether needs immediate re-evaluation")


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

        # Monitoring data structures
        self.monitored_investments: dict[str, PerformanceMetrics] = {}
        self.alert_history: deque[GradeDegradationAlert] = deque(maxlen=1000)
        self.performance_history: dict[str, deque[dict[str, Any]]] = defaultdict(lambda: deque(maxlen=100))

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
            performance_metrics = PerformanceMetrics(
                symbol=symbol,
                asset_type=asset_type,
                recommendation_date=datetime.now(),
                initial_grade=initial_analysis.candidate.grade,
                current_grade=initial_analysis.candidate.grade,
                initial_score=initial_analysis.composite_score,
                current_score=initial_analysis.composite_score,
                total_return=0.0,
                annualized_return=0.0,
                benchmark_return=0.0,
                alpha=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
            )

            self.monitored_investments[symbol] = performance_metrics

            # Record metrics
            self.metrics_collector.record_counter("a_plus_monitoring.investments_added")
            self.metrics_collector.record_gauge("a_plus_monitoring.total_monitored", len(self.monitored_investments))

            logger.info(f"Added {symbol} to A+ monitoring system")

        except Exception as e:
            logger.error(f"Failed to add {symbol} to monitoring: {str(e)}")
            raise

    def remove_investment_from_monitor(self, symbol: str, reason: str = "Manual removal") -> None:
        """Remove an investment from monitoring."""
        if symbol in self.monitored_investments:
            # Mark as inactive instead of removing to preserve history
            self.monitored_investments[symbol].is_active = False

            # Record metrics
            self.metrics_collector.record_counter("a_plus_monitoring.investments_removed")
            self.metrics_collector.record_gauge("a_plus_monitoring.total_monitored", len(self.get_active_investments()))

            logger.info(f"Removed {symbol} from monitoring: {reason}")
        else:
            logger.warning(f"Attempted to remove {symbol} but not found in monitoring")

    def get_active_investments(self) -> dict[str, PerformanceMetrics]:
        """Get currently active monitored investments."""
        return {symbol: metrics for symbol, metrics in self.monitored_investments.items() if metrics.is_active}

    async def evaluate_investment(self, symbol: str, force_evaluation: bool = False) -> APlusAnalysis | None:
        """Evaluate a single investment and check for grade changes."""
        try:
            if symbol not in self.monitored_investments:
                logger.warning(f"Investment {symbol} not found in monitoring system")
                return None

            metrics = self.monitored_investments[symbol]

            # Check if evaluation is needed
            time_since_last = datetime.now() - metrics.last_evaluation
            if not force_evaluation and time_since_last.total_seconds() < self.reevaluation_interval_hours * 3600:
                return None

            # Perform A+ scoring
            scoring_result = self.scoring_tool._run(
                symbol=symbol,
                asset_type=metrics.asset_type,
                fundamental_data={},  # Would fetch fresh data in production
                market_context={},  # Would fetch current market context
            )

            if "error" in scoring_result:
                logger.error(f"Scoring failed for {symbol}: {scoring_result['error']}")
                return None

            # Extract new analysis
            new_score = scoring_result["composite_score"]
            new_grade = scoring_result["grade"]

            # Check for grade degradation
            previous_grade = metrics.current_grade
            previous_score = metrics.current_score

            if self._is_grade_degradation(previous_grade, new_grade, previous_score, new_score):
                await self._handle_grade_degradation(symbol, metrics, previous_grade, new_grade, previous_score, new_score)

            # Update metrics
            metrics.current_grade = new_grade
            metrics.current_score = new_score
            metrics.last_evaluation = datetime.now()

            # Record grade change if significant
            if previous_grade != new_grade or abs(previous_score - new_score) > 0.05:
                grade_change = {
                    "timestamp": datetime.now().isoformat(),
                    "previous_grade": previous_grade,
                    "new_grade": new_grade,
                    "previous_score": previous_score,
                    "new_score": new_score,
                    "score_change": new_score - previous_score,
                }
                metrics.grade_changes.append(grade_change)

            # Update performance history
            self.performance_history[symbol].append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "grade": new_grade,
                    "score": new_score,
                    "evaluation_type": "scheduled" if not force_evaluation else "forced",
                }
            )

            # Record metrics
            self.metrics_collector.record_counter("a_plus_monitoring.evaluations_completed")
            if new_score >= 0.95:
                self.metrics_collector.record_counter("a_plus_monitoring.a_plus_maintained")
            else:
                self.metrics_collector.record_counter("a_plus_monitoring.a_plus_lost")

            logger.info(f"Evaluated {symbol}: {previous_grade} -> {new_grade} (score: {new_score:.3f})")

            # Create analysis object (simplified for monitoring)
            candidate = InvestmentCandidate(
                symbol=symbol,
                name=symbol,  # Would fetch full name in production
                asset_type=metrics.asset_type,
                current_price=100.0,  # Would fetch current price
                preliminary_score=new_score,
                final_score=new_score,
                grade=new_grade,
                grade_description=score_to_grade(new_score).description,
                recommended_action=score_to_grade(new_score).action,
                data_source="monitoring_system",
            )

            analysis = APlusAnalysis(
                candidate=candidate,
                fundamental_score=scoring_result.get("analysis_summary", {}).get("component_scores", {}).get("fundamental", 0.5),
                technical_score=scoring_result.get("analysis_summary", {}).get("component_scores", {}).get("technical", 0.5),
                quality_score=scoring_result.get("analysis_summary", {}).get("component_scores", {}).get("quality", 0.5),
                risk_score=scoring_result.get("analysis_summary", {}).get("component_scores", {}).get("risk", 0.5),
                composite_score=new_score,
                confidence_level=scoring_result.get("analysis_summary", {}).get("confidence", 0.7),
                is_a_plus_candidate=new_score >= 0.95,
                rationale=scoring_result.get("analysis_summary", {}).get("top_strengths", []),
            )

            return analysis

        except Exception as e:
            logger.error(f"Failed to evaluate {symbol}: {str(e)}")
            self.metrics_collector.record_counter("a_plus_monitoring.evaluation_errors")
            return None

    async def evaluate_all_investments(self, force_evaluation: bool = False) -> dict[str, APlusAnalysis]:
        """Evaluate all monitored investments."""
        results = {}
        active_investments = self.get_active_investments()

        logger.info(f"Evaluating {len(active_investments)} monitored investments")

        # Evaluate investments in parallel (with concurrency limit)
        semaphore = asyncio.Semaphore(5)  # Limit concurrent evaluations

        async def evaluate_with_semaphore(symbol: str) -> tuple[str, APlusAnalysis | None]:
            async with semaphore:
                analysis = await self.evaluate_investment(symbol, force_evaluation)
                return symbol, analysis

        tasks = [evaluate_with_semaphore(symbol) for symbol in active_investments.keys()]
        evaluation_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for result in evaluation_results:
            if isinstance(result, Exception):
                logger.error(f"Evaluation task failed: {str(result)}")
                continue

            symbol, analysis = result
            if analysis:
                results[symbol] = analysis

        logger.info(f"Completed evaluation of {len(results)} investments")
        return results

    def get_degradation_alerts(self, hours_back: int = 24) -> list[GradeDegradationAlert]:
        """Get recent degradation alerts."""
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        return [alert for alert in self.alert_history if alert.alert_timestamp >= cutoff_time]

    def get_performance_summary(self) -> dict[str, Any]:
        """Get performance summary for all monitored investments."""
        active_investments = self.get_active_investments()

        if not active_investments:
            return {"total_investments": 0, "summary": "No investments currently monitored"}

        # Calculate summary statistics
        total_investments = len(active_investments)
        a_plus_count = sum(1 for m in active_investments.values() if m.current_score >= 0.95)
        a_grade_count = sum(1 for m in active_investments.values() if 0.85 <= m.current_score < 0.95)
        degraded_count = sum(1 for m in active_investments.values() if m.current_score < 0.85)

        # Average metrics
        avg_score = sum(m.current_score for m in active_investments.values()) / total_investments
        avg_return = sum(m.total_return for m in active_investments.values()) / total_investments
        avg_alpha = sum(m.alpha for m in active_investments.values()) / total_investments

        # Recent alerts
        recent_alerts = len(self.get_degradation_alerts(24))

        return {
            "total_investments": total_investments,
            "a_plus_count": a_plus_count,
            "a_grade_count": a_grade_count,
            "degraded_count": degraded_count,
            "a_plus_percentage": (a_plus_count / total_investments) * 100,
            "average_score": avg_score,
            "average_return": avg_return,
            "average_alpha": avg_alpha,
            "recent_alerts_24h": recent_alerts,
            "monitoring_health": "healthy" if degraded_count == 0 else "needs_attention",
            "last_updated": datetime.now().isoformat(),
        }

    def register_regime_change_callback(self, callback: Callable[[MarketRegime, MarketRegime], None]) -> None:
        """Register a callback for market regime changes."""
        self.regime_change_callbacks.append(callback)

    async def update_market_regime(self, new_regime: MarketRegime) -> None:
        """Update market regime and trigger callbacks if changed."""
        previous_regime = self.current_market_regime

        if previous_regime and self._is_significant_regime_change(previous_regime, new_regime):
            logger.info(f"Market regime change detected: {previous_regime.regime_type} -> {new_regime.regime_type}")

            # Trigger callbacks
            for callback in self.regime_change_callbacks:
                try:
                    callback(previous_regime, new_regime)
                except Exception as e:
                    logger.error(f"Regime change callback failed: {str(e)}")

            # Mark all investments for re-evaluation
            for metrics in self.monitored_investments.values():
                if metrics.is_active:
                    metrics.needs_reevaluation = True

            # Record metrics
            self.metrics_collector.record_counter("a_plus_monitoring.regime_changes")

        self.current_market_regime = new_regime

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop that runs in the background."""
        logger.info("Starting A+ monitoring loop")

        while self._is_monitoring:
            try:
                # Evaluate investments that need re-evaluation
                await self._check_reevaluation_needs()

                # Perform scheduled evaluations
                await self._perform_scheduled_evaluations()

                # Clean up old data
                self._cleanup_old_data()

                # Update monitoring metrics
                self._update_monitoring_metrics()

                # Sleep until next check (every hour)
                await asyncio.sleep(3600)

            except asyncio.CancelledError:
                logger.info("Monitoring loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                self.metrics_collector.record_counter("a_plus_monitoring.loop_errors")
                await asyncio.sleep(300)  # Wait 5 minutes before retrying

    async def _check_reevaluation_needs(self) -> None:
        """Check which investments need immediate re-evaluation."""
        investments_to_evaluate = [
            symbol for symbol, metrics in self.monitored_investments.items() if metrics.is_active and metrics.needs_reevaluation
        ]

        if investments_to_evaluate:
            logger.info(f"Re-evaluating {len(investments_to_evaluate)} investments due to triggers")

            for symbol in investments_to_evaluate:
                await self.evaluate_investment(symbol, force_evaluation=True)
                self.monitored_investments[symbol].needs_reevaluation = False

    async def _perform_scheduled_evaluations(self) -> None:
        """Perform scheduled evaluations based on time intervals."""
        current_time = datetime.now()
        investments_to_evaluate = []

        for symbol, metrics in self.monitored_investments.items():
            if not metrics.is_active:
                continue

            time_since_last = current_time - metrics.last_evaluation
            if time_since_last.total_seconds() >= self.reevaluation_interval_hours * 3600:
                investments_to_evaluate.append(symbol)

        if investments_to_evaluate:
            logger.info(f"Performing scheduled evaluation of {len(investments_to_evaluate)} investments")

            # Evaluate in batches to avoid overwhelming the system
            batch_size = 10
            for i in range(0, len(investments_to_evaluate), batch_size):
                batch = investments_to_evaluate[i : i + batch_size]
                tasks = [self.evaluate_investment(symbol) for symbol in batch]
                await asyncio.gather(*tasks, return_exceptions=True)

                # Small delay between batches
                if i + batch_size < len(investments_to_evaluate):
                    await asyncio.sleep(30)

    def _is_grade_degradation(self, prev_grade: Grade, new_grade: Grade, prev_score: float, new_score: float) -> bool:
        """Check if there's a significant grade degradation."""
        # Grade order for comparison
        grade_order = {"A+": 8, "A": 7, "B+": 6, "B": 5, "C+": 4, "C": 3, "D": 2, "F": 1}

        prev_order = grade_order.get(prev_grade, 0)
        new_order = grade_order.get(new_grade, 0)

        # Check for grade drop or significant score drop
        grade_dropped = new_order < prev_order
        significant_score_drop = new_score < prev_score - 0.05  # 5% drop threshold

        return grade_dropped or significant_score_drop

    async def _handle_grade_degradation(
        self,
        symbol: str,
        metrics: PerformanceMetrics,
        prev_grade: Grade,
        new_grade: Grade,
        prev_score: float,
        new_score: float,
    ) -> None:
        """Handle grade degradation by creating alerts and notifications."""
        try:
            # Determine severity
            severity = self._determine_alert_severity(prev_grade, new_grade, prev_score, new_score)

            # Analyze degradation factors (simplified)
            degradation_factors = self._analyze_degradation_factors(symbol, prev_score, new_score)

            # Generate recommended actions
            recommended_actions = self._generate_recommended_actions(symbol, new_grade, degradation_factors)

            # Find replacement candidates (simplified)
            replacement_candidates = await self._find_replacement_candidates(symbol, metrics.asset_type)

            # Create alert
            alert = GradeDegradationAlert(
                symbol=symbol,
                asset_type=metrics.asset_type,
                previous_grade=prev_grade,
                current_grade=new_grade,
                previous_score=prev_score,
                current_score=new_score,
                score_change=new_score - prev_score,
                degradation_factors=degradation_factors,
                severity=severity,
                recommended_actions=recommended_actions,
                replacement_candidates=replacement_candidates,
            )

            # Store alert
            self.alert_history.append(alert)

            # Send notification if within threshold
            if severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]:
                await self._send_degradation_notification(alert)

            # Record metrics
            self.metrics_collector.record_counter("a_plus_monitoring.degradation_alerts", tags={"severity": severity.value})

            logger.warning(f"Grade degradation detected for {symbol}: {prev_grade} -> {new_grade} (severity: {severity.value})")

        except Exception as e:
            logger.error(f"Failed to handle grade degradation for {symbol}: {str(e)}")

    def _determine_alert_severity(self, prev_grade: Grade, new_grade: Grade, prev_score: float, new_score: float) -> AlertSeverity:
        """Determine the severity of a grade degradation alert."""
        score_drop = prev_score - new_score

        # Critical: A+ to B+ or lower, or >15% score drop
        if (prev_grade == "A+" and new_grade not in ["A+", "A"]) or score_drop > 0.15:
            return AlertSeverity.CRITICAL

        # High: A+ to A, or A to B+/lower, or >10% score drop
        if (prev_grade == "A+" and new_grade == "A") or (prev_grade == "A" and new_grade not in ["A", "B+"]) or score_drop > 0.10:
            return AlertSeverity.HIGH

        # Medium: Any grade drop with >5% score drop
        if score_drop > 0.05:
            return AlertSeverity.MEDIUM

        return AlertSeverity.LOW

    def _analyze_degradation_factors(self, symbol: str, prev_score: float, new_score: float) -> list[str]:
        """Analyze potential factors causing grade degradation."""
        factors = []

        score_drop = prev_score - new_score

        if score_drop > 0.10:
            factors.append("Significant fundamental deterioration")
        elif score_drop > 0.05:
            factors.append("Moderate performance decline")

        # In production, would analyze specific metrics that changed
        factors.extend(
            [
                "Market conditions impact",
                "Sector-specific headwinds",
                "Company-specific issues",
            ]
        )

        return factors[:5]  # Limit to top 5 factors

    def _generate_recommended_actions(self, symbol: str, new_grade: Grade, factors: list[str]) -> list[str]:
        """Generate recommended actions based on degradation."""
        actions = []

        if new_grade in ["D", "F"]:
            actions.append("Consider immediate position reduction or exit")
        elif new_grade in ["C", "C+"]:
            actions.append("Monitor closely and consider reducing position size")
        elif new_grade in ["B", "B+"]:
            actions.append("Maintain position but halt additional investments")
        else:
            actions.append("Continue monitoring for further changes")

        actions.append("Review fundamental analysis for changes")
        actions.append("Consider rebalancing to maintain portfolio quality")

        return actions

    async def _find_replacement_candidates(self, symbol: str, asset_type: Literal["etf", "stock", "crypto"]) -> list[str]:
        """Find potential replacement candidates for degraded investment."""
        # Simplified implementation - in production would use market screening
        replacement_map = {
            "etf": ["SPY", "VTI", "VXUS", "BND"],
            "stock": ["AAPL", "MSFT", "GOOGL", "AMZN"],
            "crypto": ["BTC-USD", "ETH-USD"],
        }

        candidates = replacement_map.get(asset_type, [])
        # Filter out the degraded symbol itself
        return [c for c in candidates if c != symbol][:3]

    async def _send_degradation_notification(self, alert: GradeDegradationAlert) -> None:
        """Send notification for grade degradation."""
        try:
            message = (
                f"🚨 A+ Grade Degradation Alert\n\n"
                f"Investment: {alert.symbol}\n"
                f"Grade Change: {alert.previous_grade} → {alert.current_grade}\n"
                f"Score Change: {alert.previous_score:.3f} → {alert.current_score:.3f}\n"
                f"Severity: {alert.severity.value.upper()}\n\n"
                f"Factors: {', '.join(alert.degradation_factors[:3])}\n\n"
                f"Recommended Actions:\n" + "\n".join(f"• {action}" for action in alert.recommended_actions[:3])
            )

            await self.notification_service.send_alert(
                title=f"A+ Degradation: {alert.symbol}",
                message=message,
                severity=alert.severity.value,
                tags={"type": "grade_degradation", "symbol": alert.symbol},
            )

        except Exception as e:
            logger.error(f"Failed to send degradation notification: {str(e)}")

    def _is_significant_regime_change(self, prev_regime: MarketRegime, new_regime: MarketRegime) -> bool:
        """Check if market regime change is significant enough to trigger re-evaluation."""
        return (
            prev_regime.regime_type != new_regime.regime_type
            or prev_regime.market_stress_level != new_regime.market_stress_level
            or abs(prev_regime.vix_level - new_regime.vix_level) > 5
            or abs(prev_regime.inflation_rate - new_regime.inflation_rate) > 1
        )

    def _cleanup_old_data(self) -> None:
        """Clean up old monitoring data to prevent memory bloat."""
        cutoff_date = datetime.now() - timedelta(days=90)

        # Clean up old alerts
        self.alert_history = deque([alert for alert in self.alert_history if alert.alert_timestamp >= cutoff_date], maxlen=1000)

        # Clean up old performance history
        for symbol in list(self.performance_history.keys()):
            history = self.performance_history[symbol]
            cleaned_history = deque(
                [entry for entry in history if datetime.fromisoformat(entry["timestamp"]) >= cutoff_date], maxlen=100
            )
            if cleaned_history:
                self.performance_history[symbol] = cleaned_history
            else:
                del self.performance_history[symbol]

    def _update_monitoring_metrics(self) -> None:
        """Update monitoring system metrics."""
        active_investments = self.get_active_investments()

        self.metrics_collector.record_gauge("a_plus_monitoring.total_monitored", len(active_investments))
        self.metrics_collector.record_gauge(
            "a_plus_monitoring.a_plus_count", sum(1 for m in active_investments.values() if m.current_score >= 0.95)
        )
        self.metrics_collector.record_gauge("a_plus_monitoring.recent_alerts", len(self.get_degradation_alerts(24)))


# Global monitoring system instance
_monitoring_system: APlusMonitoringSystem | None = None


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
