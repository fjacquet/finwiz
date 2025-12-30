"""Hybrid Analysis Flow for Python/AI Integration.

This module implements the CrewAI Flow for coordinating Python-based quantitative
analysis with AI-generated qualitative insights.

Refactored to delegate to:
- HybridDataCollector: Multi-source data collection
- HybridAnalysisSynthesizer: Result synthesis
"""

from __future__ import annotations

import copy
import logging
import time
from datetime import datetime
from typing import Any

from crewai.flow.flow import Flow, listen, start
from pydantic import BaseModel, Field

from finwiz.flows.hybrid_analysis_synthesizer import HybridAnalysisSynthesizer
from finwiz.flows.hybrid_data_collector import HybridDataCollector
from finwiz.schemas.hybrid_analysis import (
    EnrichedAnalysis,
    QuantitativeAnalysis,
)
from finwiz.scoring.deep_analysis_scorer import DeepAnalysisScorer

logger = logging.getLogger(__name__)


class HybridAnalysisState(BaseModel):
    """Structured state for hybrid analysis flow."""

    ticker: str = ""
    asset_class: str = ""
    company_name: str = ""
    raw_data: dict[str, Any] = Field(default_factory=dict)
    quantitative_analysis: dict[str, Any] = Field(default_factory=dict)
    qualitative_insights: dict[str, Any] = Field(default_factory=dict)
    processing_start: float = 0.0
    deep_analysis_success: bool = False
    deep_analysis_error: str | None = None


class HybridAnalysisFlow(Flow[HybridAnalysisState]):
    """Flow for hybrid Python/AI analysis."""

    def __init__(self):
        """Initialize the hybrid analysis flow with component delegates."""
        super().__init__()
        self.scorer = DeepAnalysisScorer()
        self.data_collector = HybridDataCollector()
        self.synthesizer = HybridAnalysisSynthesizer()
        logger.info("HybridAnalysisFlow initialized with delegated components")

    @start()
    def collect_data(self) -> dict[str, Any]:
        """
        Collect raw data using Python tools.

        Returns:
            Dict containing ticker, asset_class, raw_data, and collection_timestamp.
        """
        ticker = self.state.ticker
        asset_class = self.state.asset_class
        company_name = self.state.company_name

        logger.info(f"Starting data collection for {ticker} ({asset_class})")
        self.state.processing_start = time.time()

        # Delegate to HybridDataCollector
        raw_data = self.data_collector.collect_raw_data(
            ticker=ticker,
            asset_class=asset_class,
            existing_data=self.state.raw_data if self.state.raw_data else None,
        )

        self.state.raw_data = raw_data
        logger.info(f"Data collection complete for {ticker}")

        return {
            "ticker": ticker,
            "asset_class": asset_class,
            "company_name": company_name,
            "raw_data": raw_data,
            "collection_timestamp": datetime.now().isoformat(),
        }

    @listen(collect_data)
    def calculate_quantitative_metrics(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Calculate quantitative metrics using Python.

        Args:
            data: Data from collect_data containing ticker, asset_class, and raw_data

        Returns:
            Dict containing all upstream data plus quantitative_analysis.
        """
        ticker = data["ticker"]
        asset_class = data["asset_class"]
        raw_data = data["raw_data"]

        logger.info(f"Starting quantitative analysis for {ticker}")

        try:
            deep_result = self.scorer.calculate_composite_score(
                ticker=ticker, asset_class=asset_class, data=raw_data
            )

            quant_analysis = self._convert_to_quantitative_analysis(deep_result, ticker, asset_class)
            self.state.quantitative_analysis = quant_analysis.model_dump()

            logger.info(
                f"Quantitative analysis complete for {ticker}: "
                f"Grade {quant_analysis.grade}, Score {quant_analysis.composite_score:.2f}"
            )

            return {
                **data,
                "quantitative_analysis": quant_analysis.model_dump(),
                "calculation_timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Quantitative analysis failed for {ticker}: {e}")
            self.state.deep_analysis_success = False
            self.state.deep_analysis_error = str(e)
            raise

    def _convert_to_quantitative_analysis(
        self, deep_result: Any, ticker: str, asset_class: str
    ) -> QuantitativeAnalysis:
        """Convert DeepAnalysisResult to QuantitativeAnalysis schema."""
        from finwiz.schemas.hybrid_analysis.metadata import DataLineage, DataQualityMetrics

        data_quality = DataQualityMetrics(
            completeness_score=0.9,
            freshness_score=0.95,
            accuracy_confidence=0.85,
            source_reliability=0.9,
            missing_fields=[],
        )

        data_lineage = DataLineage(
            primary_sources=["deep_analysis_scorer", "yahoo_finance"],
            collection_timestamp=datetime.now(),
            transformation_steps=["calculate_composite_score"],
            cache_status="fresh",
        )

        return QuantitativeAnalysis(
            composite_score=deep_result.composite_score,
            fundamental_score=deep_result.fundamental_score or 0.0,
            technical_score=deep_result.technical_score or 0.0,
            risk_score=deep_result.risk_score or 0.0,
            grade=deep_result.grade,
            preliminary_recommendation=deep_result.recommendation,
            fundamental_metrics=deep_result.fundamental_details or {},
            technical_indicators=deep_result.technical_details or {},
            risk_metrics=deep_result.risk_details or {},
            calculation_timestamp=datetime.now(),
            data_quality=data_quality,
            data_lineage=data_lineage,
            confidence_level=deep_result.confidence_level or 0.85,
            python_rationale=deep_result.rationale or "Python-generated analysis",
        )

    @listen(calculate_quantitative_metrics)
    def analyze_qualitative_insights(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Generate qualitative insights using AI crew.

        Args:
            data: Data from calculate_quantitative_metrics

        Returns:
            Dict containing all upstream data plus qualitative_insights.
        """
        from finwiz.validation.ai_output_validator import (
            AIOutputError,
            validate_ai_output_with_retry,
        )

        ticker = data["ticker"]
        asset_class = data["asset_class"]
        quant_analysis = data["quantitative_analysis"]

        logger.info(f"Starting qualitative analysis for {ticker}")
        quantitative = QuantitativeAnalysis(**quant_analysis)

        try:
            crew_inputs = {
                "ticker": ticker,
                "asset_class": asset_class,
                "company_name": data.get("company_name", ""),
                "quantitative_analysis": copy.deepcopy(quant_analysis),
                "grade": quant_analysis["grade"],
                "score": quant_analysis["composite_score"],
                "preliminary_recommendation": quant_analysis["preliminary_recommendation"],
            }

            def retry_with_extraction(format_instructions: str, retry_context: str) -> Any:
                """Retry crew execution and extract raw output."""
                logger.info(f"Retrying crew execution with format instructions for {ticker}")
                retry_inputs = {
                    **crew_inputs,
                    "format_instructions": format_instructions,
                    "retry_context": retry_context,
                }
                crew_result = self._execute_crew(asset_class, retry_inputs)
                return self._extract_raw_output(crew_result)

            crew_result = self._execute_crew(asset_class, crew_inputs)
            raw_output = self._extract_raw_output(crew_result)

            qualitative_insights = validate_ai_output_with_retry(
                result=raw_output,
                quantitative=quantitative,
                retry_callback=retry_with_extraction,
                max_retries=2,
            )

            self.state.qualitative_insights = qualitative_insights.model_dump()
            self.state.deep_analysis_success = True

            logger.info(f"Qualitative analysis complete for {ticker}")

            return {
                **data,
                "qualitative_insights": qualitative_insights.model_dump(),
                "ai_analysis_timestamp": datetime.now().isoformat(),
            }

        except AIOutputError as e:
            logger.error(f"AI output validation failed for {ticker}: {e}")
            self.state.deep_analysis_success = False
            self.state.deep_analysis_error = str(e)
            return {
                **data,
                "qualitative_insights": {},
                "error": str(e),
                "ai_analysis_timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Qualitative analysis failed for {ticker}: {e}")
            self.state.deep_analysis_success = False
            self.state.deep_analysis_error = str(e)
            return {
                **data,
                "qualitative_insights": {},
                "error": str(e),
                "ai_analysis_timestamp": datetime.now().isoformat(),
            }

    def _execute_crew(self, asset_class: str, inputs: dict[str, Any]) -> Any:
        """Execute the appropriate analysis crew based on asset class."""
        crew = self._get_analysis_crew(asset_class)
        return crew.crew().kickoff(inputs=inputs)

    def _get_analysis_crew(self, asset_class: str) -> Any:
        """
        Get the appropriate analysis crew based on asset class.

        Raises:
            ValueError: If asset_class is not supported
        """
        asset_class_lower = asset_class.lower()

        if asset_class_lower == "stock":
            from finwiz.crews.stock_crew.stock_crew import StockCrew

            logger.info("Instantiating StockCrew for analysis")
            return StockCrew()

        elif asset_class_lower == "etf":
            from finwiz.crews.etf_crew.etf_crew import EtfCrew

            logger.info("Instantiating EtfCrew for analysis")
            return EtfCrew()

        elif asset_class_lower == "crypto":
            from finwiz.crews.crypto_crew.crypto_crew import CryptoCrew

            logger.info("Instantiating CryptoCrew for analysis")
            return CryptoCrew()

        else:
            raise ValueError(f"Unsupported asset class: {asset_class}. Must be 'stock', 'etf', or 'crypto'.")

    def _extract_raw_output(self, crew_result: Any) -> Any:
        """Extract raw output from crew result."""
        from finwiz.validation.ai_output_validator import AIOutputError

        try:
            if hasattr(crew_result, "raw"):
                logger.debug(f"Extracted .raw attribute: {type(crew_result.raw)}")
                return crew_result.raw
            elif hasattr(crew_result, "output"):
                logger.debug(f"Extracted .output attribute: {type(crew_result.output)}")
                return crew_result.output
            elif isinstance(crew_result, dict):
                logger.debug("Crew result is already a dict")
                return crew_result
            elif hasattr(crew_result, "model_dump"):
                logger.debug("Converted Pydantic model to dict")
                return crew_result.model_dump()
            else:
                raise AIOutputError(f"Unexpected crew result type: {type(crew_result)}")
        except Exception as e:
            logger.error(f"Failed to extract raw output from crew result: {e}")
            raise AIOutputError(f"Raw output extraction failed: {e}") from e

    @listen(analyze_qualitative_insights)
    def synthesize_enriched_analysis(self, data: dict[str, Any]) -> EnrichedAnalysis:
        """
        Synthesize quantitative and qualitative into final analysis.

        Args:
            data: Data from analyze_qualitative_insights

        Returns:
            EnrichedAnalysis Pydantic model
        """
        # Delegate to HybridAnalysisSynthesizer
        return self.synthesizer.synthesize(data, self.state)
