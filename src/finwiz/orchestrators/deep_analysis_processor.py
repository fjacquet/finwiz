"""Result processing for deep analysis."""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from finwiz.flow_state import DeepAnalysisResult, FinwizState
from finwiz.schemas.hybrid_analysis import EnrichedAnalysis
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class DeepAnalysisProcessor:
    """Processes deep analysis results and manages metrics."""

    def __init__(self, state: FinwizState) -> None:
        self.state = state
        self.logger = get_logger(self.__class__.__name__)

    def create_deep_analysis_result_from_crew_output(
        self, crew_output: Any, ticker: str, asset_class: str, crew_name: str = "DeepAnalysisCrew", cached: bool = False
    ) -> DeepAnalysisResult:
        """Parse crew output into structured result."""
        from finwiz.utils.data_extractor import CrewDataExtractor

        extractor, warnings = CrewDataExtractor(), []

        try:
            grade, composite_score, fundamental_score, technical_score, risk_score = self._extract_scores(
                crew_output, ticker, extractor, warnings
            )
        except Exception:
            self.logger.error(f"Failed to extract fields for {ticker}")
            raise

        confidence = (
            0.9 if fundamental_score and technical_score and risk_score
            else 0.6 if not fundamental_score and not technical_score
            else 0.8
        )
        if confidence == 0.6:
            warnings.append("Missing fundamental and technical scores")
        if cached:
            warnings.append("Using cached analysis data")

        return DeepAnalysisResult(
            ticker=ticker,
            asset_class=asset_class,
            crew_name=crew_name,
            analysis_timestamp=datetime.now().isoformat(),
            composite_score=composite_score,
            grade=grade,
            recommendation="HOLD",
            rationale="Analysis completed",
            risk_details={},
            fundamental_score=fundamental_score,
            technical_score=technical_score,
            risk_score=risk_score,
            data_freshness_hours=0.0 if not cached else 1.0,
            confidence_level=confidence,
            warnings=warnings,
            cached=cached,
        )

    def _extract_scores(
        self, crew_output: Any, ticker: str, extractor: Any, warnings: list[str]
    ) -> tuple[str, float, float | None, float | None, float | None]:
        """Extract scores from crew output."""
        import re

        from finwiz.cache.analysis_cache_manager import CrewAnalysisResult
        from finwiz.exceptions.data_quality import MissingRequiredFieldError

        if isinstance(crew_output, CrewAnalysisResult):
            return (
                crew_output.grade,
                crew_output.composite_score,
                crew_output.fundamental_score,
                crew_output.technical_score,
                crew_output.risk_score,
            )

        if hasattr(crew_output, "pydantic") and crew_output.pydantic:
            pydantic_data = crew_output.pydantic

            data_dict = (
                pydantic_data.model_dump()
                if hasattr(pydantic_data, "model_dump")
                else pydantic_data.dict()
                if hasattr(pydantic_data, "dict")
                else {
                    "grade": getattr(pydantic_data, "grade", None),
                    "composite_score": getattr(pydantic_data, "composite_score", None),
                }
            )

            grade_score = extractor.extract_grade_and_score(data_dict, ticker)
            grade, composite_score = grade_score["grade"], grade_score["composite_score"]

            if not extractor.validate_grade_score_consistency(grade, composite_score, ticker):
                warnings.append(f"Grade {grade} may not match score {composite_score:.3f}")

            return (
                grade,
                composite_score,
                getattr(pydantic_data, "fundamental_score", None),
                getattr(pydantic_data, "technical_score", None),
                getattr(pydantic_data, "risk_score", None),
            )

        elif hasattr(crew_output, "raw"):
            raw = str(crew_output.raw)

            grade_patterns = [
                r"[Gg]rade:\s*([A-F][+\-]?)",
                r"[Rr]ating:\s*([A-F][+\-]?)",
                r"[Oo]verall\s+[Gg]rade:\s*([A-F][+\-]?)",
            ]
            score_patterns = [
                r"[Cc]omposite\s+[Ss]core:\s*(0?\.\d+|\d+\.\d+)",
                r"[Ss]core:\s*(0?\.\d+|\d+\.\d+)",
                r"[Oo]verall\s+[Ss]core:\s*(0?\.\d+|\d+\.\d+)",
            ]

            grade_match = None
            for pattern in grade_patterns:
                grade_match = re.search(pattern, raw)
                if grade_match:
                    break

            score_match = None
            for pattern in score_patterns:
                score_match = re.search(pattern, raw)
                if score_match:
                    break

            if not grade_match or not score_match:
                raw_snippet = raw[:500] if len(raw) > 500 else raw
                self.logger.error(f"Failed to extract grade/score for {ticker}. Raw output snippet: {raw_snippet}")
                raise MissingRequiredFieldError(
                    ticker=ticker,
                    field="grade/score",
                    context={
                        "source": "raw",
                        "found_grade": bool(grade_match),
                        "found_score": bool(score_match),
                        "raw_snippet": raw_snippet,
                    },
                )

            return grade_match.group(1), float(score_match.group(1)), None, None, None
        else:
            raise MissingRequiredFieldError(
                ticker=ticker, field="grade, composite_score", context={"error": "No output"}
            )

    def extract_collected_data(self, crew_output: Any) -> dict[str, Any] | None:
        """
        Extract RAW tool outputs from crew for Python scoring.

        Bypasses AI-processed output to get actual tool results with raw metrics.

        Args:
            crew_output: CrewAI crew execution result

        Returns:
            Dictionary of raw metrics for Python scoring, or None if extraction fails
        """
        try:
            self.logger.info(f"🔍 DEBUG: Starting extraction from crew_output (type={type(crew_output).__name__})")

            crew_attrs = [a for a in dir(crew_output) if not a.startswith("_")]
            self.logger.info(f"🔍 DEBUG: crew_output attributes: {crew_attrs[:20]}...")

            if not hasattr(crew_output, "tasks_output"):
                self.logger.error("❌ crew_output has no 'tasks_output' attribute!")
                return None

            if not crew_output.tasks_output:
                self.logger.error("❌ crew_output.tasks_output is empty!")
                return None

            if not isinstance(crew_output.tasks_output, (list, tuple)):
                self.logger.error(f"❌ crew_output.tasks_output is not a list/tuple! Got {type(crew_output.tasks_output).__name__}")
                return None

            self.logger.info(f"🔍 DEBUG: Found {len(crew_output.tasks_output)} tasks in tasks_output")

            data_task = crew_output.tasks_output[0]

            if hasattr(data_task, "raw") and data_task.raw:
                raw_output = data_task.raw
                self.logger.info(f"🔍 DEBUG: Found task.raw (length={len(raw_output)} chars)")

                if isinstance(raw_output, str):
                    return self._parse_raw_output(raw_output)

            if hasattr(crew_output, "pydantic") and crew_output.pydantic:
                return self._extract_from_pydantic(crew_output.pydantic)

            self.logger.warning("Could not extract tool outputs - no raw data found")
            return None

        except Exception as e:
            self.logger.error(f"Failed to extract tool outputs: {e}", exc_info=True)
            return None

    def _parse_raw_output(self, raw_output: str) -> dict[str, Any] | None:
        """Parse raw string output from crew."""
        import re

        cleaned = raw_output.strip()

        if cleaned.startswith("```"):
            lines = cleaned.split("\n", 1)
            cleaned = lines[1] if len(lines) > 1 else cleaned
            cleaned = cleaned.rstrip("`").strip()
            self.logger.info("🔍 Stripped markdown code fence")

        if cleaned.startswith("{"):
            self.logger.info("🔍 Raw output is already JSON format")
            open_braces = cleaned.count("{")
            close_braces = cleaned.count("}")
            if open_braces > close_braces:
                missing = open_braces - close_braces
                cleaned = cleaned + ("}" * missing)
                self.logger.info(f"🔍 Fixed malformed JSON: added {missing} closing braces")
        else:
            match = re.search(r"=\s*(\{.+)", cleaned, re.DOTALL)
            if match:
                cleaned = match.group(1).strip()
                self.logger.info(f"🔍 Extracted JSON from assignment (length={len(cleaned)})")

                open_braces = cleaned.count("{")
                close_braces = cleaned.count("}")
                if open_braces > close_braces:
                    missing = open_braces - close_braces
                    cleaned = cleaned + ("}" * missing)
                    self.logger.info(f"🔍 Fixed malformed JSON: added {missing} closing braces")

        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict):
                self.logger.info(f"✅ Parsed JSON with keys: {list(parsed.keys())[:10]}")

                if "collected_data" in parsed and len(parsed) == 1:
                    self.logger.info("🔍 Unwrapping 'collected_data' wrapper")
                    parsed = parsed["collected_data"]

                flattened = self._flatten_collected_data(parsed)
                self.logger.info(f"🔍 Flattened to {len(flattened)} top-level fields")
                return flattened
        except json.JSONDecodeError as e:
            self.logger.warning(f"⚠️ JSON parse failed: {e}")
            self.logger.info(f"Cleaned text preview: {cleaned[:300]}")

        return None

    def _extract_from_pydantic(self, pydantic_data: Any) -> dict[str, Any] | None:
        """Extract data from pydantic output."""
        if hasattr(pydantic_data, "model_dump"):
            data_dict = pydantic_data.model_dump()
        elif hasattr(pydantic_data, "dict"):
            data_dict = pydantic_data.dict()
        else:
            data_dict = pydantic_data if isinstance(pydantic_data, dict) else None

        if data_dict:
            self.logger.info(f"✅ Extracted pydantic data with keys: {list(data_dict.keys())[:5]}...")
            return data_dict

        return None

    def _flatten_collected_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Flatten nested tool output structures for Python scorer."""
        flattened = {}

        for key, value in data.items():
            if key not in ["ticker_info", "company_info", "quantitative_analysis", "sec_analysis", "sentiment_analysis", "ticker_validation"]:
                if isinstance(value, (int, float, str, bool, type(None))):
                    flattened[key] = value

        if "quantitative_analysis" in data and isinstance(data["quantitative_analysis"], dict):
            quant = data["quantitative_analysis"]

            if "performance_metrics" in quant and isinstance(quant["performance_metrics"], dict):
                perf = quant["performance_metrics"]
                for field in ["beta", "volatility", "max_drawdown", "sharpe_ratio", "total_return", "annualized_return"]:
                    if field in perf and perf[field] is not None:
                        flattened[field] = perf[field]

            if "technical_analysis" in quant and isinstance(quant["technical_analysis"], dict):
                tech = quant["technical_analysis"]
                if "technical_indicators" in tech and isinstance(tech["technical_indicators"], dict):
                    indicators = tech["technical_indicators"]
                    for field in ["rsi", "macd", "macd_signal", "moving_avg_50", "moving_avg_200", "sma_50", "sma_200"]:
                        if field in indicators and indicators[field] is not None:
                            flattened[field] = indicators[field]

                    if "sma_50" in flattened and "moving_avg_50" not in flattened:
                        flattened["moving_avg_50"] = flattened["sma_50"]
                    if "sma_200" in flattened and "moving_avg_200" not in flattened:
                        flattened["moving_avg_200"] = flattened["sma_200"]

        for section in ["ticker_info", "company_info", "quantitative_analysis", "sec_analysis", "sentiment_analysis"]:
            if section in data and isinstance(data[section], dict):
                self._flatten_recursive(data[section], flattened)

        return flattened

    def _flatten_recursive(self, obj: Any, target: dict[str, Any]) -> None:
        """Recursively flatten nested dict structures."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key in ["meta", "metadata", "raw_data", "debug_info"]:
                    continue

                if isinstance(value, (int, float, str, bool, type(None))):
                    if key not in target:
                        target[key] = value
                elif isinstance(value, dict):
                    self._flatten_recursive(value, target)
                elif isinstance(value, list) and len(value) == 1 and isinstance(value[0], dict):
                    self._flatten_recursive(value[0], target)

    def save_batch_metrics_to_file(self, metrics: dict[str, Any], output_path: str | None = None) -> None:
        """Save batch metrics to file."""
        if not metrics:
            return

        try:
            if output_path:
                file_path = Path(output_path)
            else:
                output_dir = Path(f"output/reports/{self.state.session_id}")
                output_dir.mkdir(parents=True, exist_ok=True)
                file_path = output_dir / "batch_prefetch_metrics.json"

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(metrics, f, indent=2, default=str)

            self.logger.info(f"✓ Metrics saved: {file_path}")
        except Exception as e:
            self.logger.error(f"✗ Save failed: {e}")

    def update_batch_metrics(
        self, crew_duration: float, processed: int, total: int, ticker_times: dict[str, float]
    ) -> None:
        """Update batch metrics with crew execution data."""
        if not self.state.batch_prefetch_metrics:
            return

        prefetch_dur = self.state.batch_prefetch_metrics.get("prefetch_duration_seconds", 0)
        total_time = prefetch_dur + crew_duration
        est_sequential = total * 30.0
        savings = est_sequential - total_time
        savings_pct = (savings / est_sequential * 100) if est_sequential > 0 else 0

        self.state.batch_prefetch_metrics.update(
            {
                "crew_execution_duration_seconds": crew_duration,
                "total_duration_seconds": total_time,
                "successful_executions": processed,
                "failed_executions": total - processed,
                "ticker_execution_times": ticker_times,
                "avg_time_per_ticker_seconds": crew_duration / processed if processed > 0 else 0,
                "estimated_sequential_time_seconds": est_sequential,
                "time_savings_seconds": savings,
                "time_savings_percentage": savings_pct,
                "crew_execution_timestamp": datetime.now().isoformat(),
            }
        )

        self.logger.info(f"Savings: {savings:.1f}s ({savings_pct:.1f}%)")

    def create_fallback_analysis(
        self, ticker: str, asset_class: str, error: Exception, data_collector: Any, hybrid_flow: Any
    ) -> EnrichedAnalysis | None:
        """
        Create fallback analysis using Python-only calculations.

        Args:
            ticker: Stock ticker symbol
            asset_class: Asset class (stock, etf, crypto)
            error: The exception that triggered the fallback
            data_collector: Data collector instance
            hybrid_flow: HybridAnalysisFlow instance

        Returns:
            EnrichedAnalysis with LOW confidence, or None if fallback also fails
        """
        self.logger.warning(f"Creating fallback analysis for {ticker} due to error: {error}")

        try:
            raw_data = data_collector.collect_data(ticker, asset_class, batch_enabled=False)

            from finwiz.scoring.deep_analysis_scorer import DeepAnalysisScorer

            scorer = DeepAnalysisScorer()
            python_result = scorer.calculate_composite_score(ticker, asset_class, raw_data)

            fallback_data = {
                "ticker": ticker,
                "asset_class": asset_class,
                "company_name": raw_data.get("company_name", ticker),
                "quantitative_analysis": {
                    "composite_score": python_result.composite_score,
                    "fundamental_score": python_result.fundamental_score,
                    "technical_score": python_result.technical_score,
                    "risk_score": python_result.risk_score,
                    "grade": python_result.grade,
                    "preliminary_recommendation": python_result.recommendation,
                    "fundamental_metrics": python_result.fundamental_metrics or {},
                    "technical_indicators": python_result.technical_indicators or {},
                    "risk_metrics": python_result.risk_metrics or {},
                    "calculation_timestamp": datetime.now().isoformat(),
                    "confidence_level": 0.5,
                    "python_rationale": python_result.rationale or "Fallback analysis",
                },
            }

            enriched_analysis = hybrid_flow._create_fallback_analysis(fallback_data)

            self.logger.info(
                f"Fallback analysis created for {ticker}: Grade {enriched_analysis.final_grade}"
            )

            return enriched_analysis

        except Exception as e:
            self.logger.error(f"Fallback analysis creation failed for {ticker}: {e}", exc_info=True)
            return None

    def validate_analysis_quality(self, analysis: EnrichedAnalysis) -> list[str]:
        """
        Validate analysis quality against requirements.

        Checks:
        - word_count >= 2000
        - unique_insights_count >= 5
        - processing_time <= 30s
        - llm_cost <= $0.10

        Args:
            analysis: EnrichedAnalysis to validate

        Returns:
            List of validation warnings (empty if all checks pass)
        """
        warnings = []

        if analysis.report_word_count < 2000:
            warning = f"Word count below threshold: {analysis.report_word_count} < 2000"
            warnings.append(warning)
            self.logger.warning(f"{analysis.ticker}: {warning}")

        if analysis.unique_insights_count < 5:
            warning = f"Insights count below threshold: {analysis.unique_insights_count} < 5"
            warnings.append(warning)
            self.logger.warning(f"{analysis.ticker}: {warning}")

        if analysis.processing_time_seconds > 30.0:
            warning = f"Processing time exceeded: {analysis.processing_time_seconds:.1f}s > 30s"
            warnings.append(warning)
            self.logger.warning(f"{analysis.ticker}: {warning}")

        if analysis.llm_cost_dollars > 0.10:
            warning = f"LLM cost exceeded: ${analysis.llm_cost_dollars:.3f} > $0.10"
            warnings.append(warning)
            self.logger.warning(f"{analysis.ticker}: {warning}")

        if not warnings:
            self.logger.info(f"{analysis.ticker}: Quality validation passed")

        return warnings

    def calculate_processing_time(self, start_time: float) -> float:
        """Calculate processing time for an analysis."""
        return time.time() - start_time

    def calculate_llm_cost(self, analysis_data: dict[str, Any]) -> float:
        """
        Calculate LLM cost for an analysis.

        Estimates cost based on typical token usage for deep analysis.

        Args:
            analysis_data: Analysis data containing LLM usage information

        Returns:
            Estimated LLM cost in dollars
        """
        if analysis_data.get("error") or not analysis_data.get("qualitative_insights"):
            return 0.0

        return 0.05  # Conservative estimate
