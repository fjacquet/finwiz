"""
Candidate scorer for newcomer discovery.

Scores and grades newcomer candidates by reusing existing scoring
infrastructure: ScreeningRanking for preliminary scores,
ScreeningCriteria for A+ filters, and score_to_grade for letter grades.
"""

from __future__ import annotations

from typing import Any

from finwiz.schemas.newcomer_discovery import NewcomerCandidate
from finwiz.scoring.grading_system import score_to_grade
from finwiz.tools.logger import get_logger
from finwiz.tools.screening_criteria import ScreeningCriteria
from finwiz.tools.screening_ranking import ScreeningRanking


class CandidateScorer:
    """Scores and grades newcomer candidates using existing scoring infrastructure."""

    def __init__(self) -> None:
        """Initialize with screening ranking and criteria instances."""
        self._logger = get_logger(__name__)
        self._screening_criteria = ScreeningCriteria()
        self._screening_ranking = ScreeningRanking()

    def score_and_grade(
        self,
        candidates: list[NewcomerCandidate],
    ) -> list[NewcomerCandidate]:
        """Score, grade, and sort candidates.

        For each candidate:
        1. Calculate a preliminary score via ScreeningRanking.
        2. Blend with existing source-specific composite_score (if non-default).
        3. Assign letter grade and recommendation via score_to_grade.
        4. Check A+ screening filter pass/fail.

        Args:
            candidates: List of NewcomerCandidate to score.

        Returns:
            Updated list sorted by composite_score descending.
        """
        for candidate in candidates:
            try:
                preliminary = self._calculate_score(candidate)
                grade_str, recommendation = self._assign_grade(preliminary)

                # Blend: preserve source signal if candidate has a non-default score
                if candidate.composite_score not in (0.0, 0.5):
                    final_score = 0.6 * preliminary + 0.4 * candidate.composite_score
                else:
                    final_score = preliminary

                final_score = max(0.0, min(1.0, final_score))

                # Re-grade on final blended score
                grade_str, recommendation = self._assign_grade(final_score)

                candidate.composite_score = final_score
                candidate.grade = grade_str
                candidate.recommendation = recommendation

                passes = self._passes_filters(candidate)
                if passes:
                    candidate.metadata["passes_a_plus_filters"] = True

            except Exception:
                self._logger.warning(
                    "Failed to score candidate %s, keeping original values",
                    candidate.ticker,
                    exc_info=True,
                )

        candidates.sort(key=lambda c: c.composite_score, reverse=True)
        return candidates

    def _build_market_data_dict(
        self,
        candidate: NewcomerCandidate,
    ) -> dict[str, Any]:
        """Convert candidate fields to the dict format expected by screening tools.

        Args:
            candidate: The NewcomerCandidate to convert.

        Returns:
            Dict matching the format expected by ScreeningRanking and ScreeningCriteria.
        """
        meta = candidate.metadata

        if candidate.asset_class == "stock":
            return {
                "market_cap": candidate.market_cap or 0,
                "roe": meta.get("roe", 0),
                "revenue_growth": meta.get("revenue_growth", 0),
                "debt_to_equity": meta.get("debt_to_equity", 0.5),
                "fcf_positive": meta.get("fcf_positive", False),
                "fcf_growing": meta.get("fcf_growing", False),
                "name": candidate.name,
            }
        if candidate.asset_class == "etf":
            return {
                "expense_ratio": meta.get("expense_ratio", 0.5),
                "aum": candidate.market_cap or 0,
                "tracking_error": meta.get("tracking_error", 0.01),
                "history_years": meta.get("history_years", 0),
                "name": candidate.name,
            }
        # crypto
        return {
            "market_cap": candidate.market_cap or 0,
            "daily_volume": meta.get("daily_volume", 0),
            "age_months": meta.get("age_months", 0),
            "institutional_adoption": meta.get("institutional_adoption", False),
            "real_utility": meta.get("real_utility", False),
            "name": candidate.name,
        }

    def _calculate_score(self, candidate: NewcomerCandidate) -> float:
        """Calculate preliminary score using ScreeningRanking.

        Args:
            candidate: The candidate to score.

        Returns:
            Float score between 0.0 and 1.0.
        """
        market_data = self._build_market_data_dict(candidate)
        return self._screening_ranking.calculate_preliminary_score(
            market_data,
            candidate.asset_class,
        )

    def _assign_grade(self, score: float) -> tuple[str, str]:
        """Assign letter grade and recommendation from score.

        Args:
            score: Composite score between 0.0 and 1.0.

        Returns:
            Tuple of (grade, action/recommendation).
        """
        grade_info = score_to_grade(score)
        return grade_info.grade, grade_info.action

    def _passes_filters(self, candidate: NewcomerCandidate) -> bool:
        """Check if candidate passes A+ screening criteria.

        Args:
            candidate: The candidate to check.

        Returns:
            True if passes all default screening filters for its asset class.
        """
        market_data = self._build_market_data_dict(candidate)
        criteria = ScreeningCriteria.get_default_criteria(candidate.asset_class)
        return ScreeningCriteria.passes_screening_filters(
            market_data,
            candidate.asset_class,
            criteria,
        )
