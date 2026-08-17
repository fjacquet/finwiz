"""
Deep Analysis Pipeline - Functional Programming Approach.

Pure functions with composition for per-holding analysis.
Combines Python quantitative scoring ($0) with AI qualitative insights.

Architecture:
    1. collect_raw_data(ctx) -> RawData         [Python tools]
    2. calculate_quantitative(ctx, raw) -> Quant   [$0 Python]
    3. generate_qualitative(ctx, quant) -> Qual    [AI crew]
    4. synthesize(ctx, quant, qual) -> Enriched    [Python]
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from finwiz.analysis._helpers import (
    _get_analysis_crew,  # noqa: F401 — re-exported for test compatibility
)
from finwiz.analysis.stages import run_pipeline
from finwiz.analysis.stages._qualify_fallbacks import _create_fallback_qualitative  # noqa: F401 — re-exported for callers/tests
from finwiz.analysis.stages._synthesize_helpers import (  # noqa: F401
    _calculate_word_count,
    _count_unique_insights,
    _generate_executive_summary,
    _get_confidence,
    _get_investment_rationale,
)
from finwiz.analysis.stages.collect import collect_raw_data  # noqa: F401 — re-exported for callers/tests
from finwiz.analysis.stages.emit import build_verdict  # noqa: F401
from finwiz.analysis.stages.qualify import (  # noqa: F401
    _create_python_qualitative,
    _extract_qualitative,
    _has_qualitative_content,
    _safe_strategic,
    generate_qualitative,
)
from finwiz.analysis.stages.quantify import _result_to_quantitative, calculate_quantitative  # noqa: F401
from finwiz.analysis.stages.synthesize import (  # noqa: F401
    _apply_strategic_recompute,
    _bs_nd2,
    _compute_options_probabilities,
    _compute_scenario_probabilities,
    _synthesize_recommendation,
    synthesize_enriched_analysis,
)
from finwiz.flow_state_models import DeepAnalysisResult
from finwiz.schemas.hybrid_analysis import (
    EnrichedAnalysis,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AnalysisContext:
    """Immutable context for analysis pipeline."""

    ticker: str
    asset_class: str
    company_name: str = ""
    # Optional ledger and run_id — populated by DeepAnalysisOrchestrator (D6).
    # Legacy callers that construct AnalysisContext without these fields still work;
    # run_pipeline falls back to creating an ad-hoc in-memory ledger.
    ledger: Any = None
    run_id: str | None = None


# === COMPOSED PIPELINE (Main Entry Point) ===
def analyze_holding(
    ticker: str,
    asset_class: str,
    company_name: str = "",
    prefetched_data: dict[str, Any] | None = None,
    ledger: Any = None,
    run_id: str | None = None,
) -> tuple[DeepAnalysisResult, EnrichedAnalysis]:
    """Backwards-compatible facade calling the new pipeline.

    All orchestration lives in `finwiz.analysis.stages.run_pipeline`. This
    facade is preserved for existing callers (tests, orchestrators) that
    import `analyze_holding` from this module.

    Args:
        ticker: Ticker symbol to analyze.
        asset_class: Asset class (stock, etf, crypto).
        company_name: Optional company name for display.
        prefetched_data: Optional pre-fetched raw data (batch prefetch path).
        ledger: Optional RunLedger from the orchestrator (D6). When supplied,
            stage results are recorded into the shared ledger instead of a
            per-call in-memory ledger. Legacy callers omit this parameter.
        run_id: Optional run identifier to match the orchestrator's ledger.
    """
    ctx = AnalysisContext(ticker=ticker, asset_class=asset_class, company_name=company_name, ledger=ledger, run_id=run_id)
    return run_pipeline(ctx, prefetched_data=prefetched_data)
