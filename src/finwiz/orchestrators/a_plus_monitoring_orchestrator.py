"""
A+ Monitoring Orchestrator for integration with FinWiz main flow.

This orchestrator integrates A+ monitoring with the main FinWiz workflow,
handling automatic monitoring setup after investment discovery and
providing monitoring status in portfolio reports.
"""

from datetime import datetime
from typing import Any

from finwiz.schemas.investment_discovery import APlusDiscoveryResult
from finwiz.schemas.portfolio_review import PortfolioReview
from finwiz.services.a_plus_monitoring_service import get_monitoring_service
from finwiz.tools.logger import get_logger
from finwiz.utils.monitoring import monitor_performance

logger = get_logger(__name__)


class APlusMonitoringOrchestrator:
    """
    Orchestrator for A+ monitoring integration with FinWiz workflows.

    Handles the integration of A+ monitoring with portfolio reviews,
    investment discovery results, and reporting workflows.
    """

    def __init__(self) -> None:
        """Initialize the A+ monitoring orchestrator."""
        self.monitoring_service = get_monitoring_service()
        logger.info("A+ Monitoring Orchestrator initialized")

    @monitor_performance("a_plus_monitoring_orchestrator.initialize")
    async def initialize_monitoring(self) -> dict[str, Any]:
        """
        Initialize the A+ monitoring system.

        Returns:
            Initialization status and configuration

        """
        try:
            await self.monitoring_service.start_service()

            result = {
                "status": "initialized",
                "timestamp": datetime.now().isoformat(),
                "monitoring_active": True,
                "message": "A+ monitoring system initialized successfully",
            }

            logger.info("A+ monitoring system initialized")
            return result

        except Exception as e:
            logger.error(f"Failed to initialize A+ monitoring: {str(e)}")
            return {
                "status": "failed",
                "timestamp": datetime.now().isoformat(),
                "monitoring_active": False,
                "error": str(e),
                "message": "Failed to initialize A+ monitoring system",
            }

    @monitor_performance("a_plus_monitoring_orchestrator.process_discovery")
    async def process_discovery_results(self, discovery_result: APlusDiscoveryResult) -> dict[str, Any]:
        """
        Process investment discovery results and set up monitoring.

        Args:
            discovery_result: Results from investment discovery crew

        Returns:
            Processing results and monitoring setup status

        """
        try:
            logger.info(f"Processing discovery results for {discovery_result.asset_type} investments")

            # Process discovery results
            processing_result = await self.monitoring_service.process_discovery_results(discovery_result)

            # Get updated monitoring status
            dashboard = await self.monitoring_service.get_monitoring_dashboard()

            result = {
                "processing_status": "success",
                "discovery_processing": processing_result,
                "monitoring_summary": {
                    "total_monitored": dashboard["performance_summary"]["total_investments"],
                    "a_plus_count": dashboard["performance_summary"]["a_plus_count"],
                    "monitoring_health": dashboard["performance_summary"]["monitoring_health"],
                },
                "recommendations": dashboard["recommendations"],
                "timestamp": datetime.now().isoformat(),
            }

            logger.info(
                f"Discovery processing complete: {processing_result['added_to_monitoring']} investments added to monitoring"
            )
            return result

        except Exception as e:
            logger.error(f"Failed to process discovery results: {str(e)}")
            return {
                "processing_status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    @monitor_performance("a_plus_monitoring_orchestrator.enhance_portfolio_review")
    async def enhance_portfolio_review(self, portfolio_review: PortfolioReview) -> dict[str, Any]:
        """
        Enhance portfolio review with A+ monitoring insights.

        Args:
            portfolio_review: Portfolio review results

        Returns:
            Enhanced portfolio review with monitoring insights

        """
        try:
            logger.info("Enhancing portfolio review with A+ monitoring insights")

            # Integrate with portfolio review
            integration_result = await self.monitoring_service.integrate_with_portfolio_review(portfolio_review)

            # Get current monitoring dashboard
            dashboard = await self.monitoring_service.get_monitoring_dashboard()

            # Create enhanced review data
            enhanced_review = {
                "original_portfolio": {
                    "portfolio_id": portfolio_review.portfolio_id,
                    "total_value": portfolio_review.total_value,
                    "portfolio_grade": portfolio_review.portfolio_grade,
                    "average_score": portfolio_review.average_score,
                    "holdings_count": len(portfolio_review.holdings),
                },
                "monitoring_integration": integration_result,
                "monitoring_status": {
                    "service_active": dashboard["service_status"]["is_running"],
                    "total_monitored": dashboard["performance_summary"]["total_investments"],
                    "monitoring_health": dashboard["performance_summary"]["monitoring_health"],
                    "recent_alerts": dashboard["alerts"]["total_recent"],
                    "critical_alerts": dashboard["alerts"]["critical_count"],
                },
                "a_plus_insights": {
                    "monitored_holdings": len(integration_result["existing_a_plus_holdings"]),
                    "degraded_holdings": len(integration_result["degraded_holdings"]),
                    "monitoring_recommendations": len(integration_result["monitoring_recommendations"]),
                    "portfolio_monitoring_health": integration_result["portfolio_monitoring_health"],
                },
                "recommendations": self._generate_portfolio_recommendations(integration_result, dashboard),
                "timestamp": datetime.now().isoformat(),
            }

            logger.info("Portfolio review enhanced with A+ monitoring insights")
            return enhanced_review

        except Exception as e:
            logger.error(f"Failed to enhance portfolio review: {str(e)}")
            return {
                "enhancement_status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    @monitor_performance("a_plus_monitoring_orchestrator.get_monitoring_report")
    async def get_monitoring_report(self) -> dict[str, Any]:
        """
        Generate comprehensive A+ monitoring report.

        Returns:
            Comprehensive monitoring report

        """
        try:
            logger.info("Generating A+ monitoring report")

            # Get dashboard data
            dashboard = await self.monitoring_service.get_monitoring_dashboard()

            # Generate report sections
            report = {
                "report_metadata": {
                    "report_type": "a_plus_monitoring",
                    "generated_at": datetime.now().isoformat(),
                    "report_period": "current_status",
                },
                "executive_summary": self._generate_executive_summary(dashboard),
                "service_status": dashboard["service_status"],
                "performance_overview": dashboard["performance_summary"],
                "alert_summary": dashboard["alerts"],
                "investment_details": dashboard["investments"],
                "recommendations": dashboard["recommendations"],
                "health_assessment": self._assess_monitoring_health(dashboard),
                "next_actions": self._generate_next_actions(dashboard),
            }

            logger.info("A+ monitoring report generated successfully")
            return report

        except Exception as e:
            logger.error(f"Failed to generate monitoring report: {str(e)}")
            return {
                "report_status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    @monitor_performance("a_plus_monitoring_orchestrator.handle_alerts")
    async def handle_monitoring_alerts(self) -> dict[str, Any]:
        """
        Handle and process monitoring alerts.

        Returns:
            Alert handling results and actions taken

        """
        try:
            logger.info("Processing monitoring alerts")

            # Get dashboard to check alerts
            dashboard = await self.monitoring_service.get_monitoring_dashboard()
            alerts = dashboard["alerts"]

            # Process critical alerts
            critical_alerts = [alert for alert in alerts["recent_alerts"] if alert["severity"] in ["high", "critical"]]

            actions_taken = []

            if critical_alerts:
                # Force evaluation of critical investments
                critical_symbols = [alert["symbol"] for alert in critical_alerts]
                logger.warning(f"Processing {len(critical_alerts)} critical alerts for symbols: {critical_symbols}")

                # Could trigger additional actions here:
                # - Send notifications
                # - Generate replacement recommendations
                # - Update portfolio recommendations

                actions_taken.append(f"Identified {len(critical_alerts)} critical alerts requiring attention")
                actions_taken.append("Recommended immediate review of degraded investments")

            result = {
                "alert_processing_status": "completed",
                "total_alerts": alerts["total_recent"],
                "critical_alerts": len(critical_alerts),
                "actions_taken": actions_taken,
                "critical_symbols": [alert["symbol"] for alert in critical_alerts],
                "recommendations": [
                    "Review degraded investments immediately",
                    "Consider replacement candidates",
                    "Update portfolio allocation if needed",
                ]
                if critical_alerts
                else ["No critical alerts - monitoring healthy"],
                "timestamp": datetime.now().isoformat(),
            }

            logger.info(f"Alert processing complete: {len(critical_alerts)} critical alerts handled")
            return result

        except Exception as e:
            logger.error(f"Failed to handle monitoring alerts: {str(e)}")
            return {
                "alert_processing_status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def shutdown_monitoring(self) -> dict[str, Any]:
        """
        Shutdown the A+ monitoring system.

        Returns:
            Shutdown status

        """
        try:
            await self.monitoring_service.stop_service()

            result = {
                "status": "shutdown",
                "timestamp": datetime.now().isoformat(),
                "message": "A+ monitoring system shutdown successfully",
            }

            logger.info("A+ monitoring system shutdown")
            return result

        except Exception as e:
            logger.error(f"Failed to shutdown A+ monitoring: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def _generate_portfolio_recommendations(self, integration_result: dict[str, Any], dashboard: dict[str, Any]) -> list[str]:
        """Generate portfolio-specific recommendations."""
        recommendations = []

        # Check for degraded holdings
        degraded_holdings = integration_result["degraded_holdings"]
        if degraded_holdings:
            recommendations.append(f"🚨 Review {len(degraded_holdings)} degraded A+ holdings immediately")
            for holding in degraded_holdings[:3]:  # Top 3
                recommendations.append(f"   • {holding['symbol']}: {holding['initial_grade']} → {holding['current_grade']}")

        # Check for monitoring recommendations
        monitoring_recs = integration_result["monitoring_recommendations"]
        if monitoring_recs:
            recommendations.append(f"💡 Consider adding {len(monitoring_recs)} high-grade holdings to monitoring")

        # Check overall health
        health = integration_result["portfolio_monitoring_health"]
        if health == "poor":
            recommendations.append("⚠️ Portfolio monitoring health is poor - consider comprehensive review")
        elif health == "needs_attention":
            recommendations.append("📊 Portfolio monitoring needs attention - review degraded positions")
        elif health == "healthy":
            recommendations.append("✅ Portfolio monitoring is healthy - maintain current approach")

        return recommendations

    def _generate_executive_summary(self, dashboard: dict[str, Any]) -> dict[str, Any]:
        """Generate executive summary for monitoring report."""
        perf_summary = dashboard["performance_summary"]
        alerts = dashboard["alerts"]

        # Determine overall status
        if alerts["critical_count"] > 0:
            overall_status = "critical"
            status_message = f"{alerts['critical_count']} investments require immediate attention"
        elif perf_summary["degraded_count"] > 0:
            overall_status = "needs_attention"
            status_message = f"{perf_summary['degraded_count']} investments have degraded below A grade"
        else:
            overall_status = "healthy"
            status_message = "All monitored investments maintaining high grades"

        return {
            "overall_status": overall_status,
            "status_message": status_message,
            "key_metrics": {
                "total_monitored": perf_summary["total_investments"],
                "a_plus_maintained": perf_summary["a_plus_count"],
                "a_plus_percentage": perf_summary.get("a_plus_percentage", 0),
                "recent_alerts": alerts["total_recent"],
            },
            "health_indicator": perf_summary.get("monitoring_health", "unknown"),
        }

    def _assess_monitoring_health(self, dashboard: dict[str, Any]) -> dict[str, Any]:
        """Assess overall monitoring system health."""
        perf_summary = dashboard["performance_summary"]
        alerts = dashboard["alerts"]
        service_status = dashboard["service_status"]

        health_score = 100
        health_factors = []

        # Service health
        if not service_status["is_running"]:
            health_score -= 50
            health_factors.append("Service not running")

        # Alert health
        if alerts["critical_count"] > 0:
            health_score -= 30
            health_factors.append(f"{alerts['critical_count']} critical alerts")
        elif alerts["total_recent"] > 5:
            health_score -= 15
            health_factors.append("High alert volume")

        # Performance health
        if perf_summary["total_investments"] > 0:
            degraded_percentage = (perf_summary["degraded_count"] / perf_summary["total_investments"]) * 100
            if degraded_percentage > 50:
                health_score -= 25
                health_factors.append("High degradation rate")
            elif degraded_percentage > 25:
                health_score -= 10
                health_factors.append("Moderate degradation rate")

        # Determine health level
        if health_score >= 90:
            health_level = "excellent"
        elif health_score >= 75:
            health_level = "good"
        elif health_score >= 60:
            health_level = "fair"
        elif health_score >= 40:
            health_level = "poor"
        else:
            health_level = "critical"

        return {
            "health_score": health_score,
            "health_level": health_level,
            "health_factors": health_factors,
            "assessment_timestamp": datetime.now().isoformat(),
        }

    def _generate_next_actions(self, dashboard: dict[str, Any]) -> list[str]:
        """Generate recommended next actions."""
        actions = []

        alerts = dashboard["alerts"]
        perf_summary = dashboard["performance_summary"]

        # Critical actions
        if alerts["critical_count"] > 0:
            actions.append("🚨 Address critical alerts immediately")
            actions.append("📋 Review degraded investment fundamentals")
            actions.append("🔄 Consider replacement candidates")

        # Maintenance actions
        if perf_summary["total_investments"] > 10:
            actions.append("🧹 Consider cleanup of inactive investments")

        if perf_summary["total_investments"] < 5:
            actions.append("📈 Consider adding more A+ investments to monitoring")

        # Regular actions
        actions.append("📊 Schedule weekly monitoring review")
        actions.append("🔍 Monitor market regime changes")

        return actions[:5]  # Limit to top 5 actions


# Global orchestrator instance
_monitoring_orchestrator: APlusMonitoringOrchestrator | None = None


def get_monitoring_orchestrator() -> APlusMonitoringOrchestrator:
    """Get the global A+ monitoring orchestrator instance."""
    global _monitoring_orchestrator
    if _monitoring_orchestrator is None:
        _monitoring_orchestrator = APlusMonitoringOrchestrator()
    return _monitoring_orchestrator
