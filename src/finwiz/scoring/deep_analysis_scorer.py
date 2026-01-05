"""
Deep Analysis Scoring Engine.

Python-based scoring engine for deep analysis that replaces AI-based scoring
with deterministic, testable calculations. Provides composite scoring based on
fundamental, technical, and risk factors.

This module orchestrates component scorers and result builders.
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any, Literal, cast

from finwiz.flow_state import DeepAnalysisResult

if TYPE_CHECKING:
    from finwiz.validation.quality_metrics import DataQualityMetrics
from finwiz.scoring.crew_export_generator import CrewExportGenerator
from finwiz.scoring.fundamental_scorer import FundamentalScorer
from finwiz.scoring.risk_scorer import RiskScorer
from finwiz.scoring.score_result_builder import ScoreResultBuilder
from finwiz.scoring.technical_fallback import (
    calculate_missing_technical_indicators,
    get_price_history_from_data,
)
from finwiz.scoring.technical_scorer import TechnicalScorer
from finwiz.scoring.thresholds import ScoringThresholds, get_thresholds

logger = logging.getLogger(__name__)


class DeepAnalysisScorer:
    """
    Python-based scoring engine orchestrator for deep analysis.

    Coordinates component scorers to produce composite scores:
    - 40% fundamental analysis (via FundamentalScorer)
    - 30% technical analysis (via TechnicalScorer)
    - 30% risk assessment (via RiskScorer)

    Refactored to use composition pattern with focused scorers.
    """

    def __init__(self, thresholds: ScoringThresholds | None = None) -> None:
        """
        Initialize the scoring engine with component scorers.

        Args:
            thresholds: Optional custom thresholds (defaults to DEFAULT_THRESHOLDS)
        """
        self.logger = logger
        self._data_quality_metrics: DataQualityMetrics | None = None
        self._current_ticker: str | None = None

        # Scoring thresholds
        self.thresholds = thresholds or get_thresholds()

        # Initialize component scorers
        self.fundamental_scorer = FundamentalScorer(thresholds=self.thresholds)
        self.technical_scorer = TechnicalScorer(thresholds=self.thresholds)
        self.risk_scorer = RiskScorer(thresholds=self.thresholds)

        # Initialize result builders
        self.result_builder = ScoreResultBuilder(thresholds=self.thresholds)
        self.export_generator = CrewExportGenerator(thresholds=self.thresholds)

    def calculate_composite_score(self, ticker: str, asset_class: str, data: dict[str, Any]) -> DeepAnalysisResult:
        """
        Calculate composite score from fundamental, technical, and risk factors.

        Args:
            ticker: Asset ticker symbol
            asset_class: Asset class (stock, etf, crypto)
            data: Dictionary containing all analysis data

        Returns:
            DeepAnalysisResult with scores, grade, and recommendation

        Raises:
            CriticalFieldError: If critical fields are missing (fail fast)
        """
        from finwiz.config.critical_fields_config import CriticalFieldError

        try:
            # Step 1: Initialize tracking systems
            self._initialize_tracking(ticker, asset_class, data)

            # Step 2: Validate critical fields
            self._validate_critical_fields(ticker, asset_class, data)

            # Step 3: Calculate component scores
            scores = self._calculate_component_scores(asset_class, data)

            # Step 4: Compute weighted composite score
            composite_score = self._compute_weighted_score(scores)

            # Step 5: Build final result (delegate to ScoreResultBuilder)
            # After _initialize_tracking, data quality metrics is guaranteed to be set
            assert self._data_quality_metrics is not None
            return self.result_builder.build_result(
                ticker=ticker,
                asset_class=asset_class,
                composite_score=composite_score,
                scores=scores,
                data=data,
                data_quality_metrics=self._data_quality_metrics,
            )

        except CriticalFieldError as e:
            self.logger.error(
                f"❌ ANALYSIS FAILED for {ticker}: Missing critical fields {e.missing_fields}\n   This holding will be SKIPPED to avoid decisions based on assumptions."
            )
            raise
        except Exception as e:
            self.logger.error(f"Error calculating composite score for {ticker}: {e}")
            return self.result_builder.create_error_result(ticker, asset_class, str(e))

    def analyze_and_export(
        self,
        ticker: str,
        asset_class: str,
        collected_data: dict[str, Any],
        session_id: str = "default",
    ) -> tuple[DeepAnalysisResult, dict[str, Any]]:
        """
        Complete analysis pipeline: scoring + detailed analysis + crew export.

        This is the main entry point for the Python scoring approach.

        Args:
            ticker: Asset ticker symbol
            asset_class: Asset class (stock, etf, crypto)
            collected_data: Raw data from data collection task
            session_id: Session identifier for file paths

        Returns:
            Tuple of (DeepAnalysisResult, crew_export_dict)
        """
        start_time = time.time()

        try:
            # Step 1: Calculate scores using Python algorithms
            result = self.calculate_composite_score(ticker, asset_class, collected_data)

            # Step 2: Create comprehensive detailed analysis (delegate)
            detailed_analysis = self.export_generator.create_detailed_analysis(ticker, asset_class, collected_data, result)

            # Step 3: Create crew export dict (delegate)
            crew_export_dict = self.export_generator.create_crew_export(result, detailed_analysis, session_id)

            # Calculate performance metrics
            execution_time = time.time() - start_time

            self.logger.info(
                f"🚀 PYTHON SCORING PERFORMANCE for {ticker}:\n"
                f"  ✅ Execution time: {execution_time:.2f}s (target: 10-30s)\n"
                f"  ✅ LLM calls: 0 (target: 0)\n"
                f"  ✅ Cost: $0.00 (target: $0.00)\n"
                f"  ✅ Data preservation: ALL raw metrics preserved\n"
                f"  ✅ Deterministic: Same input = same output"
            )

            return result, crew_export_dict

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Error in analyze_and_export for {ticker}: {e}")

            error_result = self.result_builder.create_error_result(ticker, asset_class, str(e))
            error_detailed = {
                "error": str(e),
                "execution_time": execution_time,
                "ticker": ticker,
                "asset_class": asset_class,
            }
            error_export = self.export_generator.create_crew_export(error_result, error_detailed, session_id)

            return error_result, error_export

    def _initialize_tracking(self, ticker: str, asset_class: str, data: dict[str, Any]) -> None:
        """Initialize data quality tracking systems."""
        from finwiz.validation.quality_metrics import DataQualityMetrics

        self._data_quality_metrics = DataQualityMetrics()
        self._current_ticker = ticker

        expected_fields = self._get_expected_fields(asset_class)
        self._data_quality_metrics.set_expected_fields(expected_fields)
        self.logger.info(f"📋 Initialized data quality tracking for {ticker} ({asset_class}): expecting {len(expected_fields)} fields")

    def _validate_critical_fields(self, ticker: str, asset_class: str, data: dict[str, Any]) -> None:
        """Validate that all critical fields are present before scoring."""
        from finwiz.config.critical_fields_config import (
            CriticalFieldError,
            validate_critical_fields,
        )

        try:
            asset_class_literal = cast(Literal["stock", "etf", "crypto"], asset_class)
            validate_critical_fields(ticker, asset_class_literal, data)
            self.logger.info(f"✅ All critical fields present for {ticker}")
        except CriticalFieldError as e:
            self.logger.error(
                f"❌ CRITICAL FIELDS MISSING for {ticker}: {e.missing_fields}\n"
                f"   Cannot proceed with analysis - would be based on assumptions.\n"
                f"   Recommendation: Check API connectivity and data sources."
            )
            raise

    def _calculate_component_scores(self, asset_class: str, data: dict[str, Any]) -> dict[str, Any]:
        """Calculate fundamental, technical, and risk component scores."""
        # Calculate missing technical indicators as fallback
        price_history = get_price_history_from_data(data)
        data = calculate_missing_technical_indicators(data, price_history)

        # Calculate component scores (with data quality tracking)
        fundamental_score, fundamental_details = self.calculate_fundamental_score(asset_class, data)
        technical_score, technical_details = self.calculate_technical_score(data)
        risk_score, risk_details = self.calculate_risk_score(data)

        return {
            "fundamental_score": fundamental_score,
            "fundamental_details": fundamental_details,
            "technical_score": technical_score,
            "technical_details": technical_details,
            "risk_score": risk_score,
            "risk_details": risk_details,
        }

    def _compute_weighted_score(self, scores: dict[str, Any]) -> float:
        """
        Compute weighted composite score from component scores.

        Uses adaptive weights: high-quality companies get more weight on fundamentals.
        """
        fundamental_score = scores["fundamental_score"]
        fundamental_details = scores.get("fundamental_details", {})

        is_quality_company = self.result_builder.is_quality_company(fundamental_score, fundamental_details)

        # Adaptive weights based on company quality
        if is_quality_company:
            weight_fundamental = 0.50
            weight_technical = 0.25
            weight_risk = 0.25
            self.logger.info("✨ Quality company detected - using adaptive weights (50/25/25)")
        else:
            weight_fundamental = self.thresholds.weight_fundamental
            weight_technical = self.thresholds.weight_technical
            weight_risk = self.thresholds.weight_risk

        # Calculate weighted composite score
        composite_score = weight_fundamental * scores["fundamental_score"] + weight_technical * scores["technical_score"] + weight_risk * scores["risk_score"]

        # Store adaptive weights in scores for transparency
        scores["weights_used"] = {
            "fundamental": weight_fundamental,
            "technical": weight_technical,
            "risk": weight_risk,
            "is_quality_company": is_quality_company,
        }

        return float(composite_score)

    def calculate_fundamental_score(self, asset_class: str, data: dict[str, Any]) -> tuple[float, dict[str, Any]]:
        """
        Calculate fundamental score based on asset class.

        Delegates to FundamentalScorer component.
        """
        # Use empty string as fallback when ticker not set (should not happen in normal flow)
        ticker = self._current_ticker or ""
        self.fundamental_scorer.set_context(ticker, self._data_quality_metrics)
        return self.fundamental_scorer.calculate_fundamental_score(asset_class, data)

    def calculate_technical_score(self, data: dict[str, Any]) -> tuple[float, dict[str, Any]]:
        """
        Calculate technical score based on RSI, trend analysis, and momentum.

        Delegates to TechnicalScorer component.
        """
        if self._data_quality_metrics is not None:
            self.technical_scorer.set_data_quality_metrics(self._data_quality_metrics)
        return self.technical_scorer.calculate_technical_score(data)

    def calculate_risk_score(self, data: dict[str, Any]) -> tuple[float, dict[str, Any]]:
        """
        Calculate risk score (0-5 scale converted to 0-1, where 1 = low risk).

        Delegates to RiskScorer component.
        """
        if self._data_quality_metrics is not None:
            self.risk_scorer.set_data_quality_metrics(self._data_quality_metrics)
        return self.risk_scorer.calculate_risk_score(data)

    def _get_expected_fields(self, asset_class: str) -> list[str]:
        """Get list of expected fields based on asset class."""
        common_fields = ["current_price", "volatility", "max_drawdown", "beta", "rsi", "macd", "macd_signal"]

        if asset_class == "stock":
            return common_fields + ["roe", "debt_to_equity", "revenue_growth", "profit_margin"]
        elif asset_class == "etf":
            return common_fields + ["expense_ratio", "tracking_error", "aum"]
        elif asset_class == "crypto":
            return common_fields + ["market_cap", "volume_24h", "age_years"]
        return common_fields

    # Legacy method delegation for backward compatibility
    def assign_grade(self, composite_score: float) -> str:
        """Assign letter grade based on composite score. Delegates to ScoreResultBuilder."""
        return self.result_builder.assign_grade(composite_score)

    def generate_recommendation(self, composite_score: float, grade: str) -> str:
        """Generate investment recommendation. Delegates to ScoreResultBuilder."""
        return self.result_builder.generate_recommendation(composite_score, grade)

    def generate_rationale(
        self,
        ticker: str,
        asset_class: str,
        composite_score: float,
        grade: str,
        fundamental_details: dict[str, Any],
        technical_details: dict[str, Any],
        risk_details: dict[str, Any],
    ) -> str:
        """Generate template-based rationale. Delegates to ScoreResultBuilder."""
        return self.result_builder.generate_rationale(ticker, asset_class, composite_score, grade, fundamental_details, technical_details, risk_details)

    def create_detailed_analysis(
        self,
        ticker: str,
        asset_class: str,
        data: dict[str, Any],
        result: DeepAnalysisResult,
    ) -> dict[str, Any]:
        """Create comprehensive detailed_analysis dict. Delegates to CrewExportGenerator."""
        return self.export_generator.create_detailed_analysis(ticker, asset_class, data, result)

    def create_crew_export(
        self,
        result: DeepAnalysisResult,
        detailed_analysis: dict[str, Any],
        session_id: str = "default",
    ) -> dict[str, Any]:
        """Create DeepAnalysisCrewExport dict. Delegates to CrewExportGenerator."""
        return self.export_generator.create_crew_export(result, detailed_analysis, session_id)
