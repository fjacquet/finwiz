"""
Portfolio monitoring system for continuous drift monitoring and alerting.

This module provides real-time portfolio monitoring capabilities, including
drift detection, alert generation, and automated rebalancing triggers.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from finwiz.quantitative.portfolio_analyzer import PortfolioAnalyzer
from finwiz.quantitative.rebalancing_engine import RebalancingEngine
from finwiz.schemas.portfolio_rebalancing import (
    PortfolioConfiguration,
    RebalancingNeed,
    UrgencyLevel,
)
from finwiz.tools.portfolio_price_service import PortfolioPriceService

logger = logging.getLogger(__name__)


class MonitoringRule(BaseModel):
    """Configuration for automated monitoring rules."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    rule_id: str = Field(..., description="Unique rule identifier")
    rule_name: str = Field(..., description="Human-readable rule name")
    enabled: bool = Field(default=True, description="Whether rule is active")

    # Trigger conditions
    max_deviation_threshold: float = Field(default=0.10, gt=0, le=1, description="Maximum allowed deviation (10% = 0.10)")
    min_check_interval_hours: int = Field(default=1, ge=1, le=168, description="Minimum hours between checks")

    # Alert conditions
    alert_on_deviation: bool = Field(default=True, description="Alert when deviation exceeds threshold")
    alert_on_multiple_positions: bool = Field(default=True, description="Alert when multiple positions need rebalancing")
    min_positions_for_alert: int = Field(default=2, ge=1, description="Minimum positions needing rebalancing to trigger alert")

    # Auto-rebalancing
    enable_auto_rebalancing: bool = Field(default=False, description="Enable automated rebalancing")
    auto_rebalance_threshold: float = Field(default=0.15, gt=0, le=1, description="Threshold for auto-rebalancing")
    max_auto_rebalance_frequency_days: int = Field(default=7, ge=1, description="Minimum days between auto-rebalancing")


class AlertType(str, Enum):
    """Alert type enumeration."""

    DEVIATION_ALERT = "DEVIATION_ALERT"
    MULTIPLE_POSITIONS_ALERT = "MULTIPLE_POSITIONS_ALERT"
    AUTO_REBALANCE_TRIGGERED = "AUTO_REBALANCE_TRIGGERED"
    MONITORING_ERROR = "MONITORING_ERROR"
    PRICE_DATA_STALE = "PRICE_DATA_STALE"


class AlertSeverity(str, Enum):
    """Alert severity enumeration."""

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class PortfolioAlert(BaseModel):
    """Portfolio monitoring alert."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    # Alert identification
    alert_id: str = Field(..., description="Unique alert identifier")
    portfolio_id: str = Field(..., description="Portfolio identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="Alert timestamp")

    # Alert details
    alert_type: AlertType = Field(..., description="Type of alert")
    severity: AlertSeverity = Field(..., description="Alert severity")
    title: str = Field(..., description="Alert title")
    message: str = Field(..., description="Detailed alert message")

    # Context data
    affected_positions: list[str] = Field(default_factory=list, description="Positions affected by alert")
    current_deviations: dict[str, float] = Field(default_factory=dict, description="Current deviations by position")
    recommended_actions: list[str] = Field(default_factory=list, description="Recommended actions")

    # Status
    acknowledged: bool = Field(default=False, description="Whether alert has been acknowledged")
    resolved: bool = Field(default=False, description="Whether alert has been resolved")
    resolution_notes: str | None = Field(None, description="Resolution notes")


class MonitoringStatus(BaseModel):
    """Current monitoring status for a portfolio."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    portfolio_id: str = Field(..., description="Portfolio identifier")
    last_check_timestamp: datetime = Field(..., description="Last monitoring check timestamp")
    next_check_timestamp: datetime = Field(..., description="Next scheduled check timestamp")

    # Current state
    monitoring_active: bool = Field(..., description="Whether monitoring is active")
    positions_monitored: int = Field(..., ge=0, description="Number of positions being monitored")
    positions_out_of_tolerance: int = Field(..., ge=0, description="Positions currently out of tolerance")

    # Alert summary
    active_alerts: int = Field(..., ge=0, description="Number of active alerts")
    unacknowledged_alerts: int = Field(..., ge=0, description="Number of unacknowledged alerts")
    last_alert_timestamp: datetime | None = Field(None, description="Timestamp of last alert")

    # Health indicators
    price_data_freshness_minutes: int = Field(..., ge=0, description="Age of price data in minutes")
    monitoring_health_score: float = Field(..., ge=0, le=10, description="Overall monitoring health score")


class PortfolioHealthDashboard(BaseModel):
    """Portfolio health dashboard data."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    portfolio_id: str = Field(..., description="Portfolio identifier")
    dashboard_timestamp: datetime = Field(default_factory=datetime.now, description="Dashboard generation timestamp")

    # Overall health
    overall_health_score: float = Field(..., ge=0, le=10, description="Overall portfolio health score")
    health_status: str = Field(..., description="Health status description")

    # Deviation analysis
    max_deviation: float = Field(..., ge=0, description="Maximum position deviation")
    avg_deviation: float = Field(..., ge=0, description="Average position deviation")
    positions_needing_attention: list[RebalancingNeed] = Field(..., description="Positions needing attention")

    # Rebalancing recommendations
    rebalancing_urgency: UrgencyLevel = Field(..., description="Overall rebalancing urgency")
    estimated_rebalancing_cost: float = Field(..., ge=0, description="Estimated cost to rebalance")
    days_since_last_rebalance: int | None = Field(None, ge=0, description="Days since last rebalancing")

    # Monitoring status
    monitoring_status: MonitoringStatus = Field(..., description="Current monitoring status")
    recent_alerts: list[PortfolioAlert] = Field(default_factory=list, description="Recent alerts")


class PortfolioMonitor:
    """Portfolio monitoring system for continuous drift monitoring and alerting."""

    def __init__(
        self,
        price_service: PortfolioPriceService | None = None,
        portfolio_analyzer: PortfolioAnalyzer | None = None,
        rebalancing_engine: RebalancingEngine | None = None,
    ) -> None:
        """Initialize portfolio monitor."""
        self.price_service = price_service or PortfolioPriceService()
        self.portfolio_analyzer = portfolio_analyzer or PortfolioAnalyzer()
        self.rebalancing_engine = rebalancing_engine or RebalancingEngine()

        # Internal state
        self._monitoring_tasks: dict[str, asyncio.Task] = {}
        self._monitoring_rules: dict[str, MonitoringRule] = {}
        self._alert_history: dict[str, list[PortfolioAlert]] = {}
        self._last_check_times: dict[str, datetime] = {}

        logger.info("Portfolio monitor initialized")

    async def start_monitoring(
        self, portfolio_id: str, portfolio_config: PortfolioConfiguration, monitoring_rule: MonitoringRule | None = None
    ) -> None:
        """Start monitoring a portfolio for drift and rebalancing needs."""
        try:
            # Use default rule if none provided
            if monitoring_rule is None:
                monitoring_rule = MonitoringRule(
                    rule_id=f"default_{portfolio_id}", rule_name=f"Default monitoring for {portfolio_id}"
                )

            # Store monitoring configuration
            self._monitoring_rules[portfolio_id] = monitoring_rule
            self._alert_history[portfolio_id] = []

            # Cancel existing monitoring task if running
            if portfolio_id in self._monitoring_tasks:
                self._monitoring_tasks[portfolio_id].cancel()

            # Start new monitoring task
            task = asyncio.create_task(self._monitor_portfolio_loop(portfolio_id, portfolio_config, monitoring_rule))
            self._monitoring_tasks[portfolio_id] = task

            logger.info(f"Started monitoring portfolio {portfolio_id}")

        except Exception as e:
            logger.error(f"Failed to start monitoring for portfolio {portfolio_id}: {e}")
            raise

    async def stop_monitoring(self, portfolio_id: str) -> None:
        """Stop monitoring a portfolio."""
        try:
            if portfolio_id in self._monitoring_tasks:
                self._monitoring_tasks[portfolio_id].cancel()
                del self._monitoring_tasks[portfolio_id]
                logger.info(f"Stopped monitoring portfolio {portfolio_id}")

            # Clean up monitoring data
            self._monitoring_rules.pop(portfolio_id, None)
            self._last_check_times.pop(portfolio_id, None)

        except Exception as e:
            logger.error(f"Failed to stop monitoring for portfolio {portfolio_id}: {e}")
            raise

    async def check_portfolio_drift(self, portfolio_id: str, portfolio_config: PortfolioConfiguration) -> list[RebalancingNeed]:
        """Check current portfolio drift against targets."""
        try:
            # Get current prices
            symbols = [holding.symbol for holding in portfolio_config.holdings]
            prices = await self.price_service.get_current_prices(symbols)

            # Analyze current portfolio
            current_analysis = self.portfolio_analyzer.analyze_current_portfolio(portfolio_config.holdings, prices)

            # Identify rebalancing needs
            rebalancing_needs = self.portfolio_analyzer.identify_rebalancing_needs(
                current_analysis.weightings,
                portfolio_config.target_weights,
                portfolio_config.tolerance_bands,
                portfolio_config.global_tolerance,
            )

            # Update last check time
            self._last_check_times[portfolio_id] = datetime.now()

            return rebalancing_needs

        except Exception as e:
            logger.error(f"Failed to check portfolio drift for {portfolio_id}: {e}")
            raise

    async def generate_health_dashboard(
        self, portfolio_id: str, portfolio_config: PortfolioConfiguration
    ) -> PortfolioHealthDashboard:
        """Generate comprehensive portfolio health dashboard."""
        try:
            # Check current drift
            rebalancing_needs = await self.check_portfolio_drift(portfolio_id, portfolio_config)

            # Calculate health metrics
            positions_needing_attention = [need for need in rebalancing_needs if need.exceeds_tolerance]
            max_deviation = max([abs(need.deviation) for need in rebalancing_needs], default=0.0)
            avg_deviation = (
                sum([abs(need.deviation) for need in rebalancing_needs]) / len(rebalancing_needs) if rebalancing_needs else 0.0
            )

            # Determine overall health score (1-10 scale)
            health_score = self._calculate_health_score(rebalancing_needs, portfolio_config)

            # Determine rebalancing urgency
            urgency = self._determine_rebalancing_urgency(positions_needing_attention, max_deviation)

            # Get monitoring status
            monitoring_status = self._get_monitoring_status(portfolio_id)

            # Get recent alerts
            recent_alerts = self._get_recent_alerts(portfolio_id, hours=24)

            # Estimate rebalancing cost if needed
            estimated_cost = 0.0
            if positions_needing_attention:
                # This would typically call the rebalancing engine to estimate costs
                estimated_cost = len(positions_needing_attention) * 10.0  # Simplified estimate

            return PortfolioHealthDashboard(
                portfolio_id=portfolio_id,
                overall_health_score=health_score,
                health_status=self._get_health_status_description(health_score),
                max_deviation=max_deviation,
                avg_deviation=avg_deviation,
                positions_needing_attention=positions_needing_attention,
                rebalancing_urgency=urgency,
                estimated_rebalancing_cost=estimated_cost,
                days_since_last_rebalance=self._get_days_since_last_rebalance(portfolio_id),
                monitoring_status=monitoring_status,
                recent_alerts=recent_alerts,
            )

        except Exception as e:
            logger.error(f"Failed to generate health dashboard for {portfolio_id}: {e}")
            raise

    async def _monitor_portfolio_loop(
        self, portfolio_id: str, portfolio_config: PortfolioConfiguration, monitoring_rule: MonitoringRule
    ) -> None:
        """Run main monitoring loop for a portfolio."""
        logger.info(f"Starting monitoring loop for portfolio {portfolio_id}")

        try:
            while monitoring_rule.enabled:
                try:
                    # Check if enough time has passed since last check
                    last_check = self._last_check_times.get(portfolio_id)
                    if last_check:
                        time_since_check = datetime.now() - last_check
                        if time_since_check.total_seconds() < monitoring_rule.min_check_interval_hours * 3600:
                            # Wait until next check time
                            sleep_time = monitoring_rule.min_check_interval_hours * 3600 - time_since_check.total_seconds()
                            await asyncio.sleep(sleep_time)
                            continue

                    # Perform drift check
                    rebalancing_needs = await self.check_portfolio_drift(portfolio_id, portfolio_config)

                    # Process monitoring rules
                    await self._process_monitoring_rules(portfolio_id, portfolio_config, rebalancing_needs, monitoring_rule)

                    # Sleep until next check
                    await asyncio.sleep(monitoring_rule.min_check_interval_hours * 3600)

                except asyncio.CancelledError:
                    logger.info(f"Monitoring cancelled for portfolio {portfolio_id}")
                    break
                except Exception as e:
                    logger.error(f"Error in monitoring loop for {portfolio_id}: {e}")
                    # Generate error alert
                    await self._generate_alert(
                        portfolio_id=portfolio_id,
                        alert_type=AlertType.MONITORING_ERROR,
                        severity=AlertSeverity.ERROR,
                        title="Monitoring Error",
                        message=f"Error occurred during monitoring: {str(e)}",
                        affected_positions=[],
                        current_deviations={},
                        recommended_actions=["Check monitoring system", "Review error logs"],
                    )
                    # Wait before retrying
                    await asyncio.sleep(300)  # 5 minutes

        except Exception as e:
            logger.error(f"Fatal error in monitoring loop for {portfolio_id}: {e}")
        finally:
            logger.info(f"Monitoring loop ended for portfolio {portfolio_id}")

    async def _process_monitoring_rules(
        self,
        portfolio_id: str,
        portfolio_config: PortfolioConfiguration,
        rebalancing_needs: list[RebalancingNeed],
        monitoring_rule: MonitoringRule,
    ) -> None:
        """Process monitoring rules and generate alerts as needed."""
        try:
            positions_out_of_tolerance = [need for need in rebalancing_needs if need.exceeds_tolerance]
            max_deviation = max([abs(need.deviation) for need in rebalancing_needs], default=0.0)

            # Check deviation threshold rule
            if monitoring_rule.alert_on_deviation and max_deviation > monitoring_rule.max_deviation_threshold:
                await self._generate_deviation_alert(portfolio_id, positions_out_of_tolerance, max_deviation, monitoring_rule)

            # Check multiple positions rule
            if (
                monitoring_rule.alert_on_multiple_positions
                and len(positions_out_of_tolerance) >= monitoring_rule.min_positions_for_alert
            ):
                await self._generate_multiple_positions_alert(portfolio_id, positions_out_of_tolerance, monitoring_rule)

            # Check auto-rebalancing rule
            if monitoring_rule.enable_auto_rebalancing and max_deviation > monitoring_rule.auto_rebalance_threshold:
                await self._check_auto_rebalancing(portfolio_id, portfolio_config, positions_out_of_tolerance, monitoring_rule)

        except Exception as e:
            logger.error(f"Error processing monitoring rules for {portfolio_id}: {e}")
            raise

    async def _generate_deviation_alert(
        self,
        portfolio_id: str,
        positions_out_of_tolerance: list[RebalancingNeed],
        max_deviation: float,
        monitoring_rule: MonitoringRule,
    ) -> None:
        """Generate alert for deviation threshold breach."""
        affected_positions = [need.symbol for need in positions_out_of_tolerance]
        current_deviations = {need.symbol: need.deviation for need in positions_out_of_tolerance}

        severity = AlertSeverity.WARNING
        if max_deviation > monitoring_rule.max_deviation_threshold * 2:
            severity = AlertSeverity.ERROR
        if max_deviation > monitoring_rule.max_deviation_threshold * 3:
            severity = AlertSeverity.CRITICAL

        await self._generate_alert(
            portfolio_id=portfolio_id,
            alert_type=AlertType.DEVIATION_ALERT,
            severity=severity,
            title=f"Portfolio Deviation Alert - {max_deviation:.1%}",
            message=f"Portfolio has {len(positions_out_of_tolerance)} positions exceeding tolerance bands. "
            f"Maximum deviation: {max_deviation:.1%} (threshold: {monitoring_rule.max_deviation_threshold:.1%})",
            affected_positions=affected_positions,
            current_deviations=current_deviations,
            recommended_actions=[
                "Review portfolio allocations",
                "Consider rebalancing affected positions",
                "Check if tolerance bands need adjustment",
            ],
        )

    async def _generate_multiple_positions_alert(
        self, portfolio_id: str, positions_out_of_tolerance: list[RebalancingNeed], monitoring_rule: MonitoringRule
    ) -> None:
        """Generate alert for multiple positions needing rebalancing."""
        affected_positions = [need.symbol for need in positions_out_of_tolerance]
        current_deviations = {need.symbol: need.deviation for need in positions_out_of_tolerance}

        await self._generate_alert(
            portfolio_id=portfolio_id,
            alert_type=AlertType.MULTIPLE_POSITIONS_ALERT,
            severity=AlertSeverity.WARNING,
            title=f"Multiple Positions Need Rebalancing - {len(positions_out_of_tolerance)} positions",
            message=f"{len(positions_out_of_tolerance)} positions are outside tolerance bands and may need rebalancing. "
            f"Consider comprehensive portfolio rebalancing.",
            affected_positions=affected_positions,
            current_deviations=current_deviations,
            recommended_actions=[
                "Run comprehensive rebalancing analysis",
                "Review overall portfolio strategy",
                "Consider batch rebalancing to minimize costs",
            ],
        )

    async def _check_auto_rebalancing(
        self,
        portfolio_id: str,
        portfolio_config: PortfolioConfiguration,
        positions_out_of_tolerance: list[RebalancingNeed],
        monitoring_rule: MonitoringRule,
    ) -> None:
        """Check if auto-rebalancing should be triggered."""
        # Check if enough time has passed since last auto-rebalancing
        # This would typically check a database or cache for last auto-rebalancing time
        # For now, we'll just generate an alert that auto-rebalancing is recommended

        affected_positions = [need.symbol for need in positions_out_of_tolerance]
        current_deviations = {need.symbol: need.deviation for need in positions_out_of_tolerance}

        await self._generate_alert(
            portfolio_id=portfolio_id,
            alert_type=AlertType.AUTO_REBALANCE_TRIGGERED,
            severity=AlertSeverity.INFO,
            title="Auto-Rebalancing Recommended",
            message=f"Portfolio deviations exceed auto-rebalancing threshold. "
            f"Automated rebalancing is recommended for {len(positions_out_of_tolerance)} positions.",
            affected_positions=affected_positions,
            current_deviations=current_deviations,
            recommended_actions=[
                "Execute automated rebalancing",
                "Review rebalancing recommendations",
                "Confirm available capital for rebalancing",
            ],
        )

    async def _generate_alert(
        self,
        portfolio_id: str,
        alert_type: AlertType,
        severity: AlertSeverity,
        title: str,
        message: str,
        affected_positions: list[str],
        current_deviations: dict[str, float],
        recommended_actions: list[str],
    ) -> PortfolioAlert:
        """Generate and store a portfolio alert."""
        alert = PortfolioAlert(
            alert_id=f"{portfolio_id}_{alert_type.value}_{datetime.now().isoformat()}",
            portfolio_id=portfolio_id,
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            affected_positions=affected_positions,
            current_deviations=current_deviations,
            recommended_actions=recommended_actions,
        )

        # Store alert in history
        if portfolio_id not in self._alert_history:
            self._alert_history[portfolio_id] = []
        self._alert_history[portfolio_id].append(alert)

        # Keep only recent alerts (last 100)
        self._alert_history[portfolio_id] = self._alert_history[portfolio_id][-100:]

        logger.info(f"Generated {severity.value} alert for portfolio {portfolio_id}: {title}")

        return alert

    def _calculate_health_score(self, rebalancing_needs: list[RebalancingNeed], portfolio_config: PortfolioConfiguration) -> float:
        """Calculate overall portfolio health score (1-10 scale)."""
        if not rebalancing_needs:
            return 10.0

        # Calculate weighted deviation score
        total_deviation = sum([abs(need.deviation) for need in rebalancing_needs])
        avg_deviation = total_deviation / len(rebalancing_needs)

        # Calculate positions out of tolerance ratio
        positions_out_of_tolerance = len([need for need in rebalancing_needs if need.exceeds_tolerance])
        out_of_tolerance_ratio = positions_out_of_tolerance / len(rebalancing_needs)

        # Health score calculation (higher deviations and more positions out of tolerance = lower score)
        base_score = 10.0
        deviation_penalty = min(avg_deviation * 50, 5.0)  # Max 5 points penalty for deviation
        tolerance_penalty = out_of_tolerance_ratio * 3.0  # Max 3 points penalty for positions out of tolerance

        health_score = max(base_score - deviation_penalty - tolerance_penalty, 1.0)

        return round(health_score, 1)

    def _determine_rebalancing_urgency(
        self, positions_needing_attention: list[RebalancingNeed], max_deviation: float
    ) -> UrgencyLevel:
        """Determine overall rebalancing urgency level."""
        if not positions_needing_attention:
            return UrgencyLevel.LOW

        if max_deviation > 0.20:  # 20%+ deviation
            return UrgencyLevel.CRITICAL
        elif max_deviation > 0.15:  # 15%+ deviation
            return UrgencyLevel.HIGH
        elif len(positions_needing_attention) >= 3:  # Multiple positions
            return UrgencyLevel.MEDIUM
        else:
            return UrgencyLevel.LOW

    def _get_health_status_description(self, health_score: float) -> str:
        """Get health status description based on score."""
        if health_score >= 9.0:
            return "Excellent - Portfolio is well-balanced"
        elif health_score >= 7.0:
            return "Good - Minor deviations within acceptable range"
        elif health_score >= 5.0:
            return "Fair - Some positions may need attention"
        elif health_score >= 3.0:
            return "Poor - Multiple positions need rebalancing"
        else:
            return "Critical - Immediate rebalancing recommended"

    def _get_monitoring_status(self, portfolio_id: str) -> MonitoringStatus:
        """Get current monitoring status for a portfolio."""
        rule = self._monitoring_rules.get(portfolio_id)
        last_check = self._last_check_times.get(portfolio_id, datetime.now())

        # Calculate next check time
        next_check = last_check + timedelta(hours=rule.min_check_interval_hours if rule else 1)

        # Get alert counts
        alerts = self._alert_history.get(portfolio_id, [])
        active_alerts = len([alert for alert in alerts if not alert.resolved])
        unacknowledged_alerts = len([alert for alert in alerts if not alert.acknowledged])

        return MonitoringStatus(
            portfolio_id=portfolio_id,
            last_check_timestamp=last_check,
            next_check_timestamp=next_check,
            monitoring_active=portfolio_id in self._monitoring_tasks,
            positions_monitored=0,  # Would be calculated from actual portfolio
            positions_out_of_tolerance=0,  # Would be calculated from latest check
            active_alerts=active_alerts,
            unacknowledged_alerts=unacknowledged_alerts,
            last_alert_timestamp=alerts[-1].timestamp if alerts else None,
            price_data_freshness_minutes=5,  # Would be calculated from price service
            monitoring_health_score=8.5,  # Would be calculated based on system health
        )

    def _get_recent_alerts(self, portfolio_id: str, hours: int = 24) -> list[PortfolioAlert]:
        """Get recent alerts for a portfolio."""
        alerts = self._alert_history.get(portfolio_id, [])
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [alert for alert in alerts if alert.timestamp >= cutoff_time]

    def _get_days_since_last_rebalance(self, portfolio_id: str) -> int | None:
        """Get days since last rebalancing (would typically query database)."""
        # This would typically query a database for the last rebalancing date
        # For now, return None to indicate no data available
        return None

    async def get_active_alerts(self, portfolio_id: str) -> list[PortfolioAlert]:
        """Get all active (unresolved) alerts for a portfolio."""
        alerts = self._alert_history.get(portfolio_id, [])
        return [alert for alert in alerts if not alert.resolved]

    async def acknowledge_alert(self, portfolio_id: str, alert_id: str) -> bool:
        """Acknowledge an alert."""
        alerts = self._alert_history.get(portfolio_id, [])
        for alert in alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                logger.info(f"Acknowledged alert {alert_id} for portfolio {portfolio_id}")
                return True
        return False

    async def resolve_alert(self, portfolio_id: str, alert_id: str, resolution_notes: str = "") -> bool:
        """Resolve an alert."""
        alerts = self._alert_history.get(portfolio_id, [])
        for alert in alerts:
            if alert.alert_id == alert_id:
                alert.resolved = True
                alert.resolution_notes = resolution_notes
                logger.info(f"Resolved alert {alert_id} for portfolio {portfolio_id}")
                return True
        return False

    def get_monitoring_statistics(self) -> dict[str, Any]:
        """Get overall monitoring system statistics."""
        total_portfolios = len(self._monitoring_tasks)
        active_monitoring = len([task for task in self._monitoring_tasks.values() if not task.done()])
        total_alerts = sum(len(alerts) for alerts in self._alert_history.values())

        return {
            "total_portfolios_monitored": total_portfolios,
            "active_monitoring_tasks": active_monitoring,
            "total_alerts_generated": total_alerts,
            "monitoring_rules_configured": len(self._monitoring_rules),
            "system_uptime_hours": 0,  # Would track actual uptime
            "last_system_check": datetime.now().isoformat(),
        }
