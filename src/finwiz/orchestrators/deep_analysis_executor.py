"""Deep analysis execution logic for portfolio holdings."""

import asyncio
import os
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from finwiz.flow_state import DeepAnalysisResult, FinwizState
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class DeepAnalysisExecutor:
    """Executes deep analysis on portfolio holdings with concurrent/sequential support."""

    def __init__(
        self,
        state: FinwizState,
        data_collector: Any,
        result_processor: Any,
        batch_prefetch_config: Any,
        integration_manager: Any = None,
    ) -> None:
        self.state = state
        self.logger = get_logger(self.__class__.__name__)
        self.data_collector = data_collector
        self.result_processor = result_processor
        self.batch_prefetch_config = batch_prefetch_config
        self.integration_manager = integration_manager

    def run_deep_analysis_on_holdings(self, holdings: list[dict[str, Any]]) -> dict[str, DeepAnalysisResult]:
        """
        Execute deep analysis on all holdings.

        Automatically uses concurrent execution when possible for 5x+ speedup.
        Falls back to sequential execution if async context unavailable.

        Args:
            holdings: List of holding dicts with 'ticker' and 'asset_class' keys

        Returns:
            Dictionary mapping tickers to DeepAnalysisResult objects
        """
        if not holdings:
            return {}

        use_concurrent = os.getenv("DEEP_ANALYSIS_CONCURRENT", "true").lower() == "true"

        if use_concurrent:
            try:
                try:
                    loop = asyncio.get_running_loop()
                    self.logger.info("Running concurrent deep analysis (existing event loop)")
                    import nest_asyncio

                    nest_asyncio.apply()
                    return asyncio.run(self.run_deep_analysis_concurrent(holdings))
                except RuntimeError:
                    self.logger.info("Running concurrent deep analysis (new event loop)")
                    return asyncio.run(self.run_deep_analysis_concurrent(holdings))
            except ImportError:
                self.logger.warning("nest_asyncio not available, falling back to sequential")
            except Exception as e:
                self.logger.warning(f"Concurrent execution failed, falling back to sequential: {e}")

        return self._run_deep_analysis_sequential(holdings)

    def _run_deep_analysis_sequential(self, holdings: list[dict[str, Any]]) -> dict[str, DeepAnalysisResult]:
        """
        Execute deep analysis sequentially (fallback method).

        Args:
            holdings: List of holding dicts

        Returns:
            Dictionary mapping tickers to DeepAnalysisResult objects
        """
        is_portfolio = len(holdings) >= self.batch_prefetch_config.min_holdings_for_batch
        batch_enabled = self.batch_prefetch_config.enabled and is_portfolio

        if batch_enabled:
            self._execute_prefetch([h.get("ticker") for h in holdings if h.get("ticker")])

        from finwiz.cache.analysis_cache_manager import get_analysis_cache_manager

        cache_mgr = get_analysis_cache_manager(ttl_hours=int(os.getenv("PORTFOLIO_CACHE_TTL_HOURS", "24")))

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
            self.result_processor.update_batch_metrics(time.time() - start_time, len(results), len(holdings), ticker_times)
            self.result_processor.save_batch_metrics_to_file(self.state.batch_prefetch_metrics, None)

        return results

    async def run_deep_analysis_concurrent(self, holdings: list[dict[str, Any]]) -> dict[str, DeepAnalysisResult]:
        """
        Execute deep analysis on all holdings concurrently.

        Uses asyncio.gather() with semaphore to process multiple holdings in parallel.

        Performance:
            - Sequential: 66 holdings × 20s = 22+ minutes
            - Concurrent (limit=5): 66 holdings in ~4-5 minutes (5x speedup)

        Args:
            holdings: List of holding dicts with 'ticker' and 'asset_class' keys

        Returns:
            Dictionary mapping tickers to DeepAnalysisResult objects
        """
        if not holdings:
            return {}

        start_time = time.time()

        is_portfolio = len(holdings) >= self.batch_prefetch_config.min_holdings_for_batch
        batch_enabled = self.batch_prefetch_config.enabled and is_portfolio

        if batch_enabled:
            self._execute_prefetch([h.get("ticker") for h in holdings if h.get("ticker")])

        from finwiz.cache.analysis_cache_manager import get_analysis_cache_manager

        cache_mgr = get_analysis_cache_manager(ttl_hours=int(os.getenv("PORTFOLIO_CACHE_TTL_HOURS", "24")))

        parallel_limit = int(os.getenv("DEEP_ANALYSIS_BATCH_SIZE", "5"))
        self.logger.info(f"Processing {len(holdings)} holdings concurrently (limit={parallel_limit})")

        semaphore = asyncio.Semaphore(parallel_limit)

        async def process_with_semaphore(idx: int, holding: dict[str, Any]) -> tuple[int, str, DeepAnalysisResult | None, float]:
            """Process a single holding with semaphore-limited concurrency."""
            ticker = holding.get("ticker")
            asset_class = holding.get("asset_class")

            if not ticker or not asset_class:
                return (idx, "", None, 0.0)

            async with semaphore:
                ticker_start = time.time()
                self.logger.debug(f"Processing {idx}/{len(holdings)}: {ticker} ({asset_class})")

                try:
                    result = await self._process_single_holding_async(ticker, asset_class, cache_mgr, 24, batch_enabled)
                    elapsed = time.time() - ticker_start
                    self.logger.debug(f"Completed {ticker} in {elapsed:.1f}s")
                    return (idx, ticker, result, elapsed)

                except Exception as e:
                    self.logger.error(f"Failed {ticker}: {e}", exc_info=True)
                    if ticker not in self.state.failed_holdings:
                        self.state.failed_holdings.append(ticker)
                    return (idx, ticker, None, time.time() - ticker_start)

        tasks = [process_with_semaphore(idx, holding) for idx, holding in enumerate(holdings, start=1)]
        task_results = await asyncio.gather(*tasks)

        results: dict[str, DeepAnalysisResult] = {}
        ticker_times: dict[str, float] = {}

        for idx, ticker, result, elapsed in task_results:
            if result and ticker:
                results[ticker] = result
                ticker_times[ticker] = elapsed

        total_time = time.time() - start_time
        sequential_estimate = len(holdings) * 20.0
        speedup = sequential_estimate / total_time if total_time > 0 else 1.0

        cache_mgr.log_cache_stats()
        self.logger.info(f"Completed {len(results)}/{len(holdings)} in {total_time:.1f}s (~{speedup:.1f}x speedup)")

        if batch_enabled and self.state.batch_prefetch_metrics:
            self.result_processor.update_batch_metrics(total_time, len(results), len(holdings), ticker_times)
            self.result_processor.save_batch_metrics_to_file(self.state.batch_prefetch_metrics, None)

        return results

    async def _process_single_holding_async(
        self,
        ticker: str,
        asset_class: str,
        cache_mgr: Any,
        cache_ttl: int,
        batch_enabled: bool,
    ) -> DeepAnalysisResult | None:
        """
        Async wrapper for _process_single_holding.

        Executes the synchronous crew kickoff in a thread pool executor.

        Args:
            ticker: Ticker symbol
            asset_class: Asset class (stock/etf/crypto)
            cache_mgr: Cache manager instance
            cache_ttl: Cache TTL in hours
            batch_enabled: Whether batch mode is enabled

        Returns:
            DeepAnalysisResult or None if processing fails
        """
        loop = asyncio.get_event_loop()

        with ThreadPoolExecutor(max_workers=1) as executor:
            return await loop.run_in_executor(
                executor,
                self._process_single_holding,
                ticker,
                asset_class,
                cache_mgr,
                cache_ttl,
                batch_enabled,
            )

    def _process_single_holding(
        self, ticker: str, asset_class: str, cache_mgr: Any, cache_ttl: int, batch_enabled: bool
    ) -> DeepAnalysisResult | None:
        """Process a single holding with caching."""
        cached = cache_mgr.get_cached_analysis(ticker, asset_class)
        if cached and cached.is_fresh(cache_ttl):
            return self.result_processor.create_deep_analysis_result_from_crew_output(
                cached.analysis, ticker, asset_class, cached.analysis.crew_name, True
            )

        # STEP 1: Python collects data directly (NO agent involvement)
        self.logger.info(f"🐍 Step 1: Python collecting data for {ticker}")
        raw_data = self.data_collector.collect_data(ticker, asset_class, batch_enabled)

        # STEP 2: Python calculates scores using raw data
        self.logger.info(f"🐍 Step 2: Python calculating scores for {ticker}")
        try:
            from finwiz.scoring.deep_analysis_scorer import DeepAnalysisScorer

            scorer = DeepAnalysisScorer()
            python_result = scorer.calculate_composite_score(ticker, asset_class, raw_data)

            self.logger.info(f"✅ Python scoring: {ticker} = {python_result.grade} ({python_result.composite_score:.3f})")

            cache_mgr.cache_analysis(ticker, asset_class, python_result)

            if self.integration_manager:
                try:
                    crew_name = f"deep_analysis_{asset_class}"
                    self.integration_manager.store_crew_output(crew_name, python_result)
                except Exception as e:
                    self.logger.warning(f"Failed to store Python result: {e}")

            # STEP 3: Pass Python results to agent for formatting
            self.logger.info("🐍 Step 3: Passing Python results to agent for formatting")
            self._execute_crew_for_formatting(ticker, asset_class, raw_data, python_result)

            return python_result

        except Exception as e:
            self.logger.error(f"Python scoring failed for {ticker}: {e}", exc_info=True)

        # FALLBACK: Old agent-based approach
        return self._process_with_fallback(ticker, asset_class, cache_mgr, batch_enabled)

    def _execute_crew_for_formatting(
        self, ticker: str, asset_class: str, raw_data: dict[str, Any], python_result: Any
    ) -> None:
        """Execute crew to format Python results."""
        from finwiz.crews.deep_analysis.deep_analysis import DeepAnalysisCrew

        crew = DeepAnalysisCrew()
        crew.crew().kickoff(
            inputs={
                "ticker": ticker,
                "asset_class": asset_class,
                "company_name": raw_data.get("company_name", ticker),
                "current_day": self.state.current_day,
                "current_month": self.state.current_month,
                "current_year": self.state.current_year,
                "current_date": self.state.current_date,
                "full_date": self.state.full_date,
                "timestamp": self.state.timestamp,
                "report_language": self.state.report_language,
                "python_results": python_result.model_dump(),
                "grade": python_result.grade,
                "composite_score": python_result.composite_score,
                "preliminary_recommendation": python_result.recommendation,
                "fundamental_score": python_result.fundamental_score or 0.0,
                "technical_score": python_result.technical_score or 0.0,
                "risk_score": python_result.risk_score or 0.0,
                "fundamental_metrics": python_result.fundamental_details,
                "technical_indicators": python_result.technical_details,
                "risk_metrics": python_result.risk_details,
            }
        )

        from finwiz.integration.html_auto_generator import auto_generate_html_for_crew

        crew_name = f"deep_analysis_{asset_class}"
        auto_generate_html_for_crew(crew_name)

    def _process_with_fallback(
        self, ticker: str, asset_class: str, cache_mgr: Any, batch_enabled: bool
    ) -> DeepAnalysisResult | None:
        """Fallback processing using agent-based approach."""
        from finwiz.crews.deep_analysis.deep_analysis import DeepAnalysisCrew

        crew = DeepAnalysisCrew()

        if batch_enabled and self.state.prefetched_data:
            crew.set_prefetched_data(self.state.prefetched_data)

        result = crew.crew().kickoff(
            inputs={
                "ticker": ticker,
                "asset_class": asset_class,
                "company_name": ticker,
                "current_day": self.state.current_day,
                "current_month": self.state.current_month,
                "current_year": self.state.current_year,
                "current_date": self.state.current_date,
                "full_date": self.state.full_date,
                "timestamp": self.state.timestamp,
                "report_language": self.state.report_language,
                "grade": "N/A",
                "composite_score": 0.0,
                "preliminary_recommendation": "PENDING",
                "fundamental_score": 0.0,
                "technical_score": 0.0,
                "risk_score": 0.0,
                "fundamental_metrics": {},
                "technical_indicators": {},
                "risk_metrics": {},
                "python_results": {},
            }
        )

        from finwiz.integration.html_auto_generator import auto_generate_html_for_crew

        crew_name = f"deep_analysis_{asset_class}"
        auto_generate_html_for_crew(crew_name)

        # Try Python scoring on agent output
        try:
            from finwiz.scoring.deep_analysis_scorer import DeepAnalysisScorer

            collected_data = self.result_processor.extract_collected_data(result)

            if collected_data:
                scorer = DeepAnalysisScorer()
                python_result = scorer.calculate_composite_score(ticker, asset_class, collected_data)

                self.logger.info(f"✅ Python scoring: {ticker} = {python_result.grade} ({python_result.composite_score:.3f})")

                cache_mgr.cache_analysis(ticker, asset_class, python_result)

                if self.integration_manager:
                    try:
                        crew_name = f"deep_analysis_{asset_class}"
                        self.integration_manager.store_crew_output(crew_name, python_result)
                    except Exception as e:
                        self.logger.warning(f"Failed to store Python scoring output: {e}")

                return python_result
            else:
                self.logger.warning(f"No collected data found for {ticker}, falling back to AI scores")
        except Exception as e:
            self.logger.error(f"Python scoring failed for {ticker}: {e}")

        # Final fallback: Store crew output
        if self.integration_manager:
            try:
                crew_name = f"deep_analysis_{asset_class}"
                self.integration_manager.store_crew_output(crew_name, result)
            except Exception as e:
                self.logger.warning(f"Failed to store crew output for {ticker}: {e}")

        deep_result = self.result_processor.create_deep_analysis_result_from_crew_output(
            result, ticker, asset_class, "DeepAnalysisCrew", False
        )
        cache_mgr.cache_analysis(ticker, asset_class, deep_result)
        return deep_result

    def _execute_prefetch(self, tickers: list[str]) -> dict[str, Any]:
        """Execute batch prefetch optimization."""
        from datetime import datetime

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
