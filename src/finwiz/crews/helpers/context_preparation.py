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


# ---------------------------------------------------------------------------
# Module-level loader functions (functional core / imperative shell pattern)
# ---------------------------------------------------------------------------


def _load_reporter_input(data_accessor: CrewDataAccessor, max_age_hours: int) -> dict[str, Any]:
    """Load consolidated reporter input and extract top-level keys.

    Fetches the consolidated reporter input, promotes portfolio_review to top
    level, and loads deep-analysis HTML files.
    """
    integrated_data = data_accessor.get_consolidated_reporter_input(max_age_hours)

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

    return integrated_data


def _track_crew_availability(
    integrated_data: dict[str, Any],
    availability_report: Any,
    availability_tracker: DataAvailabilityTracker,
    max_age_hours: int,
) -> None:
    """Track stock, ETF, and crypto crew data availability.

    The three asset classes follow an identical pattern so they are handled in
    a single loop rather than three copy-pasted blocks.
    """
    crews = [
        ("stock", "stock_crew", "stock_analysis_data", "Stock crew data not found"),
        ("etf", "etf_crew", "etf_analysis_data", "ETF crew data not found"),
        ("crypto", "crypto_crew", "crypto_analysis_data", "Crypto crew data not found"),
    ]

    for asset_type, source_name, data_key, error_msg in crews:
        is_available = getattr(availability_report, f"{asset_type}_available", False)
        if is_available:
            age = DataAgeExtractor.extract_age_from_summary(availability_report.data_freshness_summary, asset_type, max_age_hours)
            availability_tracker.track_data_source(
                source=source_name,
                status="available",
                age_hours=age,
                record_count=len(integrated_data.get(data_key, [])),
            )
        else:
            availability_tracker.track_data_source(source=source_name, status="unavailable", error_message=error_msg)


def _track_portfolio_stats(
    integrated_data: dict[str, Any],
    availability_report: Any,
    availability_tracker: DataAvailabilityTracker,
    max_age_hours: int,
) -> None:
    """Track portfolio data availability and compute deep-analysis summary.

    Mutates *integrated_data* by adding ``deep_analysis_summary``.
    """
    if not availability_report.portfolio_available:
        availability_tracker.track_data_source(source="portfolio_review", status="unavailable", error_message="Portfolio review data not found")
        return

    portfolio_holdings = integrated_data.get("portfolio_review", {}).get("holdings", []) if integrated_data.get("portfolio_review") else []
    portfolio_age = DataAgeExtractor.extract_age_from_summary(availability_report.data_freshness_summary, "portfolio", max_age_hours)
    availability_tracker.track_data_source(
        source="portfolio_review",
        status="available",
        age_hours=portfolio_age,
        record_count=len(portfolio_holdings),
    )

    # Track deep analysis statistics from portfolio holdings
    deep_analysis_count = sum(1 for h in portfolio_holdings if h.get("crew_analysis_used"))
    holdings_with_alternatives = sum(1 for h in portfolio_holdings if h.get("alternatives"))

    if deep_analysis_count > 0:
        availability_tracker.track_data_source(
            source="deep_portfolio_analysis",
            status="available",
            record_count=deep_analysis_count,
        )
        logger.info(f"Deep portfolio analysis available for {deep_analysis_count} holdings")

        integrated_data["deep_analysis_summary"] = {
            "total_holdings": len(portfolio_holdings),
            "deep_analysis_count": deep_analysis_count,
            "shallow_analysis_count": len(portfolio_holdings) - deep_analysis_count,
            "holdings_with_alternatives": holdings_with_alternatives,
            "deep_analysis_percentage": (deep_analysis_count / len(portfolio_holdings) * 100) if portfolio_holdings else 0,
        }
    else:
        availability_tracker.track_data_source(
            source="deep_portfolio_analysis",
            status="unavailable",
            error_message="No deep analysis performed on portfolio holdings",
        )
        integrated_data["deep_analysis_summary"] = None


def _fetch_discovery_results(discovery_accessor: Any, inputs: dict[str, Any] | None) -> Any:
    """Resolve discovery results from Flow state inputs or from files.

    Returns the first non-None source or None if nothing is found.
    """
    if inputs:
        if inputs.get("aplus_opportunities"):
            logger.info("Using discovery results from Flow state (aplus_opportunities)")
            return inputs["aplus_opportunities"]
        if inputs.get("investment_discovery_structured"):
            logger.info("Using discovery results from Flow state (investment_discovery_structured)")
            return inputs["investment_discovery_structured"]

    discovery_results = discovery_accessor.load_discovery_results()
    if discovery_results:
        logger.info("Loaded discovery results from files")
    return discovery_results


def _build_discovery_summary(discovery_accessor: Any, discovery_results: Any) -> tuple[str, int]:
    """Return (summary_text, total_opportunities_count) for a non-None discovery result."""
    if hasattr(discovery_accessor, "get_opportunities_summary"):
        return discovery_accessor.get_opportunities_summary(), 0

    total_opportunities = 0
    if isinstance(discovery_results, dict):
        for key in ["stocks", "etfs", "crypto"]:
            if key in discovery_results:
                candidates = discovery_results[key].get("a_plus_candidates", [])
                total_opportunities += len(candidates)
    return f"{total_opportunities} A+ opportunities found", total_opportunities


def _resolve_and_track_discovery_results(
    discovery_accessor: Any,
    inputs: dict[str, Any] | None,
    availability_tracker: DataAvailabilityTracker,
    result: dict[str, Any],
) -> None:
    """Populate result with aplus_discovery_results / aplus_opportunities_summary and track."""
    discovery_results = _fetch_discovery_results(discovery_accessor, inputs)

    if discovery_results:
        result["aplus_discovery_results"] = discovery_results
        summary_text, total_opportunities = _build_discovery_summary(discovery_accessor, discovery_results)
        result["aplus_opportunities_summary"] = summary_text
        availability_tracker.track_data_source(source="aplus_discovery", status="available", record_count=total_opportunities)
        logger.info("Discovery results available with opportunities")
    else:
        result["aplus_discovery_results"] = None
        result["aplus_opportunities_summary"] = "No A+ opportunities found in current analysis"
        availability_tracker.track_data_source(source="aplus_discovery", status="available", record_count=0)
        logger.info("Discovery results exist but no opportunities found")


def _load_discovery_data(
    discovery_accessor: Any,
    inputs: dict[str, Any] | None,
    availability_tracker: DataAvailabilityTracker,
) -> dict[str, Any]:
    """Load A+ discovery data and track its availability.

    Returns a partial dict with keys:
    ``discovery_status``, ``aplus_discovery_results``, ``aplus_opportunities_summary``.
    """
    result: dict[str, Any] = {}

    discovery_helper = DiscoveryStatusHelper(discovery_accessor)
    discovery_status = discovery_helper.get_discovery_status(inputs)
    result["discovery_status"] = discovery_status

    if discovery_status["has_results"]:
        _resolve_and_track_discovery_results(discovery_accessor, inputs, availability_tracker, result)
    else:
        result["aplus_discovery_results"] = None
        result["aplus_opportunities_summary"] = discovery_status["message"]
        availability_tracker.track_data_source(source="aplus_discovery", status="unavailable", error_message=discovery_status["message"])
        logger.info(f"A+ discovery not available: {discovery_status['message']}")

    return result


def _load_backtesting_data(
    discovery_accessor: Any,
    backtesting_extractor: BacktestingDataExtractor,
    inputs: dict[str, Any] | None,
    availability_tracker: DataAvailabilityTracker,
) -> dict[str, Any]:
    """Load backtesting data and track its availability.

    Returns a partial dict with keys:
    ``backtesting_status``, ``backtesting_data``, ``backtesting_summary``.
    """
    result: dict[str, Any] = {}

    backtesting_helper = BacktestingStatusHelper(discovery_accessor, backtesting_extractor)
    backtesting_status_result = backtesting_helper.get_backtesting_status(inputs)

    # Extract backtesting data if available (delegates to existing helper method)
    backtesting_data = _extract_backtesting_data_from_results(backtesting_extractor, backtesting_status_result)
    result["backtesting_status"] = {
        "has_data": backtesting_data["has_backtesting_data"],
        "message": backtesting_data["message"],
        "status": backtesting_data["status"],
    }

    if backtesting_data["has_backtesting_data"]:
        result["backtesting_data"] = backtesting_data["backtesting_by_candidate"]
        result["backtesting_summary"] = backtesting_data.get("summary")

        # Track backtesting data as available
        availability_tracker.track_data_source(source="backtesting", status="available", record_count=backtesting_data.get("total_candidates", 0))

        logger.info(f"Loaded backtesting data for {backtesting_data['total_candidates']} candidates")
    else:
        result["backtesting_data"] = None
        result["backtesting_summary"] = None

        # Track backtesting as unavailable
        availability_tracker.track_data_source(source="backtesting", status="unavailable", error_message=backtesting_data["message"])

        logger.info(f"Backtesting data not available: {backtesting_data['message']}")

    return result


def _summarize_availability(
    availability_tracker: DataAvailabilityTracker,
) -> dict[str, Any]:
    """Generate the data availability summary section.

    Returns a partial dict with keys:
    ``data_availability_summary``, ``data_availability_summary_formatted``.
    """
    availability_summary = availability_tracker.get_availability_summary()
    result = {
        "data_availability_summary": availability_summary.model_dump(mode="json"),
        "data_availability_summary_formatted": availability_tracker.format_summary_for_report(availability_summary),
    }

    logger.info(
        "Integrated data context prepared for report generation",
        extra={
            "total_sources": availability_summary.total_sources,
            "available_sources": availability_summary.available_sources,
            "unavailable_sources": availability_summary.unavailable_sources,
            "stale_sources": availability_summary.stale_sources,
        },
    )

    return result


def _safe_get_metric(data: dict[str, Any], key: str) -> Any:
    """Safely get a numeric metric from a data dictionary."""
    try:
        value = data.get(key)
        if value is not None and isinstance(value, (int, float)):
            return float(value)
        return None
    except (TypeError, ValueError):
        return None


def _extract_candidate_metrics(vr_data: dict[str, Any], backtesting_extractor: BacktestingDataExtractor) -> tuple[str, dict[str, Any], Any] | None:
    """Extract BacktestingMetrics for a single validation-result dict.

    Returns (symbol, entry_dict, metrics) or None if extraction fails.
    """
    from finwiz.orchestrators.extraction.backtesting import BacktestingMetrics

    symbol = vr_data.get("symbol", "UNKNOWN")

    annualized_return = _safe_get_metric(vr_data, "annualized_return")
    if annualized_return is None:
        validation_details = vr_data.get("validation_details", [])
        if validation_details:
            returns = [d.get("annualized_return") for d in validation_details if d.get("annualized_return") is not None]
            if returns:
                annualized_return = sum(returns) / len(returns)

    win_rate = _safe_get_metric(vr_data, "win_rate")
    if win_rate is None:
        validation_details = vr_data.get("validation_details", [])
        if validation_details:
            rates = [d.get("win_rate") for d in validation_details if d.get("win_rate") is not None]
            if rates:
                win_rate = sum(rates) / len(rates)

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
    metrics = BacktestingMetrics(**metrics_dict)
    if not metrics:
        return None

    entry = {
        "metrics": metrics.model_dump(mode="json"),
        "formatted_display": backtesting_extractor.format_for_display(metrics),
        "available_metrics": backtesting_extractor.get_available_metrics(metrics),
    }
    return symbol, entry, metrics


def _build_backtesting_summary(all_metrics: list[Any]) -> dict[str, Any] | None:
    """Compute aggregate statistics over a list of BacktestingMetrics objects."""
    if not all_metrics:
        return None

    def _avg(attr: str) -> float | None:
        vals = [getattr(m, attr) for m in all_metrics if getattr(m, attr) is not None]
        return sum(vals) / len(vals) if vals else None

    return {
        "total_candidates_tested": len(all_metrics),
        "candidates_with_data": len([m for m in all_metrics if m.annualized_return is not None]),
        "average_annualized_return": _avg("annualized_return"),
        "average_sharpe_ratio": _avg("sharpe_ratio"),
        "average_max_drawdown": _avg("max_drawdown"),
    }


def _extract_backtesting_data_from_results(backtesting_extractor: BacktestingDataExtractor, backtesting_status_result: dict[str, Any]) -> dict[str, Any]:
    """Extract backtesting data from backtesting status result."""
    try:
        if not backtesting_status_result.get("has_backtesting_data"):
            return backtesting_status_result

        validation_results = backtesting_status_result.get("validation_results", [])
        backtesting_by_candidate: dict[str, Any] = {}
        all_metrics: list[Any] = []

        for vr_data in validation_results:
            try:
                extracted = _extract_candidate_metrics(vr_data, backtesting_extractor)
                if extracted is not None:
                    symbol, entry, metrics = extracted
                    backtesting_by_candidate[symbol] = entry
                    all_metrics.append(metrics)
                    logger.info(f"Extracted backtesting metrics for {symbol}")
            except Exception as e:
                logger.error(f"Failed to extract backtesting metrics for validation result: {e}")
                continue

        summary_data = _build_backtesting_summary(all_metrics)

        if backtesting_by_candidate:
            logger.info(f"Successfully extracted backtesting data for {len(backtesting_by_candidate)} candidates")
            return {
                "has_backtesting_data": True,
                "message": f"Backtesting data available for {len(backtesting_by_candidate)} candidates",
                "status": "available",
                "backtesting_by_candidate": backtesting_by_candidate,
                "summary": summary_data,
                "total_candidates": len(backtesting_by_candidate),
            }

        logger.warning("No backtesting metrics could be extracted from validation results")
        return {
            "has_backtesting_data": False,
            "message": "Backtesting data not available - metrics could not be extracted",
            "status": "not_available",
        }

    except Exception as e:
        logger.error(f"Failed to extract backtesting data: {e}", exc_info=True)
        return {"has_backtesting_data": False, "message": f"Backtesting data extraction failed: {e!s}", "status": "error"}


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

            # Load consolidated reporter input with all integrated data
            integrated_data = _load_reporter_input(self.data_accessor, max_age_hours)

            # Track crew data availability
            availability_report = self.data_accessor.check_data_availability(max_age_hours)
            _track_crew_availability(integrated_data, availability_report, self.availability_tracker, max_age_hours)

            # Track portfolio stats and deep-analysis summary
            _track_portfolio_stats(integrated_data, availability_report, self.availability_tracker, max_age_hours)

            # Add data availability information
            integrated_data["data_availability_report"] = availability_report.model_dump(mode="json")

            # Add stale data warnings
            integrated_data["stale_data_warnings"] = self.data_accessor.get_stale_data_warnings(max_age_hours)

            # Load discovery data
            integrated_data.update(_load_discovery_data(self.discovery_accessor, inputs, self.availability_tracker))

            # Load backtesting data
            integrated_data.update(_load_backtesting_data(self.discovery_accessor, self.backtesting_extractor, inputs, self.availability_tracker))

            # Generate data availability summary
            integrated_data.update(_summarize_availability(self.availability_tracker))

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
        """Extract backtesting data from backtesting status result.

        Delegates to the module-level function, preserving the instance method
        signature for any callers that reference self._extract_backtesting_data_from_results.
        """
        return _extract_backtesting_data_from_results(self.backtesting_extractor, backtesting_status_result)

    @staticmethod
    def _safe_get_metric(data: dict[str, Any], key: str) -> Any:
        """Safely get a metric from data dictionary. Delegates to module-level helper."""
        return _safe_get_metric(data, key)

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
