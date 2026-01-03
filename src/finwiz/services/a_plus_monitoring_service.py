"""
A+ Monitoring Service for integration with FinWiz main application.

This service provides a high-level interface for A+ investment monitoring,
integrating with the portfolio review system and providing monitoring
capabilities for the investment discovery crew results.
"""

from datetime import datetime, timedelta
from typing import Any

from finwiz.schemas.investment_discovery import APlusDiscoveryResult
from finwiz.schemas.portfolio_review import PortfolioReview
from finwiz.tools.logger import get_logger
from finwiz.monitoring.a_plus import get_monitoring_system
from finwiz.infrastructure.monitoring.core import monitor_performance

logger = get_logger(__name__)


class APlusMonitoringService:
    """
    High-level service for A+ investment monitoring integration.

    Provides integration between the A+ monitoring system and the main
    FinWiz application, handling portfolio integration and automated
    monitoring workflows.
    """

    def __init__(self) -> None:
        """Initialize the A+ monitoring service."""
        self.monitoring_system = get_monitoring_system()
        self._service_started = False

        logger.info("A+ Monitoring Service initialized")

    @monitor_performance("a_plus_monitoring_service.start")
    async def start_service(self) -> None:
        """Start the A+ monitoring service."""
        if self._service_started:
            logger.warning("A+ monitoring service already started")
            return

        try:
            await self.monitoring_system.start_monitoring()
            self._service_started = True
            logger.info("A+ monitoring service started successfully")

        except Exception as e:
            logger.error(f"Failed to start A+ monitoring service: {str(e)}")
            raise

    @monitor_performance("a_plus_monitoring_service.stop")
    async def stop_service(self) -> None:
        """Stop the A+ monitoring service."""
        if not self._service_started:
            return

        try:
            await self.monitoring_system.stop_monitoring()
            self._service_started = False
            logger.info("A+ monitoring service stopped")

        except Exception as e:
            logger.error(f"Failed to stop A+ monitoring service: {str(e)}")
            raise

    @monitor_performance("a_plus_monitoring_service.process_discovery_results")
    async def process_discovery_results(self, discovery_result: APlusDiscoveryResult) -> dict[str, Any]:
        """
        Process A+ discovery results and add candidates to monitoring.

        Args:
            discovery_result: Results from investment discovery crew

        Returns:
            Summary of monitoring setup results

        """
        try:
            added_count = 0
            failed_count = 0

            logger.info(f"Processing {len(discovery_result.a_plus_candidates)} A+ candidates for monitoring")

            for analysis in discovery_result.a_plus_candidates:
                try:
                    # Only monitor true A+ candidates
                    if analysis.is_a_plus_candidate and analysis.composite_score >= 0.95:
                        self.monitoring_system.add_investment_to_monitor(
                            symbol=analysis.candidate.symbol,
                            asset_type=analysis.candidate.asset_type,
                            initial_analysis=analysis,
                        )
                        added_count += 1
                        logger.info(f"Added {analysis.candidate.symbol} to A+ monitoring")
                    else:
                        logger.debug(f"Skipped {analysis.candidate.symbol} - not A+ candidate")

                except Exception as e:
                    logger.error(f"Failed to add {analysis.candidate.symbol} to monitoring: {str(e)}")
                    failed_count += 1

            result = {
                "total_candidates": len(discovery_result.a_plus_candidates),
                "added_to_monitoring": added_count,
                "failed_to_add": failed_count,
                "monitoring_active": self._service_started,
                "timestamp": datetime.now().isoformat(),
            }

            logger.info(f"Discovery processing complete: {added_count} added, {failed_count} failed")
            return result

        except Exception as e:
            logger.error(f"Failed to process discovery results: {str(e)}")
            raise

    @monitor_performance("a_plus_monitoring_service.integrate_with_portfolio")
    async def integrate_with_portfolio_review(self, portfolio_review: PortfolioReview) -> dict[str, Any]:
        """
        Integrate A+ monitoring with portfolio review results.

        Args:
            portfolio_review: Portfolio review results

        Returns:
            Integration summary with monitoring recommendations

        """
        try:
            integration_results = {
                "existing_a_plus_holdings": [],
                "degraded_holdings": [],
                "monitoring_recommendations": [],
                "portfolio_monitoring_health": "unknown",
            }

            # Check existing holdings against monitored investments
            monitored_symbols = set(self.monitoring_system.get_active_investments().keys())

            for holding in portfolio_review.holdings:
                symbol = holding.symbol

                # Check if holding is already monitored
                if symbol in monitored_symbols:
                    metrics = self.monitoring_system.monitored_investments[symbol]

                    integration_results["existing_a_plus_holdings"].append(
                        {
                            "symbol": symbol,
                            "current_grade": metrics.current_grade,
                            "current_score": metrics.current_score,
                            "days_monitored": (datetime.now() - metrics.recommendation_date).days,
                            "performance": metrics.total_return,
                        }
                    )

                    # Check for degradation
                    if metrics.current_score < 0.85:  # Below A grade
                        integration_results["degraded_holdings"].append(
                            {
                                "symbol": symbol,
                                "current_grade": metrics.current_grade,
                                "initial_grade": metrics.initial_grade,
                                "score_decline": metrics.initial_score - metrics.current_score,
                            }
                        )

                # Check if high-grade holding should be monitored
                elif holding.grade in ["A+", "A"] and holding.composite_score >= 0.85:
                    integration_results["monitoring_recommendations"].append(
                        {
                            "symbol": symbol,
                            "current_grade": holding.grade,
                            "score": holding.composite_score,
                            "recommendation": "Add to A+ monitoring",
                            "rationale": "High-grade holding should be monitored for degradation",
                        }
                    )

            # Assess overall monitoring health
            total_monitored = len(integration_results["existing_a_plus_holdings"])
            degraded_count = len(integration_results["degraded_holdings"])

            if total_monitored == 0:
                integration_results["portfolio_monitoring_health"] = "no_monitoring"
            elif degraded_count == 0:
                integration_results["portfolio_monitoring_health"] = "healthy"
            elif degraded_count / total_monitored < 0.2:
                integration_results["portfolio_monitoring_health"] = "good"
            elif degraded_count / total_monitored < 0.5:
                integration_results["portfolio_monitoring_health"] = "needs_attention"
            else:
                integration_results["portfolio_monitoring_health"] = "poor"

            logger.info(f"Portfolio integration complete: {total_monitored} monitored, {degraded_count} degraded")
            return integration_results

        except Exception as e:
            logger.error(f"Failed to integrate with portfolio review: {str(e)}")
            raise

    @monitor_performance("a_plus_monitoring_service.get_monitoring_dashboard")
    async def get_monitoring_dashboard(self) -> dict[str, Any]:
        """
        Get comprehensive monitoring dashboard data.

        Returns:
            Dashboard data with monitoring status, alerts, and performance

        """
        try:
            # Get basic performance summary
            performance_summary = self.monitoring_system.get_performance_summary()

            # Get recent alerts
            recent_alerts = self.monitoring_system.get_degradation_alerts(hours_back=24)
            critical_alerts = [alert for alert in recent_alerts if alert.severity.value in ["high", "critical"]]

            # Get investment details
            active_investments = self.monitoring_system.get_active_investments()
            investment_details = []

            for symbol, metrics in active_investments.items():
                investment_details.append(
                    {
                        "symbol": symbol,
                        "asset_type": metrics.asset_type,
                        "current_grade": metrics.current_grade,
                        "current_score": metrics.current_score,
                        "initial_grade": metrics.initial_grade,
                        "score_change": metrics.current_score - metrics.initial_score,
                        "days_monitored": (datetime.now() - metrics.recommendation_date).days,
                        "total_return": metrics.total_return,
                        "alpha": metrics.alpha,
                        "last_evaluation": metrics.last_evaluation.isoformat(),
                        "needs_attention": metrics.current_score < 0.85,
                    }
                )

            # Sort by score change (worst first)
            investment_details.sort(key=lambda x: x["score_change"])

            dashboard = {
                "service_status": {
                    "is_running": self._service_started,
                    "monitoring_active": self.monitoring_system._is_monitoring,
                    "last_updated": datetime.now().isoformat(),
                },
                "performance_summary": performance_summary,
                "alerts": {
                    "total_recent": len(recent_alerts),
                    "critical_count": len(critical_alerts),
                    "recent_alerts": [
                        {
                            "symbol": alert.symbol,
                            "severity": alert.severity.value,
                            "grade_change": f"{alert.previous_grade} → {alert.current_grade}",
                            "score_change": alert.score_change,
                            "timestamp": alert.alert_timestamp.isoformat(),
                        }
                        for alert in recent_alerts[:10]  # Last 10 alerts
                    ],
                },
                "investments": {
                    "total_monitored": len(investment_details),
                    "needs_attention": len([inv for inv in investment_details if inv["needs_attention"]]),
                    "details": investment_details,
                },
                "recommendations": self._generate_dashboard_recommendations(investment_details, critical_alerts),
            }

            return dashboard

        except Exception as e:
            logger.error(f"Failed to generate monitoring dashboard: {str(e)}")
            raise

    @monitor_performance("a_plus_monitoring_service.force_evaluation")
    async def force_evaluation_all(self) -> dict[str, Any]:
        """
        Force immediate evaluation of all monitored investments.

        Returns:
            Evaluation results summary

        """
        try:
            logger.info("Starting forced evaluation of all monitored investments")

            evaluation_results = await self.monitoring_system.evaluate_all_investments(force_evaluation=True)

            # Analyze results
            total_evaluated = len(evaluation_results)
            still_a_plus = sum(1 for analysis in evaluation_results.values() if analysis.is_a_plus_candidate)
            degraded = total_evaluated - still_a_plus

            # Get new alerts generated
            recent_alerts = self.monitoring_system.get_degradation_alerts(hours_back=1)

            result = {
                "evaluation_timestamp": datetime.now().isoformat(),
                "total_evaluated": total_evaluated,
                "still_a_plus": still_a_plus,
                "degraded_count": degraded,
                "new_alerts": len(recent_alerts),
                "evaluation_success_rate": (total_evaluated / len(self.monitoring_system.get_active_investments())) * 100,
                "summary": f"Evaluated {total_evaluated} investments: {still_a_plus} maintained A+, {degraded} degraded",
            }

            logger.info(f"Forced evaluation complete: {result['summary']}")
            return result

        except Exception as e:
            logger.error(f"Failed to force evaluation: {str(e)}")
            raise

    @monitor_performance("a_plus_monitoring_service.cleanup_monitoring")
    async def cleanup_inactive_investments(self, days_inactive: int = 30) -> dict[str, Any]:
        """
        Clean up investments that have been inactive or degraded for too long.

        Args:
            days_inactive: Days after which to consider removing degraded investments

        Returns:
            Cleanup results summary

        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_inactive)
            removed_count = 0
            removed_symbols = []

            active_investments = self.monitoring_system.get_active_investments()

            for symbol, metrics in active_investments.items():
                # Remove if degraded for too long
                if (
                    metrics.current_score < 0.75  # Below B+ grade
                    and metrics.last_evaluation < cutoff_date
                ):
                    self.monitoring_system.remove_investment_from_monitor(symbol, f"Degraded below B+ for {days_inactive} days")
                    removed_count += 1
                    removed_symbols.append(symbol)

            result = {
                "cleanup_timestamp": datetime.now().isoformat(),
                "removed_count": removed_count,
                "removed_symbols": removed_symbols,
                "remaining_monitored": len(self.monitoring_system.get_active_investments()),
                "cleanup_criteria": f"Below B+ grade for {days_inactive} days",
            }

            logger.info(f"Cleanup complete: removed {removed_count} inactive investments")
            return result

        except Exception as e:
            logger.error(f"Failed to cleanup inactive investments: {str(e)}")
            raise

    def _generate_dashboard_recommendations(self, investment_details: list[dict[str, Any]], critical_alerts: list[Any]) -> list[str]:
        """Generate recommendations for the monitoring dashboard."""
        recommendations = []

        # Check for critical alerts
        if critical_alerts:
            recommendations.append(f"🚨 {len(critical_alerts)} critical alerts require immediate attention")

        # Check for degraded investments
        needs_attention = [inv for inv in investment_details if inv["needs_attention"]]
        if needs_attention:
            recommendations.append(f"⚠️ {len(needs_attention)} investments need attention (below A grade)")

        # Check for consistent performers
        strong_performers = [inv for inv in investment_details if inv["score_change"] > 0.05]
        if strong_performers:
            recommendations.append(f"📈 {len(strong_performers)} investments showing improvement")

        # Check monitoring coverage
        if len(investment_details) < 5:
            recommendations.append("💡 Consider adding more A+ investments to monitoring")

        # Default recommendation if all is well
        if not recommendations:
            recommendations.append("✅ All monitored investments are performing well")

        return recommendations


# Global service instance
_monitoring_service: APlusMonitoringService | None = None


def get_monitoring_service() -> APlusMonitoringService:
    """Get the global A+ monitoring service instance."""
    global _monitoring_service
    if _monitoring_service is None:
        _monitoring_service = APlusMonitoringService()
    return _monitoring_service
