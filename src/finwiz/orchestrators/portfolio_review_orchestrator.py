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

from finwiz.infrastructure.caching.manager import get_cache_manager
from finwiz.orchestrators.portfolio_holdings_processor import (
    PortfolioHoldingsProcessor,
    ProcessingSummary,
)
from finwiz.reporting.portfolio_review_html import (
    add_portfolio_review_sections,
    add_rebalancing_sections,
)
from finwiz.schemas.common import RiskAssessmentStandardized
from finwiz.schemas.portfolio_processing import AssetClass, RawHolding
from finwiz.schemas.portfolio_review import (
    HoldingDecision,
    PortfolioReview,
)
from finwiz.scoring.grading_system import score_to_grade

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
# Decision Building Helpers (pure functions - Domain Logic)
# =============================================================================


def calculate_score(is_valid: bool, asset_class: AssetClass) -> float:
    """
    Calculate composite score for a holding using shallow validation.

    Args:
        is_valid: Whether the holding passed validation
        asset_class: Type of asset

    Returns:
        Composite score between 0.0 and 1.0

    """
    if not is_valid:
        return 0.3  # Invalid holdings get low score

    # Base score for validated holdings (B grade = 75%)
    base = 0.75

    # ETFs get slight boost for diversification
    if asset_class == "etf":
        base += 0.05

    return min(base, 1.0)


def assess_risk(is_valid: bool, validation_result: dict[str, Any]) -> RiskAssessmentStandardized:
    """Assess risk for a holding based on validation result."""
    if is_valid:
        return RiskAssessmentStandardized(
            score=2.0,
            level="Medium",
            risk_factors=["Baseline risk - ticker validated"],
        )

    reason = validation_result.get("reason", "Unknown validation failure")
    return RiskAssessmentStandardized(
        score=4.5,
        level="Very High",
        risk_factors=[
            "Validation failed",
            f"Reason: {reason}",
            "Unable to verify ticker existence",
        ],
    )


def build_rationale(
    is_valid: bool,
    validation_result: dict[str, Any],
    holding: RawHolding,
) -> list[str]:
    """Build rationale bullets for a holding decision."""
    rationale: list[str] = []

    rationale.append("⚡ Validation rapide (analyse superficielle)")
    rationale.append("💡 Activez DEEP_PORTFOLIO_ANALYSIS=true pour une analyse complète")

    if is_valid:
        rationale.append("✅ Ticker validé avec succès")
        source = validation_result.get("meta", {}).get("source", "unknown")
        rationale.append(f"Source de données: {source}")
        rationale.append("📊 Note basée sur la validation du ticker uniquement")
        rationale.append("🔍 L'analyse approfondie fournira des métriques détaillées")
    else:
        rationale.append("⚠️ Échec de la validation du ticker")
        reason = validation_result.get("reason", "Unknown reason")
        rationale.append(f"Problème de validation: {reason}")
        rationale.append("📋 Inclus dans le rapport pour transparence")
        rationale.append("🔧 Révision manuelle requise")

    rationale.append(f"📁 Source: {Path(holding.source_file).name}, ligne {holding.line_number}")

    return rationale


def build_citations(validation_result: dict[str, Any]) -> list[str]:
    """Build citations list from validation result."""
    citations: list[str] = []

    source = validation_result.get("meta", {}).get("source")
    if source == "yahoo":
        citations.append("Yahoo Finance")
    elif source == "coinbase":
        citations.append("Coinbase Products API")

    return citations


def create_error_decision(
    holding: RawHolding,
    base_currency: str,
    error_message: str,
) -> HoldingDecision:
    """Create a minimal decision for a holding that failed to process."""
    grade_info = score_to_grade(0.0)

    return HoldingDecision(
        asset_class=holding.asset_class,
        name=holding.name,
        ticker=holding.ticker,
        currency=holding.currency or base_currency,
        decision="SELL",
        composite_score=0.0,
        grade=grade_info.grade,
        grade_description="Processing Error",
        recommended_action="Review manually",
        risk=RiskAssessmentStandardized(
            score=5.0,
            level="Very High",
            risk_factors=["Processing error", error_message],
        ),
        rationale_bullets=[
            "❌ Failed to process holding",
            f"Error: {error_message}",
            "Manual review required",
        ],
        citations=[],
        alternatives=[],
        data_freshness="stale",
    )


# =============================================================================
# Flow State Integration
# =============================================================================


def _merge_deep_analysis_from_flow_state(
    decisions: list[HoldingDecision],
    flow_state: Any,
) -> list[HoldingDecision]:
    """Merge deep analysis results from Flow state into HoldingDecision objects."""
    try:
        deep_analysis_results = getattr(flow_state, "deep_analysis_results", {})
        portfolio_alternatives = getattr(flow_state, "portfolio_alternatives", {})

        if not deep_analysis_results:
            logger.info("No deep analysis results available in Flow state")
            return decisions

        holdings_with_deep_analysis = 0
        holdings_with_alternatives = 0

        for decision in decisions:
            ticker = decision.ticker

            if ticker in deep_analysis_results:
                deep_result = deep_analysis_results[ticker]

                decision.crew_analysis_used = deep_result.crew_name
                decision.analysis_date = deep_result.analyzed_at
                decision.composite_score = deep_result.composite_score
                decision.grade = deep_result.grade

                grade_info = score_to_grade(deep_result.composite_score)
                decision.grade_description = grade_info.description
                decision.recommended_action = grade_info.action

                decision.data_freshness = "fresh" if not deep_result.cached else "recent"

                holdings_with_deep_analysis += 1
                logger.debug(f"Merged deep analysis for {ticker}: grade={deep_result.grade}")

            if ticker in portfolio_alternatives:
                alternatives_data = portfolio_alternatives[ticker]

                from finwiz.schemas.portfolio_review import Alternative

                alternatives = []
                for alt_dict in alternatives_data:
                    try:
                        alternative = Alternative.model_validate(alt_dict)
                        alternatives.append(alternative)
                    except Exception as e:
                        logger.warning(f"Failed to validate alternative for {ticker}: {e}")
                        continue

                if alternatives:
                    decision.alternatives = alternatives[:3]
                    decision.has_a_plus_opportunities = True
                    holdings_with_alternatives += 1
                    logger.debug(f"Added {len(alternatives)} alternatives for {ticker}")

        logger.info(f"Deep analysis merge complete: {holdings_with_deep_analysis} with deep analysis, {holdings_with_alternatives} with alternatives")

        return decisions

    except Exception as e:
        logger.error(f"Error merging deep analysis from Flow state: {e}", exc_info=True)
        return decisions


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
        decisions = _merge_deep_analysis_from_flow_state(decisions, flow_state)

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

    out_path.write_text(json.dumps(output_data, indent=2), encoding="utf-8")


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


# =============================================================================
# Enhanced Orchestrator Class
# =============================================================================


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
                result: dict[str, Any] = cached_result
                return result

        review_path, rebalancing_result = await run_with_rebalancing(
            target_weights=target_weights,
            available_capital=available_capital,
            include_rebalancing=target_weights is not None,
        )

        review_data = json.loads(Path(review_path).read_text(encoding="utf-8"))

        comprehensive_result = {
            "portfolio_review": review_data,
            "rebalancing_analysis": rebalancing_result,
            "analysis_timestamp": datetime.now(UTC).isoformat(),
            "has_rebalancing_recommendations": rebalancing_result is not None,
        }

        if enable_caching:
            await self.cache_manager.set(cache_key, comprehensive_result, ttl=1800)

        return comprehensive_result

    async def generate_unified_report(
        self,
        analysis_result: dict[str, Any],
        language: str = "en",
    ) -> str:
        """Generate unified HTML report combining portfolio review and rebalancing."""
        from finwiz.tools.html_report_generator import HTMLReportGenerator

        generator = HTMLReportGenerator()

        add_portfolio_review_sections(generator, analysis_result["portfolio_review"])

        if analysis_result["rebalancing_analysis"]:
            add_rebalancing_sections(generator, analysis_result["rebalancing_analysis"])

        title = f"Comprehensive Portfolio Analysis - {datetime.now().strftime('%Y-%m-%d')}"

        if hasattr(generator, "generate_unified_html"):
            return generator.generate_unified_html(title=title, language=language)
        else:
            return generator.generate_html_fallback(title=title, language=language)


# =============================================================================
# Public API Exports
# =============================================================================

__all__ = [
    # Configuration
    "get_csv_paths",
    "get_thresholds",
    # Decision builders (domain logic)
    "calculate_score",
    "assess_risk",
    "build_rationale",
    "build_citations",
    "create_error_decision",
    # Core functions
    "build_portfolio_review",
    "save_review_json",
    "run",
    "run_with_rebalancing",
    # Orchestrator
    "EnhancedPortfolioReviewOrchestrator",
    # Re-export from reporting layer for convenience
    "add_portfolio_review_sections",
    "add_rebalancing_sections",
]
