"""
Context preparation utilities for the Report Crew.

This module handles preparation of integrated data context for crew execution.
"""

from typing import Any

from finwiz.crews.helpers.data_extraction_helpers import (
    DataAgeExtractor,
    DeepAnalysisExtractor,
    MetricsExtractor,
    TickerValidator,
)
from finwiz.crews.helpers.data_integration_helpers import (
    BacktestingStatusHelper,
    ContextMerger,
    DiscoveryStatusHelper,
)
from finwiz.integration.accessor import CrewDataAccessor
from finwiz.integration.availability import DataAvailabilityTracker
from finwiz.orchestrators.extraction.backtesting import BacktestingDataExtractor
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class ContextPreparationManager:
    """Manages preparation of integrated context for crew execution."""

    def __init__(
        self,
        data_accessor: CrewDataAccessor,
        discovery_accessor: Any,
        backtesting_extractor: BacktestingDataExtractor,
        availability_tracker: DataAvailabilityTracker,
    ) -> None:
        """Initialize context preparation manager."""
        self.data_accessor = data_accessor
        self.discovery_accessor = discovery_accessor
        self.backtesting_extractor = backtesting_extractor
        self.availability_tracker = availability_tracker

    def get_integrated_data_context(self, max_age_hours: int = 24, inputs: dict[str, Any] | None = None) -> dict[str, Any]:
        """Get integrated data context for report generation."""
        try:
            # Clear previous tracking
            self.availability_tracker.clear_tracked_sources()

            # Get consolidated reporter input with all integrated data
            integrated_data = self.data_accessor.get_consolidated_reporter_input(max_age_hours)

            # Extract portfolio_review from consolidated_crew_data to top level
            consolidated_crew_data = integrated_data.get("consolidated_crew_data", {})
            if "portfolio" in consolidated_crew_data:
                integrated_data["portfolio_review"] = consolidated_crew_data["portfolio"]
                logger.info(f"✅ Extracted portfolio_review with {len(integrated_data['portfolio_review'].get('holdings', []))} holdings")
            else:
                logger.warning("❌ No portfolio data found in consolidated_crew_data")
                integrated_data["portfolio_review"] = None

            # Load deep analysis HTML files and extract real grades
            integrated_data["deep_analysis_html_content"] = DeepAnalysisExtractor.load_deep_analysis_html_files()
            logger.info(f"✅ Loaded {len(integrated_data['deep_analysis_html_content'])} deep analysis HTML files")

            # Track crew data availability
            availability_report = self.data_accessor.check_data_availability(max_age_hours)

            # Track stock crew data
            if availability_report.stock_available:
                stock_age = DataAgeExtractor.extract_age_from_summary(availability_report.data_freshness_summary, "stock", max_age_hours)
                self.availability_tracker.track_data_source(
                    source="stock_crew",
                    status="available",
                    age_hours=stock_age,
                    record_count=len(integrated_data.get("stock_analysis_data", [])),
                )
            else:
                self.availability_tracker.track_data_source(source="stock_crew", status="unavailable", error_message="Stock crew data not found")

            # Track ETF crew data
            if availability_report.etf_available:
                etf_age = DataAgeExtractor.extract_age_from_summary(availability_report.data_freshness_summary, "etf", max_age_hours)
                self.availability_tracker.track_data_source(
                    source="etf_crew",
                    status="available",
                    age_hours=etf_age,
                    record_count=len(integrated_data.get("etf_analysis_data", [])),
                )
            else:
                self.availability_tracker.track_data_source(source="etf_crew", status="unavailable", error_message="ETF crew data not found")

            # Track crypto crew data
            if availability_report.crypto_available:
                crypto_age = DataAgeExtractor.extract_age_from_summary(availability_report.data_freshness_summary, "crypto", max_age_hours)
                self.availability_tracker.track_data_source(
                    source="crypto_crew",
                    status="available",
                    age_hours=crypto_age,
                    record_count=len(integrated_data.get("crypto_analysis_data", [])),
                )
            else:
                self.availability_tracker.track_data_source(source="crypto_crew", status="unavailable", error_message="Crypto crew data not found")

            # Track portfolio data
            if availability_report.portfolio_available:
                portfolio_holdings = integrated_data.get("portfolio_review", {}).get("holdings", [])
                portfolio_age = DataAgeExtractor.extract_age_from_summary(availability_report.data_freshness_summary, "portfolio", max_age_hours)
                self.availability_tracker.track_data_source(
                    source="portfolio_review",
                    status="available",
                    age_hours=portfolio_age,
                    record_count=len(portfolio_holdings),
                )

                # Track deep analysis statistics from portfolio holdings
                deep_analysis_count = sum(1 for h in portfolio_holdings if h.get("crew_analysis_used"))
                holdings_with_alternatives = sum(1 for h in portfolio_holdings if h.get("alternatives"))

                if deep_analysis_count > 0:
                    self.availability_tracker.track_data_source(
                        source="deep_portfolio_analysis",
                        status="available",
                        record_count=deep_analysis_count,
                    )
                    logger.info(f"Deep portfolio analysis available for {deep_analysis_count} holdings")

                    # Add deep analysis summary to integrated data
                    integrated_data["deep_analysis_summary"] = {
                        "total_holdings": len(portfolio_holdings),
                        "deep_analysis_count": deep_analysis_count,
                        "shallow_analysis_count": len(portfolio_holdings) - deep_analysis_count,
                        "holdings_with_alternatives": holdings_with_alternatives,
                        "deep_analysis_percentage": (deep_analysis_count / len(portfolio_holdings) * 100) if portfolio_holdings else 0,
                    }
                else:
                    self.availability_tracker.track_data_source(
                        source="deep_portfolio_analysis",
                        status="unavailable",
                        error_message="No deep analysis performed on portfolio holdings",
                    )
                    integrated_data["deep_analysis_summary"] = None
            else:
                self.availability_tracker.track_data_source(source="portfolio_review", status="unavailable", error_message="Portfolio review data not found")

            # Add data availability information
            integrated_data["data_availability_report"] = availability_report.model_dump(mode="json")

            # Add stale data warnings
            integrated_data["stale_data_warnings"] = self.data_accessor.get_stale_data_warnings(max_age_hours)

            # Add A+ discovery data with proper status handling
            discovery_helper = DiscoveryStatusHelper(self.discovery_accessor)
            discovery_status = discovery_helper.get_discovery_status(inputs)
            integrated_data["discovery_status"] = discovery_status

            if discovery_status["has_results"]:
                # Try to get discovery results from Flow state inputs
                discovery_results = None
                if inputs:
                    if inputs.get("aplus_opportunities"):
                        discovery_results = inputs["aplus_opportunities"]
                        logger.info("Using discovery results from Flow state (aplus_opportunities)")
                    elif inputs.get("investment_discovery_structured"):
                        discovery_results = inputs["investment_discovery_structured"]
                        logger.info("Using discovery results from Flow state (investment_discovery_structured)")

                # Fall back to file-based loading if not in inputs
                if not discovery_results:
                    discovery_results = self.discovery_accessor.load_discovery_results()
                    if discovery_results:
                        logger.info("Loaded discovery results from files")

                if discovery_results:
                    integrated_data["aplus_discovery_results"] = discovery_results

                    # Generate summary from results
                    if hasattr(self.discovery_accessor, "get_opportunities_summary"):
                        integrated_data["aplus_opportunities_summary"] = self.discovery_accessor.get_opportunities_summary()
                    else:
                        # Generate basic summary from results
                        total_opportunities = 0
                        if isinstance(discovery_results, dict):
                            for key in ["stocks", "etfs", "crypto"]:
                                if key in discovery_results:
                                    candidates = discovery_results[key].get("a_plus_candidates", [])
                                    total_opportunities += len(candidates)
                        integrated_data["aplus_opportunities_summary"] = f"{total_opportunities} A+ opportunities found"

                    # Track discovery data as available
                    self.availability_tracker.track_data_source(
                        source="aplus_discovery",
                        status="available",
                        record_count=total_opportunities if "total_opportunities" in locals() else 0,
                    )

                    logger.info("Discovery results available with opportunities")
                else:
                    integrated_data["aplus_discovery_results"] = None
                    integrated_data["aplus_opportunities_summary"] = "No A+ opportunities found in current analysis"

                    # Track discovery as available but with no opportunities
                    self.availability_tracker.track_data_source(source="aplus_discovery", status="available", record_count=0)

                    logger.info("Discovery results exist but no opportunities found")
            else:
                integrated_data["aplus_discovery_results"] = None
                integrated_data["aplus_opportunities_summary"] = discovery_status["message"]

                # Track discovery as unavailable
                self.availability_tracker.track_data_source(source="aplus_discovery", status="unavailable", error_message=discovery_status["message"])

                logger.info(f"A+ discovery not available: {discovery_status['message']}")

            # Add backtesting data with proper status handling
            backtesting_helper = BacktestingStatusHelper(self.discovery_accessor, self.backtesting_extractor)
            backtesting_status_result = backtesting_helper.get_backtesting_status(inputs)

            # Extract backtesting data if available
            backtesting_data = self._extract_backtesting_data_from_results(backtesting_status_result)
            integrated_data["backtesting_status"] = {
                "has_data": backtesting_data["has_backtesting_data"],
                "message": backtesting_data["message"],
                "status": backtesting_data["status"],
            }

            if backtesting_data["has_backtesting_data"]:
                integrated_data["backtesting_data"] = backtesting_data["backtesting_by_candidate"]
                integrated_data["backtesting_summary"] = backtesting_data.get("summary")

                # Track backtesting data as available
                self.availability_tracker.track_data_source(source="backtesting", status="available", record_count=backtesting_data.get("total_candidates", 0))

                logger.info(f"Loaded backtesting data for {backtesting_data['total_candidates']} candidates")
            else:
                integrated_data["backtesting_data"] = None
                integrated_data["backtesting_summary"] = None

                # Track backtesting as unavailable
                self.availability_tracker.track_data_source(source="backtesting", status="unavailable", error_message=backtesting_data["message"])

                logger.info(f"Backtesting data not available: {backtesting_data['message']}")

            # Generate data availability summary
            availability_summary = self.availability_tracker.get_availability_summary()
            integrated_data["data_availability_summary"] = availability_summary.model_dump(mode="json")
            integrated_data["data_availability_summary_formatted"] = self.availability_tracker.format_summary_for_report(availability_summary)

            logger.info(
                "Integrated data context prepared for report generation",
                extra={
                    "total_sources": availability_summary.total_sources,
                    "available_sources": availability_summary.available_sources,
                    "unavailable_sources": availability_summary.unavailable_sources,
                    "stale_sources": availability_summary.stale_sources,
                },
            )

            return integrated_data

        except Exception as e:
            logger.error(f"Failed to get integrated data context: {e!s}", exc_info=True)

            # Track error in availability tracker
            self.availability_tracker.track_data_source(source="data_integration", status="unavailable", error_message=f"Data integration failed: {e!s}")

            # Generate error summary
            error_summary = self.availability_tracker.get_availability_summary()

            return {
                "error": f"Data integration failed: {e!s}",
                "fallback_mode": True,
                "data_availability_report": None,
                "stale_data_warnings": [f"Data integration error: {e!s}"],
                "discovery_status": {"has_results": False, "message": f"Discovery data unavailable due to error: {e!s}"},
                "data_availability_summary": error_summary.model_dump(mode="json"),
                "data_availability_summary_formatted": self.availability_tracker.format_summary_for_report(error_summary),
            }

    def _extract_backtesting_data_from_results(self, backtesting_status_result: dict[str, Any]) -> dict[str, Any]:
        """Extract backtesting data from backtesting status result."""
        try:
            # Check if backtesting data is available
            if not backtesting_status_result.get("has_backtesting_data"):
                return backtesting_status_result

            # Extract validation results from discovery data
            validation_results = backtesting_status_result.get("validation_results", [])

            # Extract backtesting metrics for each candidate
            backtesting_by_candidate = {}
            all_metrics = []

            for vr_data in validation_results:
                try:
                    # Work directly with dict data
                    symbol = vr_data.get("symbol", "UNKNOWN")

                    # Extract annualized return from validation details if not in top level
                    annualized_return = self._safe_get_metric(vr_data, "annualized_return")
                    if annualized_return is None:
                        validation_details = vr_data.get("validation_details", [])
                        if validation_details:
                            returns = [d.get("annualized_return") for d in validation_details if d.get("annualized_return") is not None]
                            if returns:
                                annualized_return = sum(returns) / len(returns)

                    # Extract win rate from validation details if not in top level
                    win_rate = self._safe_get_metric(vr_data, "win_rate")
                    if win_rate is None:
                        validation_details = vr_data.get("validation_details", [])
                        if validation_details:
                            rates = [d.get("win_rate") for d in validation_details if d.get("win_rate") is not None]
                            if rates:
                                win_rate = sum(rates) / len(rates)

                    # Extract metrics directly from the dict
                    metrics_dict = {
                        "annualized_return": annualized_return,
                        "sharpe_ratio": MetricsExtractor.safe_get_metric(vr_data, "average_sharpe_ratio"),
                        "sortino_ratio": MetricsExtractor.safe_get_metric(vr_data, "average_sortino_ratio"),
                        "calmar_ratio": MetricsExtractor.calculate_calmar_from_dict(vr_data),
                        "max_drawdown": MetricsExtractor.safe_get_metric(vr_data, "average_max_drawdown"),
                        "win_rate": win_rate,
                        "backtest_period_years": vr_data.get("backtest_period_years"),
                        "total_trades": MetricsExtractor.extract_total_trades_from_dict(vr_data),
                    }

                    # Create BacktestingMetrics from the extracted data
                    from finwiz.orchestrators.extraction.backtesting import BacktestingMetrics

                    metrics = BacktestingMetrics(**metrics_dict)

                    if metrics:
                        backtesting_by_candidate[symbol] = {
                            "metrics": metrics.model_dump(mode="json"),
                            "formatted_display": self.backtesting_extractor.format_for_display(metrics),
                            "available_metrics": self.backtesting_extractor.get_available_metrics(metrics),
                        }
                        all_metrics.append(metrics)
                        logger.info(f"Extracted backtesting metrics for {symbol}")
                except Exception as e:
                    logger.error(f"Failed to extract backtesting metrics for validation result: {e}")
                    continue

            # Generate summary if we have metrics
            summary = None
            if all_metrics:
                summary_data = {
                    "total_candidates_tested": len(all_metrics),
                    "candidates_with_data": len([m for m in all_metrics if m.annualized_return is not None]),
                    "average_annualized_return": sum(m.annualized_return for m in all_metrics if m.annualized_return is not None)
                    / len([m for m in all_metrics if m.annualized_return is not None])
                    if any(m.annualized_return is not None for m in all_metrics)
                    else None,
                    "average_sharpe_ratio": sum(m.sharpe_ratio for m in all_metrics if m.sharpe_ratio is not None) / len([m for m in all_metrics if m.sharpe_ratio is not None])
                    if any(m.sharpe_ratio is not None for m in all_metrics)
                    else None,
                    "average_max_drawdown": sum(m.max_drawdown for m in all_metrics if m.max_drawdown is not None) / len([m for m in all_metrics if m.max_drawdown is not None])
                    if any(m.max_drawdown is not None for m in all_metrics)
                    else None,
                }

            if backtesting_by_candidate:
                logger.info(f"Successfully extracted backtesting data for {len(backtesting_by_candidate)} candidates")
                return {
                    "has_backtesting_data": True,
                    "message": f"Backtesting data available for {len(backtesting_by_candidate)} candidates",
                    "status": "available",
                    "backtesting_by_candidate": backtesting_by_candidate,
                    "summary": summary_data if summary else None,
                    "total_candidates": len(backtesting_by_candidate),
                }
            else:
                logger.warning("No backtesting metrics could be extracted from validation results")
                return {
                    "has_backtesting_data": False,
                    "message": "Backtesting data not available - metrics could not be extracted",
                    "status": "not_available",
                }

        except Exception as e:
            logger.error(f"Failed to extract backtesting data: {e}", exc_info=True)
            return {"has_backtesting_data": False, "message": f"Backtesting data extraction failed: {e!s}", "status": "error"}

    @staticmethod
    def _safe_get_metric(data: dict[str, Any], key: str) -> Any:
        """Safely get a metric from data dictionary."""
        try:
            value = data.get(key)
            if value is not None and isinstance(value, (int, float)):
                return float(value)
            return None
        except (TypeError, ValueError):
            return None

    def prepare_crew_context(self, max_age_hours: int = 24, inputs: dict[str, Any] | None = None) -> dict[str, Any]:
        """Prepare integrated context for crew execution."""
        try:
            # Get integrated data context, passing inputs to check Flow state first
            integrated_context = self.get_integrated_data_context(max_age_hours, inputs)

            # Merge original Flow state inputs to preserve template variables
            integrated_context = ContextMerger.merge_flow_state_inputs(integrated_context, inputs)

            # Extract and validate tickers to prevent hallucination
            validated_tickers = TickerValidator.extract_validated_tickers(integrated_context)

            if not validated_tickers or len(validated_tickers) < 3:
                error_msg = (
                    f"Insufficient validated tickers for full report generation. "
                    f"Found {len(validated_tickers)} ticker(s): {validated_tickers}. "
                    f"Recommended: at least 3 validated tickers for a diversified portfolio report. "
                    f"Will generate limited report with available data to prevent hallucination."
                )
                logger.warning(error_msg)

                # Add warning to context instead of failing completely
                integrated_context["ticker_validation_warning"] = error_msg
                integrated_context["insufficient_tickers"] = True
            else:
                integrated_context["insufficient_tickers"] = False

            # Add validated tickers to context for agents to use
            integrated_context["validated_tickers_list"] = validated_tickers
            integrated_context["ticker_count"] = len(validated_tickers)

            logger.info(f"Validated {len(validated_tickers)} tickers for report generation", extra={"validated_tickers": validated_tickers})

            # Add execution metadata
            integrated_context["execution_metadata"] = {
                "max_age_hours": max_age_hours,
                "integration_manager_initialized": True,
                "data_accessor_initialized": True,
                "tools_count": 0,
                "validated_ticker_count": len(validated_tickers),
            }

            logger.info("Crew context prepared with integrated data and validated tickers")
            return integrated_context

        except Exception as e:
            logger.error(f"Failed to prepare crew context: {e!s}", exc_info=True)
            # Return minimal context for graceful degradation
            return {
                "error": f"Context preparation failed: {e!s}",
                "fallback_mode": True,
                "execution_metadata": {
                    "max_age_hours": max_age_hours,
                    "integration_manager_initialized": False,
                    "data_accessor_initialized": False,
                    "tools_count": 0,
                },
            }
