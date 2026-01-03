"""
Deep Analysis Data Merger for FinWiz.

This module provides the DeepAnalysisDataMerger component that properly merges
deep analysis results into portfolio holdings with strict validation.

CRITICAL: This component fixes the data consumption gap where expensive crew
analysis is generated but not consumed, resulting in fallback Grade D values.
"""

from typing import cast

from finwiz.flow_state import DeepAnalysisResult
from finwiz.schemas.common import RiskLevel
from finwiz.schemas.portfolio_review import Grade, HoldingDecision
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class DataMergeError(Exception):
    """Raised when data merge fails or data is missing/corrupted."""

    pass


class DeepAnalysisDataMerger:
    """
    Properly merge deep analysis results into portfolio holdings.

    CRITICAL: This component fixes the data consumption gap where crews generate
    rich analysis data but it's not being consumed by the portfolio review.
    """

    def __init__(self) -> None:
        """Initialize the DeepAnalysisDataMerger."""
        self.logger = get_logger(__name__)

    def merge_deep_analysis_into_holdings(
        self,
        holdings: list[HoldingDecision],
        deep_analysis_results: dict[str, DeepAnalysisResult],
        alternatives_data: dict[str, list[dict]] | None = None,
    ) -> list[HoldingDecision]:
        """
        Merge deep analysis data into holdings with strict validation.

        Args:
            holdings: Portfolio holdings with fallback grades
            deep_analysis_results: Actual deep analysis from crews
            alternatives_data: Optional alternatives data keyed by ticker

        Returns:
            Holdings with actual analysis data merged

        Raises:
            DataMergeError: If merge fails or data is missing

        """
        if not deep_analysis_results:
            raise DataMergeError("No deep analysis results provided. Cannot merge - would result in fallback data.")

        merged_holdings = []
        merge_stats = {
            "total": len(holdings),
            "merged": 0,
            "failed": 0,
            "missing_analysis": [],
            "alternatives_merged": 0,
        }

        for holding in holdings:
            ticker = holding.ticker

            # CRITICAL: Check if we have actual analysis
            if ticker not in deep_analysis_results:
                merge_stats["missing_analysis"].append(ticker)
                self.logger.error(f"No deep analysis found for {ticker}. Available tickers: {list(deep_analysis_results.keys())}")
                continue

            analysis = deep_analysis_results[ticker]

            # CRITICAL: Validate analysis has real data, not defaults
            if self._is_fallback_data(analysis):
                raise DataMergeError(f"Deep analysis for {ticker} contains fallback data. Grade: {analysis.grade}, Score: {analysis.composite_score}")

            # Get alternatives for this ticker if available
            ticker_alternatives = None
            if alternatives_data and ticker in alternatives_data:
                ticker_alternatives = alternatives_data[ticker]

            # Merge actual analysis data (including alternatives)
            merged_holding = self._merge_holding_with_analysis(holding, analysis, ticker_alternatives)

            # Verify merge succeeded
            if not self._verify_merge(merged_holding, analysis):
                raise DataMergeError(f"Merge verification failed for {ticker}. Expected grade {analysis.grade}, got {merged_holding.grade}")

            merged_holdings.append(merged_holding)
            merge_stats["merged"] += 1

            # Track alternatives merge
            if ticker_alternatives:
                merge_stats["alternatives_merged"] += 1
                self.logger.info(f"✅ Merged {ticker}: Grade {analysis.grade}, Score {analysis.composite_score:.2f}, Alternatives: {len(ticker_alternatives)}")
            else:
                self.logger.info(f"✅ Merged {ticker}: Grade {analysis.grade}, Score {analysis.composite_score:.2f}")

        # CRITICAL: Fail if any holdings couldn't be merged
        missing_analysis = merge_stats["missing_analysis"]
        if isinstance(missing_analysis, list) and missing_analysis:
            raise DataMergeError(f"Failed to merge {len(missing_analysis)} holdings: {missing_analysis}")

        self.logger.info(
            f"Deep analysis merge complete: {merge_stats['merged']}/{merge_stats['total']} "
            f"holdings successfully merged with actual analysis data, "
            f"{merge_stats['alternatives_merged']} holdings with alternatives"
        )

        return merged_holdings

    def _is_fallback_data(self, analysis: DeepAnalysisResult) -> bool:
        """
        Check if analysis contains fallback data.

        Fallback pattern: Grade D + score 0.6 + "Validation rapide" in rationale

        Args:
            analysis: Deep analysis result to check

        Returns:
            True if analysis contains fallback data, False otherwise

        """
        # Grade D with score 0.6 is the fallback pattern
        # Note: DeepAnalysisResult doesn't have rationale_bullets, so we check grade and score only
        is_fallback = analysis.grade == "D" and analysis.composite_score == 0.6

        if is_fallback:
            self.logger.warning(f"Detected fallback data pattern for {analysis.ticker}: Grade D, Score 0.6")

        return is_fallback

    def _merge_holding_with_analysis(
        self,
        holding: HoldingDecision,
        analysis: DeepAnalysisResult,
        alternatives: list[dict] | None = None,
    ) -> HoldingDecision:
        """
        Merge analysis data into holding.

        Args:
            holding: Original holding decision
            analysis: Deep analysis result to merge
            alternatives: Optional list of alternative holdings (as dicts)

        Returns:
            New HoldingDecision with merged data

        """
        from finwiz.schemas.portfolio_review import Alternative

        # Create new holding with analysis data
        merged = holding.model_copy(deep=True)

        # CRITICAL: Replace fallback data with actual analysis
        merged.grade = cast(Grade, analysis.grade)
        merged.composite_score = analysis.composite_score

        # Update grade description and recommended action based on new grade
        merged.grade_description = self._get_grade_description(analysis.grade)
        merged.recommended_action = self._get_recommended_action(analysis.grade)

        # Update risk assessment if available
        if hasattr(analysis, "risk_score") and analysis.risk_score is not None:
            # Update risk score in the risk assessment
            merged.risk.score = analysis.risk_score
            merged.risk.level = self._risk_score_to_level(analysis.risk_score)

        # Mark as using deep analysis
        merged.crew_analysis_used = analysis.crew_name
        if hasattr(analysis, "analyzed_at"):
            from datetime import datetime

            try:
                merged.analysis_date = datetime.fromisoformat(analysis.analyzed_at)
            except (ValueError, AttributeError):
                merged.analysis_date = datetime.now()

        # CRITICAL: Merge alternatives from deep analysis
        if alternatives:
            try:
                # Convert alternative dicts to Alternative Pydantic models
                alternative_models = []
                for alt_dict in alternatives:
                    try:
                        alt_model = Alternative.model_validate(alt_dict)
                        alternative_models.append(alt_model)
                    except Exception as e:
                        alt_ticker = alt_dict.get("ticker", "UNKNOWN")
                        self.logger.warning(f"Failed to validate alternative {alt_ticker} for {holding.ticker}: {e}")
                        continue

                if alternative_models:
                    merged.alternatives = alternative_models
                    self.logger.info(f"Merged {len(alternative_models)} alternatives into {holding.ticker}")
                else:
                    self.logger.warning(f"No valid alternatives could be merged for {holding.ticker} (validation failed for all {len(alternatives)} alternatives)")

            except Exception as e:
                self.logger.error(
                    f"Error merging alternatives for {holding.ticker}: {e}",
                    exc_info=True,
                )
                # Continue without alternatives rather than failing the entire merge
        else:
            # Log when no alternatives are available for underperforming holdings
            if analysis.grade in ["C", "D", "F"]:
                self.logger.info(f"No alternatives available for {holding.ticker} (grade: {analysis.grade}). Consider running with --discovery flag to find A+ alternatives.")

        # Note: HoldingDecision doesn't have has_deep_analysis field in the schema
        # but we set crew_analysis_used which indicates deep analysis was performed

        return merged

    def _verify_merge(self, merged: HoldingDecision, analysis: DeepAnalysisResult) -> bool:
        """
        Verify merge succeeded.

        Args:
            merged: Merged holding decision
            analysis: Original deep analysis result

        Returns:
            True if merge succeeded, False otherwise

        """
        return merged.grade == analysis.grade and merged.composite_score == analysis.composite_score and merged.crew_analysis_used == analysis.crew_name

    def _get_grade_description(self, grade: str) -> str:
        """
        Get human-readable grade description.

        Args:
            grade: Letter grade (A+ to F)

        Returns:
            Human-readable description

        """
        descriptions = {
            "A+": "Excellent - Top tier investment",
            "A": "Very Good - Strong investment",
            "B+": "Good - Above average investment",
            "B": "Good - Solid investment",
            "C+": "Fair - Average investment",
            "C": "Fair - Below average investment",
            "D": "Poor - Underperforming investment",
            "F": "Very Poor - Failing investment",
        }
        return descriptions.get(grade, "Unknown grade")

    def _get_recommended_action(self, grade: str) -> str:
        """
        Get recommended action based on grade.

        Args:
            grade: Letter grade (A+ to F)

        Returns:
            Recommended action

        """
        if grade in ["A+", "A"]:
            return "KEEP - Strong performer"
        elif grade in ["B+", "B"]:
            return "KEEP - Solid performer"
        elif grade in ["C+", "C"]:
            return "REVIEW - Consider alternatives"
        else:  # D, F
            return "SELL - Replace with better alternative"

    def _risk_score_to_level(self, score: float) -> RiskLevel:
        """
        Convert risk score (0-5) to risk level.

        Args:
            score: Risk score (0-5 scale)

        Returns:
            Risk level (Low, Medium, High, Very High)

        """
        if score <= 1.5:
            return "Low"
        elif score <= 2.5:
            return "Medium"
        elif score <= 3.5:
            return "High"
        else:
            return "Very High"
