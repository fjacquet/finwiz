"""
Monitoring Alerts for A+ Investment System.

This module provides alert generation and management functionality
for A+ investment monitoring including grade degradation alerts,
performance alerts, and notification management.
"""

from collections.abc import Callable
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from finwiz.schemas.investment_discovery import APlusAnalysis, InvestmentCandidate, MarketRegime
from finwiz.schemas.portfolio_review import Grade
from finwiz.tools.logger import get_logger
from finwiz.tools.notification_service import NotificationService

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
    previous_grade: Grade = Field(..., description="Previous grade")
    current_grade: Grade = Field(..., description="Current grade")
    degradation_reason: str = Field(..., description="Reason for degradation")
    severity: AlertSeverity = Field(..., description="Alert severity")
    timestamp: datetime = Field(default_factory=datetime.now, description="Alert timestamp")

    # Additional context
    score_change: float = Field(default=0.0, description="Change in A+ score")
    recommendation: str = Field(default="", description="Recommended action")
    market_context: str = Field(default="", description="Market context information")


class AlertManager:
    """
    Manager for A+ monitoring alerts.

    This class handles alert generation, severity assessment, and
    notification dispatch for A+ investment monitoring events.
    """

    def __init__(self, notification_service: NotificationService | None = None) -> None:
        """
        Initialize the alert manager.

        Args:
            notification_service: Optional notification service for alert dispatch

        """
        self.logger = get_logger(__name__)
        self.notification_service = notification_service or NotificationService()
        self._alert_handlers: dict[MonitoringEvent, list[Callable]] = {}
        self._alert_history: list[GradeDegradationAlert] = []

    def register_alert_handler(self, event_type: MonitoringEvent, handler: Callable) -> None:
        """
        Register a handler for specific alert types.

        Args:
            event_type: Type of monitoring event
            handler: Callable to handle the alert

        """
        if event_type not in self._alert_handlers:
            self._alert_handlers[event_type] = []

        self._alert_handlers[event_type].append(handler)
        self.logger.info(f"Registered alert handler for {event_type.value}")

    async def generate_grade_degradation_alert(
        self,
        candidate: InvestmentCandidate,
        previous_grade: Grade,
        analysis: APlusAnalysis,
    ) -> GradeDegradationAlert:
        """
        Generate an alert for grade degradation.

        Args:
            candidate: Investment candidate with degraded grade
            previous_grade: Previous grade before degradation
            analysis: Current A+ analysis

        Returns:
            GradeDegradationAlert with alert details

        """
        # Determine severity based on grade change
        severity = self._assess_degradation_severity(previous_grade, candidate.current_grade)

        # Generate degradation reason
        degradation_reason = self._analyze_degradation_reason(analysis)

        # Calculate score change
        score_change = self._calculate_score_change(previous_grade, candidate.current_grade)

        # Generate recommendation
        recommendation = self._generate_recommendation(candidate, analysis, severity)

        # Get market context
        market_context = self._get_market_context(analysis)

        alert = GradeDegradationAlert(
            symbol=candidate.symbol,
            previous_grade=previous_grade,
            current_grade=candidate.current_grade,
            degradation_reason=degradation_reason,
            severity=severity,
            score_change=score_change,
            recommendation=recommendation,
            market_context=market_context,
        )

        # Store alert history
        self._alert_history.append(alert)

        # Dispatch alert
        await self._dispatch_alert(MonitoringEvent.GRADE_DEGRADATION, alert)

        self.logger.info(
            f"Generated grade degradation alert for {candidate.symbol}: {previous_grade.value} -> {candidate.current_grade.value}"
        )

        return alert

    async def generate_performance_alert(
        self,
        candidate: InvestmentCandidate,
        performance_metrics: dict[str, Any],
        threshold_breach: str,
    ) -> None:
        """
        Generate an alert for performance issues.

        Args:
            candidate: Investment candidate with performance issues
            performance_metrics: Performance metrics that triggered the alert
            threshold_breach: Description of threshold breach

        """
        severity = self._assess_performance_severity(performance_metrics)

        alert_data = {
            "symbol": candidate.symbol,
            "threshold_breach": threshold_breach,
            "performance_metrics": performance_metrics,
            "severity": severity,
            "timestamp": datetime.now(),
        }

        await self._dispatch_alert(MonitoringEvent.PERFORMANCE_DECLINE, alert_data)

        self.logger.warning(f"Generated performance alert for {candidate.symbol}: {threshold_breach}")

    async def generate_market_regime_alert(
        self,
        previous_regime: MarketRegime,
        current_regime: MarketRegime,
        impact_assessment: dict[str, Any],
    ) -> None:
        """
        Generate an alert for market regime changes.

        Args:
            previous_regime: Previous market regime
            current_regime: Current market regime
            impact_assessment: Assessment of impact on A+ investments

        """
        severity = self._assess_regime_change_severity(previous_regime, current_regime, impact_assessment)

        alert_data = {
            "previous_regime": previous_regime,
            "current_regime": current_regime,
            "impact_assessment": impact_assessment,
            "severity": severity,
            "timestamp": datetime.now(),
        }

        await self._dispatch_alert(MonitoringEvent.MARKET_REGIME_SHIFT, alert_data)

        self.logger.info(f"Generated market regime alert: {previous_regime.value} -> {current_regime.value}")

    def get_alert_history(self, days: int = 30) -> list[GradeDegradationAlert]:
        """
        Get alert history for the specified period.

        Args:
            days: Number of days to look back

        Returns:
            List of alerts from the specified period

        """
        cutoff_date = datetime.now() - datetime.timedelta(days=days)
        return [alert for alert in self._alert_history if alert.timestamp >= cutoff_date]

    def get_alert_summary(self) -> dict[str, Any]:
        """
        Get summary of recent alerts.

        Returns:
            Dictionary with alert summary statistics

        """
        recent_alerts = self.get_alert_history(7)  # Last 7 days

        severity_counts = {}
        for severity in AlertSeverity:
            severity_counts[severity.value] = len([a for a in recent_alerts if a.severity == severity])

        return {
            "total_alerts": len(recent_alerts),
            "severity_breakdown": severity_counts,
            "most_recent": recent_alerts[-1].timestamp if recent_alerts else None,
            "symbols_affected": len(set(alert.symbol for alert in recent_alerts)),
        }

    def _assess_degradation_severity(self, previous_grade: Grade, current_grade: Grade) -> AlertSeverity:
        """Assess severity of grade degradation."""
        grade_values = {
            Grade.A_PLUS: 4,
            Grade.A: 3,
            Grade.B_PLUS: 2,
            Grade.B: 1,
            Grade.C: 0,
        }

        previous_value = grade_values.get(previous_grade, 0)
        current_value = grade_values.get(current_grade, 0)
        degradation_level = previous_value - current_value

        if degradation_level >= 3:
            return AlertSeverity.CRITICAL
        elif degradation_level == 2:
            return AlertSeverity.HIGH
        elif degradation_level == 1:
            return AlertSeverity.MEDIUM
        else:
            return AlertSeverity.LOW

    def _analyze_degradation_reason(self, analysis: APlusAnalysis) -> str:
        """Analyze the reason for grade degradation."""
        reasons = []

        # Check various factors that could cause degradation
        if hasattr(analysis, "financial_strength_score") and analysis.financial_strength_score < 0.7:
            reasons.append("Declining financial strength")

        if hasattr(analysis, "growth_quality_score") and analysis.growth_quality_score < 0.7:
            reasons.append("Reduced growth quality")

        if hasattr(analysis, "valuation_score") and analysis.valuation_score < 0.6:
            reasons.append("Valuation concerns")

        if hasattr(analysis, "market_position_score") and analysis.market_position_score < 0.7:
            reasons.append("Weakened market position")

        if not reasons:
            reasons.append("Multiple factors contributing to score decline")

        return "; ".join(reasons)

    def _calculate_score_change(self, previous_grade: Grade, current_grade: Grade) -> float:
        """Calculate approximate score change based on grade change."""
        grade_scores = {
            Grade.A_PLUS: 0.9,
            Grade.A: 0.8,
            Grade.B_PLUS: 0.7,
            Grade.B: 0.6,
            Grade.C: 0.5,
        }

        previous_score = grade_scores.get(previous_grade, 0.5)
        current_score = grade_scores.get(current_grade, 0.5)

        return current_score - previous_score

    def _generate_recommendation(self, candidate: InvestmentCandidate, analysis: APlusAnalysis, severity: AlertSeverity) -> str:
        """Generate recommendation based on degradation."""
        if severity == AlertSeverity.CRITICAL:
            return f"IMMEDIATE ACTION: Consider selling {candidate.symbol} due to significant grade degradation"
        elif severity == AlertSeverity.HIGH:
            return f"REVIEW REQUIRED: Reassess position in {candidate.symbol} and consider reducing exposure"
        elif severity == AlertSeverity.MEDIUM:
            return f"MONITOR CLOSELY: Watch {candidate.symbol} for further degradation signals"
        else:
            return f"CONTINUE MONITORING: {candidate.symbol} shows minor grade decline"

    def _get_market_context(self, analysis: APlusAnalysis) -> str:
        """Get market context for the alert."""
        context_parts = []

        if hasattr(analysis, "market_regime"):
            context_parts.append(f"Market regime: {analysis.market_regime.value}")

        if hasattr(analysis, "sector_performance"):
            context_parts.append("Sector showing mixed performance")

        if not context_parts:
            context_parts.append("General market conditions apply")

        return "; ".join(context_parts)

    def _assess_performance_severity(self, performance_metrics: dict[str, Any]) -> AlertSeverity:
        """Assess severity of performance issues."""
        # Simplified severity assessment
        decline_percentage = performance_metrics.get("decline_percentage", 0)

        if decline_percentage > 20:
            return AlertSeverity.CRITICAL
        elif decline_percentage > 15:
            return AlertSeverity.HIGH
        elif decline_percentage > 10:
            return AlertSeverity.MEDIUM
        else:
            return AlertSeverity.LOW

    def _assess_regime_change_severity(
        self, previous_regime: MarketRegime, current_regime: MarketRegime, impact_assessment: dict[str, Any]
    ) -> AlertSeverity:
        """Assess severity of market regime change."""
        # Simplified assessment based on regime transition
        high_impact_transitions = [
            (MarketRegime.BULL_MARKET, MarketRegime.BEAR_MARKET),
            (MarketRegime.LOW_VOLATILITY, MarketRegime.HIGH_VOLATILITY),
        ]

        if (previous_regime, current_regime) in high_impact_transitions:
            return AlertSeverity.HIGH
        else:
            return AlertSeverity.MEDIUM

    async def _dispatch_alert(self, event_type: MonitoringEvent, alert_data: Any) -> None:
        """Dispatch alert to registered handlers and notification service."""
        # Call registered handlers
        if event_type in self._alert_handlers:
            for handler in self._alert_handlers[event_type]:
                try:
                    await handler(alert_data)
                except Exception as e:
                    self.logger.error(f"Error in alert handler for {event_type.value}: {e}")

        # Send notification
        try:
            await self._send_notification(event_type, alert_data)
        except Exception as e:
            self.logger.error(f"Error sending notification for {event_type.value}: {e}")

    async def _send_notification(self, event_type: MonitoringEvent, alert_data: Any) -> None:
        """Send notification through notification service."""
        if isinstance(alert_data, GradeDegradationAlert):
            title = f"Grade Degradation Alert: {alert_data.symbol}"
            message = f"{alert_data.symbol} degraded from {alert_data.previous_grade.value} to {alert_data.current_grade.value}"

            await self.notification_service.send_alert(
                title=title,
                message=message,
                severity=alert_data.severity.value,
                metadata={"symbol": alert_data.symbol, "event_type": event_type.value},
            )
        else:
            # Handle other alert types
            title = f"A+ Monitoring Alert: {event_type.value}"
            message = f"Alert generated for {event_type.value}"

            await self.notification_service.send_alert(
                title=title, message=message, severity="medium", metadata={"event_type": event_type.value}
            )
