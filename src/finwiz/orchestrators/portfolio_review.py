"""Portfolio review orchestrator module with rebalancing integration."""

from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

from finwiz.orchestrators.portfolio_holdings_processor import (
    PortfolioHoldingsProcessor,
    ProcessingSummary,
)
from finwiz.schemas.portfolio_review import (
    HoldingDecision,
    PortfolioReview,
)
from finwiz.utils.cache_manager import get_cache_manager
from finwiz.utils.grading_system import (
    get_grade_css_styles,
    get_portfolio_grade_summary,
    score_to_grade,
)

logger = logging.getLogger(__name__)


# --- Configuration helpers ---


def _get_env(name: str, default: str) -> str:
    """Get environment variable with default value."""
    return (os.getenv(name) or default).strip()


def get_csv_paths() -> tuple[Path, Path, Path]:
    """Get CSV file paths for ETF, stock, and crypto data."""
    project_root = Path(__file__).resolve().parents[3]
    etf_csv = Path(_get_env("PORTFOLIO_ETF_CSV", str(project_root / "data/etf.csv")))
    stock_csv = Path(_get_env("PORTFOLIO_STOCK_CSV", str(project_root / "data/stock.csv")))
    crypto_csv = Path(_get_env("PORTFOLIO_CRYPTO_CSV", str(project_root / "data/crypto.csv")))
    return etf_csv, stock_csv, crypto_csv


def get_thresholds() -> tuple[float, float, int]:
    """Get portfolio review thresholds from environment."""

    def _f(name: str, default: float) -> float:
        try:
            return float(os.getenv(name, default))
        except Exception:
            return default

    def _i(name: str, default: int) -> int:
        try:
            return int(os.getenv(name, default))
        except Exception:
            return default

    return (
        _f("KEEP_THRESHOLD", 0.55),
        _f("DELTA_THRESHOLD", 0.10),
        _i("MAX_RISK_STEP", 1),
    )


# --- Helper functions for Flow state integration ---


def _merge_deep_analysis_from_flow_state(
    decisions: list[HoldingDecision],
    flow_state: Any,
) -> list[HoldingDecision]:
    """
    Merge deep analysis data from Flow state into HoldingDecision objects.

    Args:
        decisions: List of HoldingDecision objects from portfolio processor
        flow_state: Flow state containing deep analysis results and alternatives

    Returns:
        Updated list of HoldingDecision objects with deep analysis data

    """
    # Check if deep analysis data exists in Flow state
    if not hasattr(flow_state, "deep_analysis_results"):
        logger.info("No deep analysis results in Flow state")
        return decisions

    deep_analysis_results = flow_state.deep_analysis_results
    portfolio_alternatives = getattr(flow_state, "portfolio_alternatives", {})

    if not deep_analysis_results:
        logger.info("Deep analysis results dict is empty")
        return decisions

    logger.info(f"Merging deep analysis data for {len(deep_analysis_results)} holdings")

    # Track statistics
    merged_count = 0
    alternatives_added_count = 0

    # Merge deep analysis data into each decision
    for decision in decisions:
        ticker = decision.ticker

        # Check if we have deep analysis for this ticker
        if ticker in deep_analysis_results:
            analysis = deep_analysis_results[ticker]

            # Update composite score and grade from crew analysis
            decision.composite_score = analysis.composite_score
            decision.grade = analysis.grade

            # Update crew analysis metadata
            decision.crew_analysis_used = analysis.crew_name
            decision.analysis_date = analysis.analyzed_at
            decision.data_freshness = "fresh" if not analysis.cached else "recent"

            # Add detailed metrics to rationale if available
            if analysis.fundamental_score is not None:
                decision.rationale_bullets.append(f"Score Fondamental: {analysis.fundamental_score:.2f}")

            if analysis.technical_score is not None:
                decision.rationale_bullets.append(f"Score Technique: {analysis.technical_score:.2f}")

            if analysis.risk_score is not None:
                decision.rationale_bullets.append(f"Score de Risque: {analysis.risk_score:.1f}/5.0")

            # Add cache status to rationale
            if analysis.cached:
                decision.rationale_bullets.append("Analyse mise en cache (données récentes)")

            merged_count += 1
            logger.debug(f"Merged deep analysis for {ticker}: {analysis.grade} ({analysis.composite_score:.2f})")

        # Add alternatives if available
        if ticker in portfolio_alternatives:
            alternatives_data = portfolio_alternatives[ticker]

            # Convert alternatives data to Alternative objects
            from finwiz.schemas.portfolio_review import Alternative

            for alt_data in alternatives_data:
                try:
                    alternative = Alternative(**alt_data)
                    decision.alternatives.append(alternative)
                    alternatives_added_count += 1
                except Exception as e:
                    logger.warning(f"Failed to create Alternative object for {ticker}: {e}")
                    continue

            decision.has_a_plus_opportunities = len(decision.alternatives) > 0

            logger.debug(f"Added {len(decision.alternatives)} alternatives for {ticker}")

    logger.info(f"Deep analysis merge complete: {merged_count} holdings updated, {alternatives_added_count} alternatives added")

    return decisions


def get_flow_state_from_context() -> Any | None:
    """
    Get current Flow state from execution context.

    This is a helper function to access Flow state after Flow execution.
    Returns None if no Flow state is available.

    Returns:
        Flow state object or None

    """
    # This will be set by the Flow execution context
    # For now, return None - will be populated by Flow integration
    return None


# --- Builder using PortfolioHoldingsProcessor ---


async def build_portfolio_review(
    *,
    base_currency: str = "CHF",
    stock_csv: Path | None = None,
    etf_csv: Path | None = None,
    crypto_csv: Path | None = None,
    flow_state: Any | None = None,
) -> tuple[PortfolioReview, ProcessingSummary]:
    """
    Build portfolio review using PortfolioHoldingsProcessor with parallel processing.

    This ensures ALL holdings from CSV files are processed and included,
    even if validation fails. Uses async/await for parallel processing of holdings,
    reducing processing time from ~66 seconds to ~2-5 seconds for 66 holdings.

    If flow_state is provided, merges deep analysis data from Flow execution.

    Args:
        base_currency: Base currency for the portfolio
        stock_csv: Path to stock holdings CSV
        etf_csv: Path to ETF holdings CSV
        crypto_csv: Path to crypto holdings CSV
        flow_state: Optional Flow state containing deep analysis results

    Returns:
        Tuple of (PortfolioReview, ProcessingSummary)

    Performance:
        - Sequential: ~66 seconds for 66 holdings
        - Parallel: ~2-5 seconds for 66 holdings (13-33x speedup)

    """
    keep_threshold, _delta, _max_step = get_thresholds()

    # Initialize processor
    processor = PortfolioHoldingsProcessor()

    # Load ALL holdings from CSV files
    logger.info("Loading holdings from CSV files")
    raw_holdings = processor.load_all_holdings(
        stock_csv=stock_csv,
        etf_csv=etf_csv,
        crypto_csv=crypto_csv,
    )

    logger.info(f"Loaded {len(raw_holdings)} total holdings from CSV files")

    # Process ALL holdings in parallel (including those that fail validation)
    logger.info("Processing all holdings in parallel")
    decisions = await processor.process_holdings(
        holdings=raw_holdings,
        base_currency=base_currency,
        keep_threshold=keep_threshold,
    )

    logger.info(f"Processed {len(decisions)} holdings")

    # Get processing summary
    summary = processor.get_processing_summary()

    # Log summary statistics
    logger.info(
        f"Processing complete: {summary.processed_successfully} successful, "
        f"{summary.processed_with_warnings} with warnings, "
        f"{summary.failed_to_process} failed"
    )

    if summary.validation_failures:
        logger.warning(f"Validation failures: {len(summary.validation_failures)}")
        for ticker, reason in summary.validation_failures:
            logger.warning(f"  - {ticker}: {reason}")

    # Merge deep analysis data from Flow state if available
    if flow_state is not None:
        logger.info("Merging deep analysis data from Flow state")
        decisions = _merge_deep_analysis_from_flow_state(decisions, flow_state)

    # Create portfolio review
    review = PortfolioReview(
        as_of=datetime.now(UTC),
        base_currency=base_currency,
        holdings=decisions,
    )

    return review, summary


def _merge_deep_analysis_from_flow_state(decisions: list[HoldingDecision], flow_state: Any) -> list[HoldingDecision]:
    """
    Merge deep analysis results from Flow state into HoldingDecision objects.

    This function enriches portfolio decisions with:
    - Crew analysis metadata (crew_analysis_used, analysis_date)
    - Composite scores and grades from deep analysis
    - A+ alternatives for underperforming holdings

    Args:
        decisions: List of HoldingDecision objects from portfolio processor
        flow_state: Flow state containing deep_analysis_results and portfolio_alternatives

    Returns:
        Updated list of HoldingDecision objects with merged deep analysis data

    """
    try:
        # Access deep analysis results from structured Flow state
        deep_analysis_results = getattr(flow_state, "deep_analysis_results", {})
        portfolio_alternatives = getattr(flow_state, "portfolio_alternatives", {})

        if not deep_analysis_results:
            logger.info("No deep analysis results available in Flow state")
            return decisions

        # Statistics tracking
        holdings_with_deep_analysis = 0
        holdings_with_alternatives = 0

        # Merge deep analysis data into each HoldingDecision
        for decision in decisions:
            ticker = decision.ticker

            # Check if we have deep analysis for this ticker
            if ticker in deep_analysis_results:
                deep_result = deep_analysis_results[ticker]

                # Update HoldingDecision with deep analysis data
                decision.crew_analysis_used = deep_result.crew_name
                decision.analysis_date = deep_result.analyzed_at
                decision.composite_score = deep_result.composite_score
                decision.grade = deep_result.grade

                # Update grade description and recommended action using grading system
                grade_info = score_to_grade(deep_result.composite_score)
                decision.grade_description = grade_info.description
                decision.recommended_action = grade_info.action

                # Update data freshness
                decision.data_freshness = "fresh" if not deep_result.cached else "recent"

                holdings_with_deep_analysis += 1
                logger.debug(
                    f"Merged deep analysis for {ticker}: grade={deep_result.grade}, "
                    f"score={deep_result.composite_score:.3f}, crew={deep_result.crew_name}"
                )

            # Check if we have alternatives for this ticker
            if ticker in portfolio_alternatives:
                alternatives_data = portfolio_alternatives[ticker]

                # Convert alternative dictionaries to Alternative objects
                from finwiz.schemas.portfolio_review import Alternative

                alternatives = []
                for alt_dict in alternatives_data:
                    try:
                        alternative = Alternative.model_validate(alt_dict)
                        alternatives.append(alternative)
                    except Exception as e:
                        logger.warning(f"Failed to validate alternative for {ticker}: {e}")
                        continue

                # Update HoldingDecision with alternatives
                if alternatives:
                    decision.alternatives = alternatives[:3]  # Limit to top 3
                    decision.has_a_plus_opportunities = True
                    holdings_with_alternatives += 1
                    logger.debug(f"Added {len(alternatives)} alternatives for {ticker}")

        # Log merge statistics
        logger.info(
            f"Deep analysis merge complete: {holdings_with_deep_analysis} holdings with deep analysis, "
            f"{holdings_with_alternatives} holdings with alternatives"
        )

        return decisions

    except Exception as e:
        logger.error(f"Error merging deep analysis from Flow state: {e}", exc_info=True)
        # Return decisions unchanged on error (graceful degradation)
        return decisions


# --- I/O helpers ---


def save_review_json(
    review: PortfolioReview,
    out_path: Path,
    summary: ProcessingSummary | None = None,
) -> None:
    """
    Save portfolio review to JSON file with optional processing summary.

    Args:
        review: Portfolio review to save
        out_path: Output file path
        summary: Optional processing summary to include

    """
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Save the review directly (not wrapped) to match PortfolioReview schema
    output_data = json.loads(review.model_dump_json())

    # Log processing summary if provided (but don't include in JSON to avoid schema mismatch)
    if summary:
        logger.info(
            f"Saved portfolio review with processing summary: "
            f"{summary.total_holdings} total, "
            f"{summary.processed_successfully} successful, "
            f"{summary.processed_with_warnings} warnings, "
            f"{summary.failed_to_process} failed"
        )
        
        # Save processing summary to a separate file
        summary_path = out_path.parent / "portfolio_processing_summary.json"
        summary_data = {
            "total_holdings": summary.total_holdings,
            "processed_successfully": summary.processed_successfully,
            "processed_with_warnings": summary.processed_with_warnings,
            "failed_to_process": summary.failed_to_process,
            "by_asset_class": summary.by_asset_class,
            "validation_failures": [{"ticker": ticker, "reason": reason} for ticker, reason in summary.validation_failures],
            "excluded_holdings": [{"ticker": ticker, "reason": reason} for ticker, reason in summary.excluded_holdings],
        }
        with open(summary_path, "w") as f:
            json.dump(summary_data, f, indent=2)
        logger.info(f"Saved processing summary to {summary_path}")

    out_path.write_text(json.dumps(output_data, indent=2), encoding="utf-8")


async def run_with_rebalancing(
    target_weights: dict[str, float] | None = None,
    available_capital: float = 0.0,
    include_rebalancing: bool = True,
    flow_state: Any | None = None,
) -> tuple[Path, dict[str, Any] | None]:
    """
    Run portfolio review process with optional rebalancing analysis.

    Args:
        target_weights: Target allocation weights for rebalancing
        available_capital: Available capital for rebalancing
        include_rebalancing: Whether to include rebalancing analysis
        flow_state: Optional Flow state containing deep analysis results

    Returns:
        Tuple of (review_path, rebalancing_result)

    """
    # Get CSV paths
    etf_csv, stock_csv, crypto_csv = get_csv_paths()

    # Run portfolio review using PortfolioHoldingsProcessor
    logger.info("Running portfolio review with holdings processor")
    review, summary = build_portfolio_review(
        stock_csv=stock_csv,
        etf_csv=etf_csv,
        crypto_csv=crypto_csv,
        flow_state=flow_state,
    )

    # Log count of holdings processed vs. holdings in CSV
    logger.info(f"Holdings processed: {len(review.holdings)} decisions generated from {summary.total_holdings} CSV entries")
    logger.info(f"By asset class: {summary.by_asset_class}")

    # Save portfolio review with processing summary
    project_root = Path(__file__).resolve().parents[3]
    out = project_root / "output" / "portfolio" / "portfolio_review.json"
    save_review_json(review, out, summary)

    rebalancing_result = None

    if include_rebalancing and target_weights:
        try:
            # Import rebalancing orchestrator
            from finwiz.orchestrators.portfolio_rebalancing import PortfolioRebalancingOrchestrator
            from finwiz.schemas.portfolio_rebalancing import Holding, PortfolioConfiguration

            # Convert portfolio review holdings to rebalancing holdings
            holdings = []
            for decision in review.holdings:
                if decision.decision == "KEEP":  # Only include holdings we're keeping
                    # For demo purposes, assume 100 shares per holding
                    # In real implementation, this would come from actual portfolio data
                    holdings.append(
                        Holding(
                            symbol=decision.ticker,
                            shares=100.0,  # Placeholder - would need actual share counts
                            cost_basis=None,
                            acquisition_date=None,
                        )
                    )

            if holdings:
                # Create portfolio configuration
                config = PortfolioConfiguration(
                    holdings=holdings,
                    target_weights=target_weights,
                    available_capital=available_capital,
                    global_tolerance=0.05,  # 5% tolerance
                )

                # Run rebalancing analysis
                orchestrator = PortfolioRebalancingOrchestrator()
                rebalancing_result = await orchestrator.rebalance_portfolio(config)

                # Save rebalancing result
                rebalancing_out = project_root / "output" / "portfolio" / "rebalancing_analysis.json"
                rebalancing_out.parent.mkdir(parents=True, exist_ok=True)
                rebalancing_out.write_text(rebalancing_result.model_dump_json(indent=2), encoding="utf-8")

        except Exception as e:
            print(f"Warning: Rebalancing analysis failed: {e}")
            rebalancing_result = None

    return out, rebalancing_result


async def run(flow_state: Any | None = None) -> Path:
    """
    Run standard portfolio review process with parallel holdings processing.

    Args:
        flow_state: Optional Flow state containing deep analysis results

    Returns:
        Path to saved portfolio review JSON

    Performance:
        Uses async/await for parallel processing of holdings, reducing
        processing time from ~66 seconds to ~2-5 seconds for 66 holdings.

    """
    # Get CSV paths
    etf_csv, stock_csv, crypto_csv = get_csv_paths()

    # Run portfolio review using PortfolioHoldingsProcessor with parallel processing
    logger.info("Running portfolio review with parallel holdings processor")
    review, summary = await build_portfolio_review(
        stock_csv=stock_csv,
        etf_csv=etf_csv,
        crypto_csv=crypto_csv,
        flow_state=flow_state,
    )

    # Log count of holdings processed vs. holdings in CSV
    logger.info(f"Holdings processed: {len(review.holdings)} decisions generated from {summary.total_holdings} CSV entries")
    logger.info(f"By asset class: {summary.by_asset_class}")

    # Save portfolio review with processing summary
    project_root = Path(__file__).resolve().parents[3]
    out = project_root / "output" / "portfolio" / "portfolio_review.json"
    save_review_json(review, out, summary)

    return out


class EnhancedPortfolioReviewOrchestrator:
    """
    Enhanced portfolio review orchestrator with integrated rebalancing capabilities.

    Provides seamless integration between portfolio review and rebalancing analysis,
    with shared caching and unified reporting.
    """

    def __init__(self) -> None:
        """Initialize the enhanced orchestrator."""
        self.cache_manager = get_cache_manager()

    async def run_comprehensive_analysis(
        self,
        target_weights: dict[str, float] | None = None,
        available_capital: float = 0.0,
        enable_caching: bool = True,
    ) -> dict[str, Any]:
        """
        Run comprehensive portfolio analysis including review and rebalancing.

        Args:
            target_weights: Target allocation weights for rebalancing
            available_capital: Available capital for rebalancing
            enable_caching: Whether to use caching for expensive operations

        Returns:
            Comprehensive analysis results

        """
        cache_key = ["portfolio_analysis", str(target_weights), str(available_capital)]

        if enable_caching:
            cached_result = await self.cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result

        # Run portfolio review
        review_path, rebalancing_result = await run_with_rebalancing(
            target_weights=target_weights,
            available_capital=available_capital,
            include_rebalancing=target_weights is not None,
        )

        # Load review data
        review_data = json.loads(Path(review_path).read_text(encoding="utf-8"))

        # Combine results
        comprehensive_result = {
            "portfolio_review": review_data,
            "rebalancing_analysis": rebalancing_result.model_dump() if rebalancing_result else None,
            "analysis_timestamp": datetime.now(UTC).isoformat(),
            "has_rebalancing_recommendations": rebalancing_result is not None,
        }

        # Cache the result for 30 minutes
        if enable_caching:
            await self.cache_manager.set(cache_key, comprehensive_result, ttl=1800)

        return comprehensive_result

    async def generate_unified_report(
        self,
        analysis_result: dict[str, Any],
        language: str = "en",
    ) -> str:
        """
        Generate unified HTML report combining portfolio review and rebalancing.

        Args:
            analysis_result: Comprehensive analysis result
            language: Report language (en/fr)

        Returns:
            HTML report content

        """
        from finwiz.tools.html_report_generator import HTMLReportGenerator

        generator = HTMLReportGenerator()

        # Add portfolio review sections
        self._add_portfolio_review_sections(generator, analysis_result["portfolio_review"])

        # Add rebalancing sections if available
        if analysis_result["rebalancing_analysis"]:
            self._add_rebalancing_sections(generator, analysis_result["rebalancing_analysis"])

        # Generate report using unified template
        title = f"Comprehensive Portfolio Analysis - {datetime.now().strftime('%Y-%m-%d')}"

        # Try to use unified HTML generator if available
        if hasattr(generator, "generate_unified_html"):
            return generator.generate_unified_html(title=title, language=language)
        else:
            return generator.generate_html_fallback(title=title, language=language)

    def _add_portfolio_review_sections(self, generator: Any, review_data: dict[str, Any]) -> None:
        """Add portfolio review sections to the report."""
        # Extract holdings and processing summary
        if "portfolio_review" in review_data:
            # New format with processing summary
            holdings = review_data["portfolio_review"].get("holdings", [])
            processing_summary = review_data.get("processing_summary")
        else:
            # Legacy format
            holdings = review_data.get("holdings", [])
            processing_summary = None

        keep_count = sum(1 for h in holdings if h.get("decision") == "KEEP")
        sell_count = sum(1 for h in holdings if h.get("decision") == "SELL")

        # Create portfolio overview using bs4
        soup = BeautifulSoup("", "html.parser")
        overview_div = soup.new_tag("div", **{"class": "portfolio-overview"})

        # Title
        title = soup.new_tag("h3")
        title.string = "Portfolio Overview"
        overview_div.append(title)

        # Metrics grid
        metrics_grid = soup.new_tag("div", **{"class": "metrics-grid"})

        # Total holdings metric
        total_metric = soup.new_tag("div", **{"class": "metric"})
        total_label = soup.new_tag("span", **{"class": "metric-label"})
        total_label.string = "Total Holdings:"
        total_value = soup.new_tag("span", **{"class": "metric-value"})
        total_value.string = str(len(holdings))
        total_metric.append(total_label)
        total_metric.append(total_value)
        metrics_grid.append(total_metric)

        # Keep recommendations metric
        keep_metric = soup.new_tag("div", **{"class": "metric"})
        keep_label = soup.new_tag("span", **{"class": "metric-label"})
        keep_label.string = "Keep Recommendations:"
        keep_value = soup.new_tag("span", **{"class": "metric-value keep"})
        keep_value.string = str(keep_count)
        keep_metric.append(keep_label)
        keep_metric.append(keep_value)
        metrics_grid.append(keep_metric)

        # Sell recommendations metric
        sell_metric = soup.new_tag("div", **{"class": "metric"})
        sell_label = soup.new_tag("span", **{"class": "metric-label"})
        sell_label.string = "Sell Recommendations:"
        sell_value = soup.new_tag("span", **{"class": "metric-value sell"})
        sell_value.string = str(sell_count)
        sell_metric.append(sell_label)
        sell_metric.append(sell_value)
        metrics_grid.append(sell_metric)

        overview_div.append(metrics_grid)
        soup.append(overview_div)

        # Add processing summary if available
        if processing_summary:
            summary_div = soup.new_tag("div", **{"class": "processing-summary"})

            summary_title = soup.new_tag("h4")
            summary_title.string = "Processing Summary"
            summary_div.append(summary_title)

            # Processing metrics
            summary_list = soup.new_tag("ul")

            # Total processed
            total_li = soup.new_tag("li")
            total_li.string = f"Total holdings in CSV: {processing_summary['total_holdings']}"
            summary_list.append(total_li)

            # Successfully processed
            success_li = soup.new_tag("li")
            success_li.string = f"Successfully processed: {processing_summary['processed_successfully']}"
            summary_list.append(success_li)

            # Warnings
            if processing_summary["processed_with_warnings"] > 0:
                warning_li = soup.new_tag("li")
                warning_li.string = f"Processed with warnings: {processing_summary['processed_with_warnings']}"
                summary_list.append(warning_li)

            # Failed
            if processing_summary["failed_to_process"] > 0:
                failed_li = soup.new_tag("li")
                failed_li.string = f"Failed to process: {processing_summary['failed_to_process']}"
                summary_list.append(failed_li)

            # By asset class
            by_class_li = soup.new_tag("li")
            by_class_li.string = f"By asset class: {processing_summary['by_asset_class']}"
            summary_list.append(by_class_li)

            summary_div.append(summary_list)

            # Validation failures
            if processing_summary.get("validation_failures"):
                failures_title = soup.new_tag("h5")
                failures_title.string = "Validation Issues"
                summary_div.append(failures_title)

                failures_list = soup.new_tag("ul")
                for failure in processing_summary["validation_failures"]:
                    failure_li = soup.new_tag("li")
                    failure_li.string = f"{failure['ticker']}: {failure['reason']}"
                    failures_list.append(failure_li)
                summary_div.append(failures_list)

            soup.append(summary_div)

        overview_content = soup.prettify(formatter="html")
        generator.add_section("Portfolio Overview", overview_content, "portfolio", order=1)

        # Holdings analysis with validation status
        holdings_content = self._generate_holdings_table(holdings)
        generator.add_section("Holdings Analysis", holdings_content, "analysis", order=2)

    def _add_rebalancing_sections(self, generator: Any, rebalancing_data: dict[str, Any]) -> None:
        """Add rebalancing sections to the report."""
        # Rebalancing summary
        execution_summary = rebalancing_data.get("execution_summary", {})
        cost_analysis = rebalancing_data.get("cost_analysis", {})

        # Create rebalancing summary using bs4
        soup = BeautifulSoup("", "html.parser")
        summary_div = soup.new_tag("div", **{"class": "rebalancing-summary"})

        # Title
        title = soup.new_tag("h3")
        title.string = "Rebalancing Summary"
        summary_div.append(title)

        # Metrics grid
        metrics_grid = soup.new_tag("div", **{"class": "metrics-grid"})

        # Trades required metric
        trades_metric = soup.new_tag("div", **{"class": "metric"})
        trades_label = soup.new_tag("span", **{"class": "metric-label"})
        trades_label.string = "Trades Required:"
        trades_value = soup.new_tag("span", **{"class": "metric-value"})
        trades_value.string = str(execution_summary.get("total_trades_required", 0))
        trades_metric.append(trades_label)
        trades_metric.append(trades_value)
        metrics_grid.append(trades_metric)

        # Total cost metric
        cost_metric = soup.new_tag("div", **{"class": "metric"})
        cost_label = soup.new_tag("span", **{"class": "metric-label"})
        cost_label.string = "Total Cost:"
        cost_value = soup.new_tag("span", **{"class": "metric-value"})
        cost_value.string = f"${cost_analysis.get('total_transaction_costs', 0):.2f}"
        cost_metric.append(cost_label)
        cost_metric.append(cost_value)
        metrics_grid.append(cost_metric)

        # Recommendation metric
        rec_metric = soup.new_tag("div", **{"class": "metric"})
        rec_label = soup.new_tag("span", **{"class": "metric-label"})
        rec_label.string = "Recommendation:"
        rec_value = soup.new_tag("span", **{"class": "metric-value"})
        rec_value.string = rebalancing_data.get("overall_recommendation", "N/A")
        rec_metric.append(rec_label)
        rec_metric.append(rec_value)
        metrics_grid.append(rec_metric)

        summary_div.append(metrics_grid)
        soup.append(summary_div)

        summary_content = soup.prettify(formatter="html")
        generator.add_section("Rebalancing Summary", summary_content, "financial", order=3)

        # Trade recommendations
        trades = rebalancing_data.get("trade_recommendations", [])
        if trades:
            trades_content = self._generate_trades_table(trades)
            generator.add_section("Trade Recommendations", trades_content, "opportunity", order=4)

    def _generate_holdings_table(self, holdings: list[dict[str, Any]]) -> str:
        """Generate HTML table for holdings with letter grades."""
        if not holdings:
            # Use bs4 for simple paragraph
            soup = BeautifulSoup("", "html.parser")
            p = soup.new_tag("p")
            p.string = "No holdings found."
            soup.append(p)
            return soup.prettify(formatter="html")

        # Calculate portfolio grade summary
        scores = [holding.get("composite_score", 0) for holding in holdings]
        grade_summary = get_portfolio_grade_summary(scores)

        # Create main soup container
        soup = BeautifulSoup("", "html.parser")

        # Add CSS styles
        style = soup.new_tag("style")
        style.string = get_grade_css_styles()
        soup.append(style)

        # Generate grade summary using BeautifulSoup
        grade_div = soup.new_tag("div", **{"class": "grade-summary"})

        # Title
        title = soup.new_tag("h4")
        title.string = "📊 Bulletin du Portefeuille"
        grade_div.append(title)

        # Average grade paragraph
        avg_p = soup.new_tag("p")
        avg_strong = soup.new_tag("strong")
        avg_strong.string = "Moyenne générale :"
        avg_p.append(avg_strong)
        avg_p.append(f" {grade_summary['grade_info'].emoji} ")

        grade_strong = soup.new_tag("strong")
        grade_strong.string = grade_summary["average_grade"]
        avg_p.append(grade_strong)
        avg_p.append(f" ({grade_summary['average_percentage']:.0f}%)")
        grade_div.append(avg_p)

        # Distribution paragraph
        dist_p = soup.new_tag("p")
        dist_strong = soup.new_tag("strong")
        dist_strong.string = "Répartition des notes :"
        dist_p.append(dist_strong)
        grade_div.append(dist_p)

        # Distribution list
        grade_ul = soup.new_tag("ul")
        for grade, data in grade_summary["distribution"].items():
            grade_info = score_to_grade(0.5)  # Get emoji for grade
            for test_score in [0.98, 0.90, 0.82, 0.77, 0.72, 0.67, 0.55, 0.25]:
                test_grade_info = score_to_grade(test_score)
                if test_grade_info.grade == grade:
                    grade_info = test_grade_info
                    break

            li = soup.new_tag("li")
            li.append(f"{grade_info.emoji} ")
            strong = soup.new_tag("strong")
            strong.string = grade
            li.append(strong)
            li.append(f": {data['count']} positions ({data['percentage']:.0f}%)")
            grade_ul.append(li)

        grade_div.append(grade_ul)
        soup.append(grade_div)

        # Create holdings table
        table = soup.new_tag("table", **{"class": "holdings-table"})

        # Count deep vs shallow analysis
        deep_count = sum(1 for h in holdings if h.get("crew_analysis_used"))
        shallow_count = len(holdings) - deep_count

        # Add analysis depth summary
        if deep_count > 0:
            analysis_summary = soup.new_tag("div", **{"class": "analysis-summary"})
            summary_title = soup.new_tag("h4")
            summary_title.string = "📊 Profondeur d'Analyse"
            analysis_summary.append(summary_title)

            summary_p = soup.new_tag("p")
            summary_p.append(f"🔍 Analyse Approfondie: {deep_count} positions | ")
            summary_p.append(f"⚡ Validation Rapide: {shallow_count} positions")
            analysis_summary.append(summary_p)

            soup.append(analysis_summary)

        # Table header
        thead = soup.new_tag("thead")
        header_row = soup.new_tag("tr")
        headers = [
            "Ticker",
            "Nom",
            "Type",
            "Analyse",
            "Décision",
            "Note",
            "Scores",
            "Risque",
            "Alternatives A+",
        ]
        for header_text in headers:
            th = soup.new_tag("th")
            th.string = header_text
            header_row.append(th)
        thead.append(header_row)
        table.append(thead)

        # Table body
        tbody = soup.new_tag("tbody")
        for holding in holdings:
            decision_class = "keep" if holding.get("decision") == "KEEP" else "sell"
            risk_score = holding.get("risk", {}).get("score", 0)
            composite_score = holding.get("composite_score", 0)

            # Get grade information
            grade_info = score_to_grade(composite_score)

            # Check if deep analysis was used
            crew_analysis_used = holding.get("crew_analysis_used")
            is_deep_analysis = crew_analysis_used is not None

            # Create table row
            tr = soup.new_tag("tr")

            # Ticker cell
            td_ticker = soup.new_tag("td")
            td_ticker.string = holding.get("ticker", "N/A")
            tr.append(td_ticker)

            # Name cell
            td_name = soup.new_tag("td")
            td_name.string = holding.get("name", "N/A")
            tr.append(td_name)

            # Asset class cell
            td_asset = soup.new_tag("td")
            td_asset.string = holding.get("asset_class", "N/A").upper()
            tr.append(td_asset)

            # Analysis depth indicator cell
            td_analysis = soup.new_tag("td")
            if is_deep_analysis:
                analysis_span = soup.new_tag("span", **{"class": "analysis-deep"})
                analysis_span.string = "🔍 Deep"
                td_analysis.append(analysis_span)
                # Add crew name as tooltip
                if crew_analysis_used:
                    crew_small = soup.new_tag("small")
                    crew_small.string = f" ({crew_analysis_used})"
                    td_analysis.append(crew_small)
            else:
                analysis_span = soup.new_tag("span", **{"class": "analysis-quick"})
                analysis_span.string = "⚡ Quick"
                td_analysis.append(analysis_span)
            tr.append(td_analysis)

            # Decision cell
            td_decision = soup.new_tag("td", **{"class": decision_class})
            td_decision.string = holding.get("decision", "N/A")
            tr.append(td_decision)

            # Grade cell with badge
            td_grade = soup.new_tag("td")
            grade_span = soup.new_tag("span", **{"class": f"grade-badge {grade_info.css_class}"})
            grade_span.string = f"{grade_info.emoji} {grade_info.grade}"
            td_grade.append(grade_span)
            tr.append(td_grade)

            # Scores cell (show detailed metrics if available from deep analysis)
            td_scores = soup.new_tag("td")
            if is_deep_analysis:
                # Extract scores from rationale bullets
                rationale_bullets = holding.get("rationale_bullets", [])
                scores_list = soup.new_tag("ul", **{"class": "scores-list"})
                for bullet in rationale_bullets:
                    if "Score" in bullet or "score" in bullet:
                        score_li = soup.new_tag("li")
                        score_li.string = bullet
                        scores_list.append(score_li)
                if scores_list.contents:
                    td_scores.append(scores_list)
                else:
                    td_scores.string = f"{composite_score:.2f}"
            else:
                td_scores.string = f"{composite_score:.2f}"
            tr.append(td_scores)

            # Risk cell
            td_risk = soup.new_tag("td")
            td_risk.string = f"{risk_score:.1f}/10"
            tr.append(td_risk)

            # Alternatives cell
            td_alternatives = soup.new_tag("td")
            alternatives = holding.get("alternatives", [])
            if alternatives:
                alt_count = len(alternatives)
                alt_span = soup.new_tag("span", **{"class": "alternatives-available"})
                alt_span.string = f"💎 {alt_count} A+ disponible{'s' if alt_count > 1 else ''}"
                td_alternatives.append(alt_span)

                # Add alternatives list
                alt_list = soup.new_tag("ul", **{"class": "alternatives-list"})
                for alt in alternatives[:3]:  # Show top 3
                    alt_li = soup.new_tag("li")
                    alt_ticker = alt.get("ticker", "N/A")
                    alt_grade = alt.get("grade", "A+")
                    alt_score = alt.get("composite_score", 0)
                    alt_li.string = f"{alt_ticker} ({alt_grade}, {alt_score:.2f})"
                    alt_list.append(alt_li)
                td_alternatives.append(alt_list)
            else:
                td_alternatives.string = "-"
            tr.append(td_alternatives)

            tbody.append(tr)

        table.append(tbody)
        soup.append(table)

        return soup.prettify(formatter="html")

    def _generate_trades_table(self, trades: list[dict[str, Any]]) -> str:
        """Generate HTML table for trade recommendations."""
        if not trades:
            # Use bs4 for simple paragraph
            soup = BeautifulSoup("", "html.parser")
            p = soup.new_tag("p")
            p.string = "No trades recommended."
            soup.append(p)
            return soup.prettify(formatter="html")

        # Create main soup container
        soup = BeautifulSoup("", "html.parser")

        # Create trades table
        table = soup.new_tag("table", **{"class": "trades-table"})

        # Table header
        thead = soup.new_tag("thead")
        header_row = soup.new_tag("tr")
        headers = ["Symbol", "Action", "Quantity", "Price", "Value", "Cost", "Priority"]
        for header_text in headers:
            th = soup.new_tag("th")
            th.string = header_text
            header_row.append(th)
        thead.append(header_row)
        table.append(thead)

        # Table body
        tbody = soup.new_tag("tbody")
        for trade in trades:
            action_class = trade.get("action", "").lower()

            # Create table row
            tr = soup.new_tag("tr")

            # Symbol cell
            td_symbol = soup.new_tag("td")
            td_symbol.string = trade.get("symbol", "N/A")
            tr.append(td_symbol)

            # Action cell
            td_action = soup.new_tag("td", **{"class": action_class})
            td_action.string = trade.get("action", "N/A")
            tr.append(td_action)

            # Quantity cell
            td_quantity = soup.new_tag("td")
            td_quantity.string = f"{trade.get('quantity', 0):.2f}"
            tr.append(td_quantity)

            # Price cell
            td_price = soup.new_tag("td")
            td_price.string = f"${trade.get('current_price', 0):.2f}"
            tr.append(td_price)

            # Value cell
            td_value = soup.new_tag("td")
            td_value.string = f"${trade.get('trade_value', 0):.2f}"
            tr.append(td_value)

            # Cost cell
            td_cost = soup.new_tag("td")
            td_cost.string = f"${trade.get('total_estimated_cost', 0):.2f}"
            tr.append(td_cost)

            # Priority cell
            td_priority = soup.new_tag("td")
            td_priority.string = str(trade.get("priority", 0))
            tr.append(td_priority)

            tbody.append(tr)

        table.append(tbody)
        soup.append(table)

        return soup.prettify(formatter="html")


if __name__ == "__main__":
    import asyncio
    import json

    async def main() -> None:
        """Run portfolio review demonstration."""
        # Run standard portfolio review
        path = run()
        print(f"Portfolio review saved to: {path}")

        # Example of enhanced analysis with rebalancing
        orchestrator = EnhancedPortfolioReviewOrchestrator()

        # Example target weights (adjust as needed)
        target_weights = {
            "AAPL": 0.20,
            "GOOGL": 0.15,
            "MSFT": 0.15,
            "TSLA": 0.10,
            "NVDA": 0.10,
            "SPY": 0.30,  # ETF allocation
        }

        try:
            comprehensive_result = await orchestrator.run_comprehensive_analysis(
                target_weights=target_weights,
                available_capital=10000.0,
            )

            # Save comprehensive result
            project_root = Path(__file__).resolve().parents[3]
            comprehensive_out = project_root / "output" / "portfolio" / "comprehensive_analysis.json"
            comprehensive_out.parent.mkdir(parents=True, exist_ok=True)
            comprehensive_out.write_text(json.dumps(comprehensive_result, indent=2, default=str), encoding="utf-8")
            print(f"Comprehensive analysis saved to: {comprehensive_out}")

            # Generate unified report
            html_report = await orchestrator.generate_unified_report(comprehensive_result)
            report_out = project_root / "output" / "portfolio" / "comprehensive_report.html"
            report_out.write_text(html_report, encoding="utf-8")
            print(f"Unified report saved to: {report_out}")

        except Exception as e:
            print(f"Enhanced analysis failed: {e}")

    asyncio.run(main())
