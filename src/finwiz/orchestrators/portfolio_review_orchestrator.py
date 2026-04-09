"""
Portfolio review orchestrator - Application/Service Layer.

This module contains business logic orchestration for portfolio review:
- Configuration and thresholds
- Holdings decision building (pure functions)
- Portfolio review building and execution
- Integration with rebalancing

HTML generation is delegated to reporting layer (finwiz.reporting.portfolio_review_html).
"""

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
from finwiz.orchestrators.portfolio_review.merge import merge_deep_analysis_from_flow_state
from finwiz.schemas.portfolio_review import PortfolioReview

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration Helpers
# =============================================================================


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
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse float env var {name}, using default {default}: {e}")
            return default

    def _i(name: str, default: int) -> int:
        try:
            return int(os.getenv(name, default))
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse int env var {name}, using default {default}: {e}")
            return default

    return (
        _f("KEEP_THRESHOLD", 0.55),
        _f("DELTA_THRESHOLD", 0.10),
        _i("MAX_RISK_STEP", 1),
    )


# =============================================================================
# Core Review Building
# =============================================================================


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

    Args:
        base_currency: Base currency for the portfolio
        stock_csv: Path to stock holdings CSV
        etf_csv: Path to ETF holdings CSV
        crypto_csv: Path to crypto holdings CSV
        flow_state: Optional Flow state containing deep analysis results

    Returns:
        Tuple of (PortfolioReview, ProcessingSummary)

    """
    keep_threshold, _delta, _max_step = get_thresholds()

    processor = PortfolioHoldingsProcessor()

    logger.info("Loading holdings from CSV files")
    raw_holdings = processor.load_all_holdings(
        stock_csv=stock_csv,
        etf_csv=etf_csv,
        crypto_csv=crypto_csv,
    )

    logger.info(f"Loaded {len(raw_holdings)} total holdings from CSV files")

    logger.info("Processing all holdings in parallel")
    decisions = await processor.process_holdings(
        holdings=raw_holdings,
        base_currency=base_currency,
        keep_threshold=keep_threshold,
    )

    logger.info(f"Processed {len(decisions)} holdings")

    summary = processor.get_processing_summary()

    logger.info(f"Processing complete: {summary.processed_successfully} successful, {summary.processed_with_warnings} with warnings, {summary.failed_to_process} failed")

    if summary.validation_failures:
        logger.warning(f"Validation failures: {len(summary.validation_failures)}")
        for ticker, reason in summary.validation_failures:
            logger.warning(f"  - {ticker}: {reason}")

    if flow_state is not None:
        logger.info("Merging deep analysis data from Flow state")
        decisions = merge_deep_analysis_from_flow_state(decisions, flow_state)

    review = PortfolioReview(
        as_of=datetime.now(UTC),
        base_currency=base_currency,
        holdings=decisions,
    )

    return review, summary


def save_review_json(
    review: PortfolioReview,
    out_path: Path,
    summary: ProcessingSummary | None = None,
) -> None:
    """Save portfolio review to JSON file with optional processing summary."""
    out_path.parent.mkdir(parents=True, exist_ok=True)

    output_data = json.loads(review.model_dump_json())

    if summary:
        logger.info(
            f"Saved portfolio review with processing summary: "
            f"{summary.total_holdings} total, "
            f"{summary.processed_successfully} successful, "
            f"{summary.processed_with_warnings} warnings, "
            f"{summary.failed_to_process} failed"
        )

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

    out_path.write_text(json.dumps(output_data, indent=2, default=str), encoding="utf-8")


# =============================================================================
# Main Execution Functions
# =============================================================================


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
    etf_csv, stock_csv, crypto_csv = get_csv_paths()

    logger.info("Running portfolio review with holdings processor")
    review, summary = await build_portfolio_review(
        stock_csv=stock_csv,
        etf_csv=etf_csv,
        crypto_csv=crypto_csv,
        flow_state=flow_state,
    )

    logger.info(f"Holdings processed: {len(review.holdings)} decisions from {summary.total_holdings} CSV entries")
    logger.info(f"By asset class: {summary.by_asset_class}")

    project_root = Path(__file__).resolve().parents[3]
    out = project_root / "output" / "portfolio" / "portfolio_review.json"
    save_review_json(review, out, summary)

    rebalancing_result = None

    if include_rebalancing and target_weights:
        try:
            from finwiz.orchestrators.portfolio_rebalancing import PortfolioRebalancingOrchestrator
            from finwiz.schemas.portfolio_rebalancing import Holding, PortfolioConfiguration

            holdings = []
            for decision in review.holdings:
                if decision.decision == "KEEP":
                    holdings.append(
                        Holding(
                            symbol=decision.ticker,
                            shares=100.0,  # Placeholder
                            cost_basis=None,
                            acquisition_date=None,
                        )
                    )

            if holdings:
                config = PortfolioConfiguration(
                    holdings=holdings,
                    target_weights=target_weights,
                    available_capital=available_capital,
                    global_tolerance=0.05,
                )

                orchestrator = PortfolioRebalancingOrchestrator()
                rebalancing_result = await orchestrator.rebalance_portfolio(config)

                rebalancing_out = project_root / "output" / "portfolio" / "rebalancing_analysis.json"
                rebalancing_out.parent.mkdir(parents=True, exist_ok=True)
                rebalancing_out.write_text(rebalancing_result.model_dump_json(indent=2), encoding="utf-8")

        except Exception as e:
            logger.warning(f"Rebalancing analysis failed: {e}")
            rebalancing_result = None

    return out, rebalancing_result.model_dump() if rebalancing_result else None


async def run(flow_state: Any | None = None) -> Path:
    """Run standard portfolio review process with parallel holdings processing."""
    etf_csv, stock_csv, crypto_csv = get_csv_paths()

    logger.info("Running portfolio review with parallel holdings processor")
    review, summary = await build_portfolio_review(
        stock_csv=stock_csv,
        etf_csv=etf_csv,
        crypto_csv=crypto_csv,
        flow_state=flow_state,
    )

    logger.info(f"Holdings processed: {len(review.holdings)} decisions from {summary.total_holdings} CSV entries")
    logger.info(f"By asset class: {summary.by_asset_class}")

    project_root = Path(__file__).resolve().parents[3]
    out = project_root / "output" / "portfolio" / "portfolio_review.json"
    save_review_json(review, out, summary)

    return out


__all__ = [
    "build_portfolio_review",
    "get_csv_paths",
    "get_thresholds",
    "run",
    "run_with_rebalancing",
    "save_review_json",
]
