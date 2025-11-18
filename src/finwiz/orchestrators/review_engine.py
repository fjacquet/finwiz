"""Portfolio review engine - core review logic and building functions."""

from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from finwiz.orchestrators.portfolio_holdings_processor import (
    PortfolioHoldingsProcessor,
    ProcessingSummary,
)
from finwiz.schemas.portfolio_review import (
    HoldingDecision,
    PortfolioReview,
)
from finwiz.utils.grading_system import score_to_grade

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


# --- Flow state integration ---


def _merge_deep_analysis_from_flow_state(
    decisions: list[HoldingDecision],
    flow_state: Any,
) -> list[HoldingDecision]:
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
                logger.debug(f"Merged deep analysis for {ticker}: grade={deep_result.grade}, score={deep_result.composite_score:.3f}, crew={deep_result.crew_name}")

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
        logger.info(f"Deep analysis merge complete: {holdings_with_deep_analysis} holdings with deep analysis, {holdings_with_alternatives} holdings with alternatives")

        return decisions

    except Exception as e:
        logger.error(f"Error merging deep analysis from Flow state: {e}", exc_info=True)
        # Return decisions unchanged on error (graceful degradation)
        return decisions


# --- Core review building ---


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
    logger.info(f"Processing complete: {summary.processed_successfully} successful, {summary.processed_with_warnings} with warnings, {summary.failed_to_process} failed")

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


# --- Main execution functions ---


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
            logger.warning(f"Rebalancing analysis failed: {e}")
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
