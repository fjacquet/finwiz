"""Merge deep analysis results from Flow state into HoldingDecision objects."""

from __future__ import annotations

import logging
from typing import Any

from finwiz.schemas.portfolio_review import Alternative, HoldingDecision
from finwiz.scoring.grading_system import score_to_grade

logger = logging.getLogger(__name__)


def merge_deep_analysis_from_flow_state(
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
            else:
                # No deep analysis ran for this holding (failure, timeout, or
                # global abort). The placeholder grade="D" / score=0.6 from
                # decisions.py would otherwise reach the report as if it were a
                # real verdict — that's the bug that caused the DELL panic.
                # Mark explicitly as N/A so the renderer can show "Analyse en
                # attente" instead of a fake D badge.
                decision.grade = "N/A"
                # Reset the placeholder composite_score=0.6 from decisions.py
                # — that's the EXACT field that caused the DELL panic. Other
                # consumers (sorts, JSON exports, future analytics) must not
                # see a fabricated 0.6 as if it were a real signal.
                decision.composite_score = 0.0
                decision.grade_description = "Analyse approfondie non disponible"
                decision.recommended_action = "Analyse en attente — ne pas décider sur ce holding"
                decision.rationale_bullets = [
                    "Analyse approfondie non disponible pour ce holding lors de cette exécution.",
                    "Aucun verdict d'investissement n'est rendu — relancer l'analyse pour obtenir un grade.",
                ]
                decision.data_freshness = "stale"
                # crew_analysis_used / analysis_date stay None — already the
                # canonical "did deep analysis run?" indicator used by counts
                # and renderers.
                logger.debug(f"Marked {ticker} as N/A (no deep analysis result)")

            if ticker in portfolio_alternatives:
                alternatives_data = portfolio_alternatives[ticker]

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
