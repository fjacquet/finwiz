"""
Portfolio monitoring system for continuous drift monitoring and alerting.

This module provides real-time portfolio monitoring capabilities, including
drift detection, alert generation, and automated rebalancing triggers.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from finwiz.quantitative.monitoring_alerts import (
    AlertManager,
    AlertSeverity,
    AlertType,
    PortfolioAlert,
)
from finwiz.quantitative.monitoring_engine import MonitoringEngine
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


# Re-export for backward compatibility
__all__ = [
    "AlertSeverity",
    "AlertType",
    "MonitoringRule",
    "MonitoringStatus",
    "PortfolioAlert",
    "PortfolioHealthDashboard",
    "PortfolioMonitor",
]


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
        # Initialize components
        self.monitoring_engine = MonitoringEngine(price_service, portfolio_analyzer, rebalancing_engine)
        self.alert_manager = AlertManager()

        # Internal state
        self._monitoring_tasks: dict[str, asyncio.Task] = {}
        self._monitoring_rules: dict[str, MonitoringRule] = {}

        logger.info("Portfolio monitor initialized")

    async def start_monitoring(self, portfolio_id: str, portfolio_config: PortfolioConfiguration, monitoring_rule: MonitoringRule | None = None) -> None:
        """Start monitoring a portfolio for drift and rebalancing needs."""
        try:
            # Use default rule if none provided
            if monitoring_rule is None:
                monitoring_rule = MonitoringRule(rule_id=f"default_{portfolio_id}", rule_name=f"Default monitoring for {portfolio_id}")

            # Store monitoring configuration
            self._monitoring_rules[portfolio_id] = monitoring_rule

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

        except Exception as e:
            logger.error(f"Failed to stop monitoring for portfolio {portfolio_id}: {e}")
            raise

    async def check_portfolio_drift(self, portfolio_id: str, portfolio_config: PortfolioConfiguration) -> list[RebalancingNeed]:
        """Check current portfolio drift against targets."""
        return await self.monitoring_engine.check_portfolio_drift(portfolio_id, portfolio_config)

    async def generate_health_dashboard(self, portfolio_id: str, portfolio_config: PortfolioConfiguration) -> PortfolioHealthDashboard:
        """Generate comprehensive portfolio health dashboard."""
        try:
            # Check current drift
            rebalancing_needs = await self.check_portfolio_drift(portfolio_id, portfolio_config)

            # Calculate health metrics
            positions_needing_attention = [need for need in rebalancing_needs if need.needs_rebalancing]
            max_deviation = max([abs(need.deviation) for need in rebalancing_needs], default=0.0)
            avg_deviation = sum([abs(need.deviation) for need in rebalancing_needs]) / len(rebalancing_needs) if rebalancing_needs else 0.0

            # Determine overall health score (1-10 scale)
            health_score = self.monitoring_engine._calculate_health_score(rebalancing_needs, portfolio_config)

            # Determine rebalancing urgency
            urgency = self.monitoring_engine._determine_rebalancing_urgency(positions_needing_attention, max_deviation)

            # Get monitoring status
            monitoring_status = self._get_monitoring_status(portfolio_id)

            # Get recent alerts
            recent_alerts = self.alert_manager._get_recent_alerts(portfolio_id, hours=24)

            # Estimate rebalancing cost if needed
            estimated_cost = 0.0
            if positions_needing_attention:
                # This would typically call the rebalancing engine to estimate costs
                estimated_cost = len(positions_needing_attention) * 10.0  # Simplified estimate

            return PortfolioHealthDashboard(
                portfolio_id=portfolio_id,
                overall_health_score=health_score,
                health_status=self.monitoring_engine._get_health_status_description(health_score),
                max_deviation=max_deviation,
                avg_deviation=avg_deviation,
                positions_needing_attention=positions_needing_attention,
                rebalancing_urgency=urgency,
                estimated_rebalancing_cost=estimated_cost,
                days_since_last_rebalance=self.monitoring_engine._get_days_since_last_rebalance(portfolio_id),
                monitoring_status=monitoring_status,
                recent_alerts=recent_alerts,
            )

        except Exception as e:
            logger.error(f"Failed to generate health dashboard for {portfolio_id}: {e}")
            raise

    async def _monitor_portfolio_loop(self, portfolio_id: str, portfolio_config: PortfolioConfiguration, monitoring_rule: MonitoringRule) -> None:
        """Run main monitoring loop for a portfolio."""
        logger.info(f"Starting monitoring loop for portfolio {portfolio_id}")

        try:
            while monitoring_rule.enabled:
                try:
                    # Check if enough time has passed since last check
                    last_check = self.monitoring_engine.get_last_check_time(portfolio_id)
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
                    await self.alert_manager.generate_error_alert(portfolio_id, str(e))
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
            positions_out_of_tolerance = [need for need in rebalancing_needs if need.needs_rebalancing]
            max_deviation = max([abs(need.deviation) for need in rebalancing_needs], default=0.0)

            # Check deviation threshold rule
            if monitoring_rule.alert_on_deviation and max_deviation > monitoring_rule.max_deviation_threshold:
                await self.alert_manager.generate_deviation_alert(portfolio_id, positions_out_of_tolerance, max_deviation, monitoring_rule.max_deviation_threshold)

            # Check multiple positions rule
            if monitoring_rule.alert_on_multiple_positions and len(positions_out_of_tolerance) >= monitoring_rule.min_positions_for_alert:
                await self.alert_manager.generate_multiple_positions_alert(portfolio_id, positions_out_of_tolerance)

            # Check auto-rebalancing rule
            if monitoring_rule.enable_auto_rebalancing and max_deviation > monitoring_rule.auto_rebalance_threshold:
                await self.alert_manager.generate_auto_rebalance_alert(portfolio_id, positions_out_of_tolerance)

        except Exception as e:
            logger.error(f"Error processing monitoring rules for {portfolio_id}: {e}")
            raise

    def _get_monitoring_status(self, portfolio_id: str) -> MonitoringStatus:
        """Get current monitoring status for a portfolio."""
        rule = self._monitoring_rules.get(portfolio_id)
        last_check = self.monitoring_engine.get_last_check_time(portfolio_id) or datetime.now()

        # Calculate next check time
        next_check = last_check + timedelta(hours=rule.min_check_interval_hours if rule else 1)

        # Get alert counts
        active_alerts, unacknowledged_alerts, last_alert_timestamp = self.alert_manager._get_monitoring_status_alerts(portfolio_id)

        return MonitoringStatus(
            portfolio_id=portfolio_id,
            last_check_timestamp=last_check,
            next_check_timestamp=next_check,
            monitoring_active=portfolio_id in self._monitoring_tasks,
            positions_monitored=0,  # Would be calculated from actual portfolio
            positions_out_of_tolerance=0,  # Would be calculated from latest check
            active_alerts=active_alerts,
            unacknowledged_alerts=unacknowledged_alerts,
            last_alert_timestamp=last_alert_timestamp,
            price_data_freshness_minutes=5,  # Would be calculated from price service
            monitoring_health_score=8.5,  # Would be calculated based on system health
        )

    async def get_active_alerts(self, portfolio_id: str) -> list[PortfolioAlert]:
        """Get all active (unresolved) alerts for a portfolio."""
        return await self.alert_manager.get_active_alerts(portfolio_id)

    async def acknowledge_alert(self, portfolio_id: str, alert_id: str) -> bool:
        """Acknowledge an alert."""
        return await self.alert_manager.acknowledge_alert(portfolio_id, alert_id)

    async def resolve_alert(self, portfolio_id: str, alert_id: str, resolution_notes: str = "") -> bool:
        """Resolve an alert."""
        return await self.alert_manager.resolve_alert(portfolio_id, alert_id, resolution_notes)

    def get_monitoring_statistics(self) -> dict[str, Any]:
        """Get overall monitoring system statistics."""
        total_portfolios = len(self._monitoring_tasks)
        active_monitoring = len([task for task in self._monitoring_tasks.values() if not task.done()])

        engine_stats = self.monitoring_engine.get_monitoring_statistics()
        alert_stats = self.alert_manager.get_alert_statistics()

        return {
            "total_portfolios_monitored": total_portfolios,
            "active_monitoring_tasks": active_monitoring,
            "total_alerts_generated": alert_stats["total_alerts_generated"],
            "total_active_alerts": alert_stats["total_active_alerts"],
            "monitoring_rules_configured": len(self._monitoring_rules),
            "system_uptime_hours": 0,  # Would track actual uptime
            "last_system_check": datetime.now().isoformat(),
        }
