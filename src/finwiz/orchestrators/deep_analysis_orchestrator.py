"""Deep Analysis Orchestrator for FinWiz Flow."""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from finwiz.flow_state import DeepAnalysisResult, FinwizState
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class DeepAnalysisOrchestrator:
    """Orchestrates deep analysis execution on portfolio holdings."""

    def __init__(self, state: FinwizState, **dependencies: Any) -> None:
        self.state = state
        self.logger = get_logger(self.__class__.__name__)
        self.batch_prefetch_config = dependencies.get("batch_prefetch_config")
        self.cache_service = dependencies.get("cache_service")
        self.cache_enabled = dependencies.get("cache_enabled", False)
        self.crew_factory = dependencies.get("crew_factory")
        self.integration_manager = dependencies.get("integration_manager")
        self.error_handler = dependencies.get("error_handler")

    async def analyze_and_update_portfolio(self) -> dict[str, Any]:
        """
        Perform deep analysis and update portfolio review (atomic operation).

        This method consolidates three related operations:
        1. Run deep analysis on holdings
        2. Match alternatives for underperforming holdings
        3. Update portfolio review with enriched data

        Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4

        Returns:
            dict: Consolidated results with deep analysis and alternatives

        """
        self.logger.info("=" * 80)
        self.logger.info("Phase 3: Deep Analysis & Portfolio Update (Atomic Operation)")
        self.logger.info("=" * 80)

        # Check if deep analysis is enabled
        enabled = os.getenv("DEEP_PORTFOLIO_ANALYSIS", "false").lower() == "true"
        if not enabled:
            self.logger.info("Deep analysis disabled via DEEP_PORTFOLIO_ANALYSIS")
            return {}

        # Get portfolio review from state
        portfolio_review = self.state.portfolio_review
        if not portfolio_review or not portfolio_review.get("holdings"):
            self.logger.warning("No portfolio holdings available for deep analysis")
            return {}

        holdings = portfolio_review.get("holdings", [])
        self.logger.info(f"Starting deep analysis for {len(holdings)} holdings")

        # Step 1: Run deep analysis on all holdings
        try:
            deep_results = self.run_deep_analysis_on_holdings(holdings)

            # Update structured Flow state
            self.state.deep_analysis_results = deep_results
            self.state.deep_analysis_success = True

            self.logger.info(f"Deep analysis completed: {len(deep_results)}/{len(holdings)} holdings analyzed")

        except Exception as e:
            self.logger.error(f"Deep analysis failed: {e}", exc_info=True)
            self.state.deep_analysis_success = False
            self.state.deep_analysis_error = str(e)
            return {"deep_analysis_results": {}, "error": str(e)}

        # Step 2: Match alternatives for underperforming holdings
        try:
            from finwiz.orchestrators.alternatives_matching_orchestrator import AlternativesMatchingOrchestrator

            alternatives_orch = AlternativesMatchingOrchestrator(
                state=self.state,
                crew_factory=self.crew_factory,
                integration_manager=self.integration_manager,
                error_handler=self.error_handler,
            )

            # Convert deep results to holdings format for alternatives matching
            holdings_with_analysis = []
            for ticker, analysis in deep_results.items():
                holding_dict = {
                    "ticker": ticker,
                    "grade": analysis.grade,
                    "composite_score": analysis.composite_score,
                    "risk_score": analysis.risk_score,
                    "name": getattr(analysis, "name", ticker),
                    "asset_class": analysis.asset_class,
                }
                holdings_with_analysis.append(holding_dict)

            alternatives_data = alternatives_orch.match_alternatives_for_holdings(
                holdings_with_analysis,
                {},  # Discovery results not yet available
            )

            # Update state with alternatives
            self.state.portfolio_alternatives = alternatives_data
            self.state.alternatives_success = True
            self.state.alternatives_count = sum(len(alts) for alts in alternatives_data.values())

            self.logger.info(f"Alternative matching completed: {self.state.alternatives_count} alternatives found")

        except Exception as e:
            self.logger.error(f"Alternative matching failed: {e}", exc_info=True)
            self.state.alternatives_success = False
            alternatives_data = {}

        # Step 3: Update portfolio review with enriched data
        try:
            self._update_portfolio_review_with_enriched_data(deep_results, alternatives_data)
            self.logger.info("Portfolio review updated with deep analysis and alternatives")

        except Exception as e:
            self.logger.error(f"Portfolio review update failed: {e}", exc_info=True)

        self.logger.info("=" * 80)

        # Return consolidated results for downstream Flow methods
        return {
            "deep_analysis_results": deep_results,
            "alternatives": alternatives_data,
            "portfolio_updated": True,
        }

    def _update_portfolio_review_with_enriched_data(
        self,
        deep_results: dict[str, DeepAnalysisResult],
        alternatives_data: dict[str, list[dict[str, Any]]],
    ) -> None:
        """
        Update portfolio review with deep analysis results and alternatives.

        Args:
            deep_results: Deep analysis results keyed by ticker
            alternatives_data: Alternatives data keyed by ticker

        """
        if not self.state.portfolio_review:
            return

        holdings = self.state.portfolio_review.get("holdings", [])

        for holding in holdings:
            ticker = holding.get("ticker")
            if not ticker:
                continue

            # Enrich with deep analysis results
            if ticker in deep_results:
                analysis = deep_results[ticker]
                holding["composite_score"] = analysis.composite_score
                holding["grade"] = analysis.grade
                # NOTE: fundamental_score, technical_score, risk_score, confidence_level, analysis_timestamp
                # are NOT in HoldingDecision schema and will cause Pydantic validation errors
                # These fields exist in DeepAnalysisResult but should not be copied to holdings

            # Enrich with alternatives
            if ticker in alternatives_data:
                holding["alternatives"] = alternatives_data[ticker]

        # Update state
        self.state.portfolio_review["holdings"] = holdings

    def run_deep_analysis_on_holdings(self, holdings: list[dict[str, Any]]) -> dict[str, DeepAnalysisResult]:
        """Execute deep analysis on all holdings. Requirements: 3.1"""
        if not holdings:
            return {}

        # Determine batch mode
        is_portfolio = len(holdings) >= self.batch_prefetch_config.min_holdings_for_batch
        batch_enabled = self.batch_prefetch_config.enabled and is_portfolio

        if batch_enabled:
            self.execute_deep_analysis_with_prefetch([h.get("ticker") for h in holdings if h.get("ticker")])

        # Initialize cache
        from finwiz.cache.analysis_cache_manager import get_analysis_cache_manager

        cache_mgr = get_analysis_cache_manager(ttl_hours=int(os.getenv("PORTFOLIO_CACHE_TTL_HOURS", "24")))

        # Process holdings
        results, ticker_times, start_time = {}, {}, time.time()

        for holding in holdings:
            ticker, asset_class = holding.get("ticker"), holding.get("asset_class")
            if not ticker or not asset_class:
                continue

            ticker_start = time.time()
            try:
                result = self._process_single_holding(ticker, asset_class, cache_mgr, 24, batch_enabled)
                if result:
                    results[ticker] = result
                    ticker_times[ticker] = time.time() - ticker_start
            except Exception as e:
                self.logger.error(f"Failed {ticker}: {e}", exc_info=True)
                if ticker not in self.state.failed_holdings:
                    self.state.failed_holdings.append(ticker)

        cache_mgr.log_cache_stats()
        self.logger.info(f"Completed {len(results)}/{len(holdings)} in {time.time() - start_time:.1f}s")

        if batch_enabled and self.state.batch_prefetch_metrics:
            self._update_batch_metrics(time.time() - start_time, len(results), len(holdings), ticker_times)
            self.save_batch_metrics_to_file(self.state.batch_prefetch_metrics, None)

        return results

    def _process_single_holding(self, ticker: str, asset_class: str, cache_mgr: Any, cache_ttl: int, batch_enabled: bool) -> DeepAnalysisResult | None:
        """Process a single holding with caching."""
        cached = cache_mgr.get_cached_analysis(ticker, asset_class)
        if cached and cached.is_fresh(cache_ttl):
            return self.create_deep_analysis_result_from_crew_output(cached.analysis, ticker, asset_class, cached.analysis.crew_name, True)

        from finwiz.crews.deep_analysis.deep_analysis import DeepAnalysisCrew

        crew = DeepAnalysisCrew()

        if batch_enabled and self.state.prefetched_data:
            crew.set_prefetched_data(self.state.prefetched_data)

        result = crew.crew().kickoff(
            inputs={
                "ticker": ticker,
                "asset_class": asset_class,
                "current_day": self.state.current_day,
                "current_month": self.state.current_month,
                "current_year": self.state.current_year,
                "current_date": self.state.current_date,
                "full_date": self.state.full_date,
                "timestamp": self.state.timestamp,
                "report_language": self.state.report_language,
            }
        )

        # PYTHON SCORING: Call DeepAnalysisScorer with collected data
        # This replaces AI-generated fake scores with real Python calculations
        try:
            from finwiz.scoring.deep_analysis_scorer import DeepAnalysisScorer

            # Extract collected data from crew output
            collected_data = self._extract_collected_data(result)

            if collected_data:
                # Calculate scores using Python scorer (not AI!)
                scorer = DeepAnalysisScorer()
                python_result = scorer.calculate_composite_score(ticker, asset_class, collected_data)

                self.logger.info(f"✅ Python scoring: {ticker} = {python_result.grade} ({python_result.composite_score:.3f})")

                # Cache and return Python-calculated result
                cache_mgr.cache_analysis(ticker, asset_class, python_result)

                # Store to disk for integration
                if self.integration_manager:
                    try:
                        crew_name = f"deep_analysis_{asset_class}"
                        # Store Python result instead of AI result
                        self.integration_manager.store_crew_output(crew_name, python_result)
                        self.logger.debug(f"Stored Python scoring output for {ticker}")
                    except Exception as e:
                        self.logger.warning(f"Failed to store Python scoring output: {e}")

                return python_result
            else:
                self.logger.warning(f"No collected data found in crew output for {ticker}, falling back to AI scores")
        except Exception as e:
            self.logger.error(f"Python scoring failed for {ticker}: {e}, falling back to AI scores")

        # Fallback: Store crew output to disk for integration system (AI scores)
        if self.integration_manager:
            try:
                crew_name = f"deep_analysis_{asset_class}"
                self.integration_manager.store_crew_output(crew_name, result)
                self.logger.debug(f"Stored crew output for {ticker} ({asset_class}) to {crew_name}")
            except Exception as e:
                self.logger.warning(f"Failed to store crew output for {ticker}: {e}")

        deep_result = self.create_deep_analysis_result_from_crew_output(result, ticker, asset_class, "DeepAnalysisCrew", False)
        cache_mgr.cache_analysis(ticker, asset_class, deep_result)
        return deep_result

    def _extract_collected_data(self, crew_output: Any) -> dict[str, Any] | None:
        """
        Extract and flatten collected data from crew output for Python scoring.

        Uses CrewDataExtractor to parse crew output and flatten it into the
        format expected by DeepAnalysisScorer.

        Args:
            crew_output: CrewAI crew execution result

        Returns:
            Dictionary of flattened metrics for Python scoring, or None if extraction fails

        """
        from finwiz.utils.data_extractor import CrewDataExtractor

        try:
            extractor = CrewDataExtractor()

            # Try to extract pydantic output first (most structured)
            if hasattr(crew_output, "pydantic") and crew_output.pydantic:
                pydantic_data = crew_output.pydantic
                # Convert pydantic model to dict
                if hasattr(pydantic_data, "model_dump"):
                    data_dict = pydantic_data.model_dump()
                elif hasattr(pydantic_data, "dict"):
                    data_dict = pydantic_data.dict()
                else:
                    data_dict = pydantic_data

                self.logger.debug(f"Extracted pydantic data with keys: {list(data_dict.keys()) if isinstance(data_dict, dict) else 'not dict'}")
                return data_dict

            # Try raw output from tasks
            if hasattr(crew_output, "tasks_output") and crew_output.tasks_output:
                # Get output from data_collection_task (first task)
                data_task = crew_output.tasks_output[0]

                if hasattr(data_task, "pydantic") and data_task.pydantic:
                    pydantic_data = data_task.pydantic
                    if hasattr(pydantic_data, "model_dump"):
                        data_dict = pydantic_data.model_dump()
                    elif hasattr(pydantic_data, "dict"):
                        data_dict = pydantic_data.dict()
                    else:
                        data_dict = pydantic_data

                    self.logger.debug(f"Extracted task pydantic data with keys: {list(data_dict.keys()) if isinstance(data_dict, dict) else 'not dict'}")
                    return data_dict

                # Try raw JSON output
                if hasattr(data_task, "raw") and isinstance(data_task.raw, str):
                    import json

                    try:
                        data_dict = json.loads(data_task.raw)
                        self.logger.debug(f"Parsed raw JSON with keys: {list(data_dict.keys()) if isinstance(data_dict, dict) else 'not dict'}")
                        return data_dict
                    except json.JSONDecodeError:
                        self.logger.debug("Raw output is not valid JSON")

            self.logger.warning("Could not extract structured data from crew output")
            return None

        except Exception as e:
            self.logger.error(f"Failed to extract collected data: {e}", exc_info=True)
            return None

    def create_deep_analysis_result_from_crew_output(
        self, crew_output: Any, ticker: str, asset_class: str, crew_name: str = "DeepAnalysisCrew", cached: bool = False
    ) -> DeepAnalysisResult:
        """Parse crew output into structured result. Requirements: 3.2, 3.5"""
        from finwiz.utils.data_extractor import CrewDataExtractor

        extractor, warnings = CrewDataExtractor(), []

        try:
            grade, composite_score, fundamental_score, technical_score, risk_score = self._extract_scores(crew_output, ticker, extractor, warnings)
        except Exception:
            self.logger.error(f"Failed to extract fields for {ticker}")
            raise

        # Calculate confidence
        confidence = 0.9 if fundamental_score and technical_score and risk_score else 0.6 if not fundamental_score and not technical_score else 0.8
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

    def _extract_scores(self, crew_output: Any, ticker: str, extractor: Any, warnings: list[str]) -> tuple[str, float, float | None, float | None, float | None]:
        """Extract scores from crew output."""
        from finwiz.exceptions.data_quality import MissingRequiredFieldError
        from finwiz.cache.analysis_cache_manager import CrewAnalysisResult

        # Handle cached CrewAnalysisResult directly
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

            # Convert to dict
            data_dict = (
                pydantic_data.model_dump()
                if hasattr(pydantic_data, "model_dump")
                else pydantic_data.dict()
                if hasattr(pydantic_data, "dict")
                else {"grade": getattr(pydantic_data, "grade", None), "composite_score": getattr(pydantic_data, "composite_score", None)}
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
            import re

            raw = str(crew_output.raw)
            grade_match = re.search(r"[Gg]rade:\s*([A-F][+\-]?)", raw)
            score_match = re.search(r"[Ss]core:\s*(0?\.\d+|\d+\.\d+)", raw)

            if not grade_match or not score_match:
                raise MissingRequiredFieldError(ticker=ticker, field="grade/score", context={"source": "raw"})

            return grade_match.group(1), float(score_match.group(1)), None, None, None
        else:
            raise MissingRequiredFieldError(ticker=ticker, field="grade, composite_score", context={"error": "No output"})

    def execute_deep_analysis_with_prefetch(self, tickers: list[str]) -> dict[str, Any]:
        """Execute with batch prefetch optimization. Requirements: 3.3"""
        from finwiz.utils.batch_data_prefetcher import BatchDataPreFetcher

        try:
            prefetcher = BatchDataPreFetcher(
                session_id=self.state.session_id or "default",
                enable_alpha_vantage=False,
                alpha_vantage_rate_limit=self.batch_prefetch_config.alpha_vantage_rate_limit,
            )
        except Exception as e:
            self.logger.error(f"Prefetcher init failed: {e}")
            return {}

        start = time.time()
        try:
            data = prefetcher.prefetch_all_data(tickers)
        except Exception as e:
            self.logger.error(f"Prefetch failed: {e}")
            return {}

        duration = time.time() - start
        successful = sum(1 for d in data.values() if not d.get("failed", False))
        failure_rate = (len(tickers) - successful) / len(tickers) if tickers else 0

        if failure_rate > 0.5:
            self.logger.warning(f"Failure rate too high: {failure_rate * 100:.1f}%")
            return {}

        self.state.prefetched_data = data
        self.state.batch_prefetch_enabled = True
        self.logger.info(f"✓ Prefetch done in {duration:.1f}s ({successful}/{len(tickers)})")

        self.state.batch_prefetch_metrics = {
            "total_tickers": len(tickers),
            "successful_tickers": successful,
            "failed_tickers": len(tickers) - successful,
            "failure_rate": failure_rate,
            "prefetch_duration_seconds": duration,
            "time_per_ticker_seconds": duration / len(tickers) if tickers else 0,
            "prefetch_timestamp": datetime.now().isoformat(),
        }

        return data

    def save_batch_metrics_to_file(self, metrics: dict[str, Any], output_path: str | None = None) -> None:
        """Save batch metrics to file. Requirements: 3.4"""
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

    def _update_batch_metrics(self, crew_duration: float, processed: int, total: int, ticker_times: dict[str, float]) -> None:
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
