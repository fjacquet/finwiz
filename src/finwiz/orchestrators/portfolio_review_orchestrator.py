"""
Portfolio review orchestrator - Application/Service Layer.

This module contains business logic orchestration for portfolio review:
- Configuration and thresholds
- Holdings decision building (pure functions)
- Portfolio review building and execution
- Integration with rebalancing

HTML generation is delegated to the reporting layer (finwiz.reporting.python_report_generator).
"""

from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from finwiz.data.fx_rates import get_fx_rate
from finwiz.orchestrators.portfolio_holdings_processor import (
    PortfolioHoldingsProcessor,
    ProcessingSummary,
)
from finwiz.orchestrators.portfolio_review.merge import merge_deep_analysis_from_flow_state
from finwiz.schemas.portfolio_processing import RawHolding
from finwiz.schemas.portfolio_review import PortfolioReview
from finwiz.schemas.portfolio_valuation import ValuationResult
from finwiz.scoring.portfolio_valuation import value_holdings
from finwiz.tools.portfolio_price_service import PortfolioPriceService

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


async def _value_portfolio(raw_holdings: list[RawHolding]) -> ValuationResult | None:
    """Pre-fetch prices and compute EUR weights. Best-effort: None on any failure.

    Short-circuits (no price service, no network) when no holding has a quantity.
    """
    tickers = list({h.ticker for h in raw_holdings if h.quantity is not None})
    if not tickers:
        return None

    try:
        service = PortfolioPriceService()
        prices = await service.get_current_prices(tickers)

        def price_fn(ticker: str) -> tuple[float, str] | None:
            pd = prices.get(ticker)
            if pd is None:
                return None
            return (pd.price, pd.currency)

        return value_holdings(
            raw_holdings,
            base="EUR",
            price_fn=price_fn,
            fx_fn=get_fx_rate,
        )
    except Exception as exc:  # never break the review over valuation
        logger.warning("Portfolio valuation failed; weights unavailable this run: %s", exc)
        return None


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

    total_value_eur: float | None = None
    valuation = await _value_portfolio(raw_holdings)
    if valuation is not None:
        total_value_eur = valuation.total_value_eur
        # per_ticker is keyed by ticker (value_holdings collapses same-ticker
        # holdings last-wins, see test_duplicate_ticker_collapses_last_wins), and
        # total_value_eur is derived from that single-count map — so the portfolio
        # total is never double-counted. The data CSVs hold unique tickers; if two
        # rows ever shared a ticker, both decisions would be stamped with the same
        # (collapsed) weight here. Acceptable given the deliberate collapse semantics.
        for decision in decisions:
            hv = valuation.per_ticker.get(decision.ticker)
            if hv is None:
                continue
            decision.quantity = hv.quantity
            decision.native_currency = hv.native_currency
            decision.native_value = hv.native_value
            decision.eur_value = hv.eur_value
            decision.weight = hv.weight
        logger.info("Valuation coverage: %s", valuation.coverage_note)

    review = PortfolioReview(
        as_of=datetime.now(UTC),
        base_currency=base_currency,
        holdings=decisions,
        total_value_eur=total_value_eur,
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
            json.dump(summary_data, f, indent=2, default=str)
        logger.info(f"Saved processing summary to {summary_path}")

    out_path.write_text(json.dumps(output_data, indent=2, default=str), encoding="utf-8")


# =============================================================================
# Main Execution Functions
# =============================================================================


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
    "save_review_json",
]
