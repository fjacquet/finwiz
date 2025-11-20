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

    def _collect_data_with_python(self, ticker: str, asset_class: str, batch_enabled: bool) -> dict[str, Any]:
        """
        Python directly calls tools to collect raw financial data.

        This ensures 100% reliable data collection - agents can't "forget" to run tools.
        Python gets raw facts (current_price=150.0, roe=0.25) for scoring.

        Args:
            ticker: Ticker symbol
            asset_class: Asset class (stock/etf/crypto)
            batch_enabled: Whether batch mode is enabled

        Returns:
            Dictionary with raw metrics for Python scoring
        """
        import json
        from finwiz.tools.quantitative_analysis_tool import QuantitativeAnalysisTool
        from finwiz.tools.enhanced_sentiment_tool import EnhancedSentimentAnalysisTool
        from finwiz.tools.yahoo_finance_ticker_info_tool import YahooFinanceTickerInfoTool
        from finwiz.tools.yahoo_finance_company_info_tool import YahooFinanceCompanyInfoTool

        self.logger.info(f"🐍 Python collecting data for {ticker} ({asset_class})")

        collected_data = {
            "ticker": ticker,
            "asset_class": asset_class,
            "collection_timestamp": self.state.full_date,
        }

        try:
            # STEP 0: Yahoo Finance - Current price and basic info
            self.logger.info(f"🐍 Calling YahooFinanceTickerInfoTool for {ticker}")
            ticker_tool = YahooFinanceTickerInfoTool()
            ticker_result = ticker_tool._run(ticker=ticker)

            if "current_price" in ticker_result:
                collected_data["current_price"] = ticker_result["current_price"]
                self.logger.info(f"✅ Got current_price: {ticker_result['current_price']}")

            collected_data["ticker_info"] = ticker_result

        except Exception as e:
            self.logger.error(f"❌ Ticker info failed: {e}", exc_info=True)
            collected_data["ticker_info"] = {}

        try:
            # STEP 0.5: Yahoo Finance - Company fundamentals (ROE, debt/equity, revenue growth)
            if asset_class.lower() == "stock":
                self.logger.info(f"🐍 Calling YahooFinanceCompanyInfoTool for {ticker}")
                company_tool = YahooFinanceCompanyInfoTool()
                company_result = company_tool._run(ticker=ticker)

                # Extract fundamental metrics to top level
                if "financial_metrics" in company_result:
                    metrics = company_result["financial_metrics"]
                    if "return_on_equity" in metrics:
                        collected_data["roe"] = metrics["return_on_equity"]
                        self.logger.info(f"✅ Got roe: {metrics['return_on_equity']}")
                    if "debt_to_equity" in metrics:
                        collected_data["debt_to_equity"] = metrics["debt_to_equity"]
                        self.logger.info(f"✅ Got debt_to_equity: {metrics['debt_to_equity']}")
                    if "revenue_growth" in metrics:
                        collected_data["revenue_growth"] = metrics["revenue_growth"]
                        self.logger.info(f"✅ Got revenue_growth: {metrics['revenue_growth']}")
                    if "profit_margin" in metrics:
                        collected_data["profit_margin"] = metrics["profit_margin"]
                        self.logger.info(f"✅ Got profit_margin: {metrics['profit_margin']}")

                collected_data["company_info"] = company_result

        except Exception as e:
            self.logger.error(f"❌ Company info failed: {e}", exc_info=True)
            collected_data["company_info"] = {}

        try:
            # STEP 1: Quantitative Analysis (volatility, beta, technical indicators, risk metrics)
            self.logger.info(f"🐍 Calling QuantitativeAnalysisTool for {ticker}")
            quant_tool = QuantitativeAnalysisTool()
            quant_result = quant_tool._run(
                symbol=ticker,
                asset_class=asset_class,
                analysis_type="comprehensive",
                timeframe="1y",
                strategy="sma_crossover"
            )

            # Parse quant result (it returns JSON string)
            quant_data = json.loads(quant_result) if isinstance(quant_result, str) else quant_result
            collected_data["quantitative_analysis"] = quant_data
            self.logger.info(f"✅ Got quantitative data with keys: {list(quant_data.keys())[:5]}")

            # DEBUG: Check if beta is in the data
            if "performance_metrics" in quant_data:
                perf_keys = list(quant_data["performance_metrics"].keys()) if isinstance(quant_data["performance_metrics"], dict) else "not a dict"
                self.logger.info(f"🔍 DEBUG: performance_metrics keys: {perf_keys}")
                if isinstance(quant_data["performance_metrics"], dict) and "beta" in quant_data["performance_metrics"]:
                    self.logger.info(f"🔍 DEBUG: Found beta={quant_data['performance_metrics']['beta']} in quantitative data")
                else:
                    self.logger.warning(f"⚠️ DEBUG: Beta NOT found in performance_metrics!")
            else:
                self.logger.warning(f"⚠️ DEBUG: No performance_metrics in quantitative data!")

        except Exception as e:
            self.logger.error(f"❌ Quantitative analysis failed: {e}", exc_info=True)
            collected_data["quantitative_analysis"] = {}

        try:
            # STEP 2: Sentiment Analysis
            self.logger.info(f"🐍 Calling SentimentAnalysisTool for {ticker}")
            sentiment_tool = EnhancedSentimentAnalysisTool()
            sentiment_result = sentiment_tool._run(
                ticker=ticker,
                asset_type=asset_class,
                max_articles=20,
                days_back=30
            )

            # Store sentiment result (it's already formatted markdown text, not JSON)
            # The sentiment tool returns markdown strings, not JSON objects
            if isinstance(sentiment_result, str):
                # Check if it's an error message
                if sentiment_result.startswith("Error:") or "No data available" in sentiment_result:
                    self.logger.warning(f"⚠️ Sentiment tool returned error/warning: {sentiment_result[:100]}")
                    collected_data["sentiment_analysis"] = {"error": sentiment_result}
                else:
                    # Store the markdown analysis text
                    collected_data["sentiment_analysis"] = {"analysis_text": sentiment_result}
                    self.logger.info(f"✅ Got sentiment analysis ({len(sentiment_result)} chars)")
            else:
                # Unexpected type - store as-is
                collected_data["sentiment_analysis"] = sentiment_result
                self.logger.info(f"✅ Got sentiment data with keys: {list(sentiment_result.keys())[:5] if isinstance(sentiment_result, dict) else 'N/A'}")

        except Exception as e:
            self.logger.error(f"❌ Sentiment analysis failed: {e}", exc_info=True)
            collected_data["sentiment_analysis"] = {}

        try:
            # STEP 3: SEC Analysis (stocks only - fundamentals like ROE, debt/equity)
            if asset_class.lower() == "stock":
                self.logger.info(f"🐍 Calling SEC Analysis for {ticker}")
                from finwiz.tools.enhanced_sec_tool import EnhancedSECAnalysisTool

                sec_tool = EnhancedSECAnalysisTool()
                sec_result = sec_tool._run(
                    ticker=ticker,
                    form_type="10-K",
                    sections=["Item 1", "Item 1A", "Item 7"],
                    risk_assessment=True,
                    include_perplexity=False  # Disabled for speed
                )

                # Store SEC result (it's already formatted markdown text, not JSON)
                # The SEC tool returns markdown strings, not JSON objects
                if isinstance(sec_result, str):
                    # Check if it's an error message
                    if sec_result.startswith("Error:") or sec_result.startswith("No SEC filings"):
                        self.logger.warning(f"⚠️ SEC tool returned error/warning: {sec_result[:100]}")
                        collected_data["sec_analysis"] = {"error": sec_result}
                    else:
                        # Store the markdown analysis text
                        collected_data["sec_analysis"] = {"analysis_text": sec_result}
                        self.logger.info(f"✅ Got SEC analysis ({len(sec_result)} chars)")
                else:
                    # Unexpected type - store as-is
                    collected_data["sec_analysis"] = sec_result
                    self.logger.info(f"✅ Got SEC data with keys: {list(sec_result.keys())[:5] if isinstance(sec_result, dict) else 'N/A'}")

        except Exception as e:
            self.logger.error(f"❌ SEC analysis failed: {e}", exc_info=True)
            collected_data["sec_analysis"] = {}

        # Flatten nested structures for Python scorer
        flattened = self._flatten_collected_data(collected_data)

        self.logger.info(f"✅ Python collected {len(flattened)} fields: {list(flattened.keys())[:10]}")
        return flattened

    def _process_single_holding(self, ticker: str, asset_class: str, cache_mgr: Any, cache_ttl: int, batch_enabled: bool) -> DeepAnalysisResult | None:
        """Process a single holding with caching."""
        cached = cache_mgr.get_cached_analysis(ticker, asset_class)
        if cached and cached.is_fresh(cache_ttl):
            return self.create_deep_analysis_result_from_crew_output(cached.analysis, ticker, asset_class, cached.analysis.crew_name, True)

        # STEP 1: PYTHON calls tools directly (NO agent involvement)
        self.logger.info(f"🐍 Step 1: Python collecting data for {ticker}")
        raw_data = self._collect_data_with_python(ticker, asset_class, batch_enabled)

        # STEP 2: PYTHON calculates scores using raw data
        self.logger.info(f"🐍 Step 2: Python calculating scores for {ticker}")
        try:
            from finwiz.scoring.deep_analysis_scorer import DeepAnalysisScorer

            scorer = DeepAnalysisScorer()
            python_result = scorer.calculate_composite_score(ticker, asset_class, raw_data)

            self.logger.info(f"✅ Python scoring: {ticker} = {python_result.grade} ({python_result.composite_score:.3f})")

            # Cache Python result
            cache_mgr.cache_analysis(ticker, asset_class, python_result)

            # Store to disk
            if self.integration_manager:
                try:
                    crew_name = f"deep_analysis_{asset_class}"
                    self.integration_manager.store_crew_output(crew_name, python_result)
                except Exception as e:
                    self.logger.warning(f"Failed to store Python result: {e}")

            # STEP 3: Pass Python results to agent as INPUT (agent just formats)
            self.logger.info(f"🐍 Step 3: Passing Python results to agent for formatting")

            from finwiz.crews.deep_analysis.deep_analysis import DeepAnalysisCrew
            crew = DeepAnalysisCrew()

            # Agent receives Python calculations as facts - NO tool calling
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
                    # CRITICAL: Pass Python results as input - agent just reads these facts
                    "python_results": python_result.model_dump(),
                    "grade": python_result.grade,
                    "composite_score": python_result.composite_score,
                    "recommendation": python_result.recommendation,
                }
            )

            return python_result  # Return Python result (NOT agent output)

        except Exception as e:
            self.logger.error(f"Python scoring failed for {ticker}: {e}", exc_info=True)
            # Fallback: Still try agent-based approach

        # FALLBACK: Old agent-based approach (if Python scoring fails)
        from finwiz.crews.deep_analysis.deep_analysis import DeepAnalysisCrew
        crew = DeepAnalysisCrew()

        if batch_enabled and self.state.prefetched_data:
            crew.set_prefetched_data(self.state.prefetched_data)

        # Provide placeholder values for template variables expected by tasks.yaml
        # These will be replaced by actual values if agent-based scoring works
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
                # Placeholder values for Python scoring results (used in task templates)
                "grade": "N/A",
                "composite_score": 0.0,
                "recommendation": "PENDING",
                "python_results": {},
            }
        )

        # OLD APPROACH: Extract collected data from agent output
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

    def _flatten_collected_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Flatten nested tool output structures for Python scorer.

        The scorer expects flat dict with fields like: current_price, roe, volatility, beta, etc.
        But agent outputs come nested in structures like:
        - quantitative_analysis.prices.current_price
        - quantitative_analysis.risk_metrics.volatility
        - sec_analysis.fundamentals.roe

        Args:
            data: Nested dict from agent tool outputs

        Returns:
            Flattened dict with all metrics at top level
        """
        flattened = {}

        # Keep ALL top-level fields (including current_price, roe, debt_to_equity, etc.)
        # These were explicitly extracted by _collect_data_with_python
        for key, value in data.items():
            # Skip only the nested sections we'll process separately
            if key not in ["ticker_info", "company_info", "quantitative_analysis", "sec_analysis", "sentiment_analysis", "ticker_validation"]:
                if isinstance(value, (int, float, str, bool, type(None))):
                    flattened[key] = value

        # CRITICAL FIX: Sometimes agent nests sections inside ticker_validation
        # Check if ticker_validation contains the other sections FIRST before processing
        if "ticker_validation" in data and isinstance(data["ticker_validation"], dict):
            ticker_val = data["ticker_validation"]

            # Extract the nested sections if they're wrongly placed inside ticker_validation
            for section in ["quantitative_analysis", "sec_analysis", "sentiment_analysis"]:
                if section in ticker_val and isinstance(ticker_val[section], dict):
                    self.logger.info(f"🔍 Found {section} nested inside ticker_validation, extracting...")
                    # Move it to top level for proper processing
                    data[section] = ticker_val[section]

            # Also process ticker_validation itself for basic fields
            if "valid" in ticker_val:
                flattened["valid"] = ticker_val["valid"]
            if "company_name" in ticker_val:
                flattened["company_name"] = ticker_val["company_name"]

        # CRITICAL: Explicitly extract well-known nested fields BEFORE general flattening
        # This ensures critical fields like beta, volatility, etc. are captured correctly
        if "quantitative_analysis" in data and isinstance(data["quantitative_analysis"], dict):
            quant = data["quantitative_analysis"]
            self.logger.info(f"🔍 FLATTEN: Found quantitative_analysis with keys: {list(quant.keys())[:10]}")

            # Extract performance_metrics fields (beta, volatility, max_drawdown, etc.)
            if "performance_metrics" in quant and isinstance(quant["performance_metrics"], dict):
                perf = quant["performance_metrics"]
                self.logger.info(f"🔍 FLATTEN: Found performance_metrics with keys: {list(perf.keys())}")
                critical_perf_fields = ["beta", "volatility", "max_drawdown", "sharpe_ratio",
                                       "total_return", "annualized_return"]
                for field in critical_perf_fields:
                    if field in perf and perf[field] is not None:
                        flattened[field] = perf[field]
                        self.logger.info(f"✅ FLATTEN: Extracted {field}={perf[field]} from performance_metrics")
                    else:
                        self.logger.warning(f"⚠️ FLATTEN: Field {field} not found or is None in performance_metrics")
            else:
                self.logger.warning(f"⚠️ FLATTEN: No performance_metrics dict in quantitative_analysis")

            # Extract technical_analysis fields (RSI, MACD, etc.)
            if "technical_analysis" in quant and isinstance(quant["technical_analysis"], dict):
                tech = quant["technical_analysis"]
                if "technical_indicators" in tech and isinstance(tech["technical_indicators"], dict):
                    indicators = tech["technical_indicators"]
                    critical_tech_fields = ["rsi", "macd", "macd_signal"]
                    for field in critical_tech_fields:
                        if field in indicators and indicators[field] is not None:
                            flattened[field] = indicators[field]
                            self.logger.debug(f"✅ Extracted {field}={indicators[field]} from technical_indicators")

        # Now extract from nested structures (including the ones we just moved to top level)
        # Also process ticker_info and company_info which contain nested data
        nested_sections = ["ticker_info", "company_info", "quantitative_analysis", "sec_analysis", "sentiment_analysis"]

        for section in nested_sections:
            if section in data and isinstance(data[section], dict):
                self.logger.info(f"🔍 Processing section: {section}")
                self._flatten_recursive(data[section], flattened, prefix="")

        return flattened

    def _flatten_recursive(self, obj: Any, target: dict[str, Any], prefix: str = "") -> None:
        """
        Recursively flatten nested dict structures.

        Extracts numeric/string values and brings them to top level.
        Skips deeply nested metadata structures.

        Args:
            obj: Object to flatten (dict, list, or primitive)
            target: Target dict to add flattened fields to
            prefix: Current key prefix (for nested keys)
        """
        if isinstance(obj, dict):
            for key, value in obj.items():
                # Skip metadata/structural keys
                if key in ["meta", "metadata", "raw_data", "debug_info"]:
                    continue

                # For primitives (numbers, strings, bools), add to target
                if isinstance(value, (int, float, str, bool, type(None))):
                    # Use simple key name (no prefix) for cleaner top-level access
                    target[key] = value
                # For nested dicts, recurse
                elif isinstance(value, dict):
                    self._flatten_recursive(value, target, prefix="")
                # For lists with single dict, extract that dict
                elif isinstance(value, list) and len(value) == 1 and isinstance(value[0], dict):
                    self._flatten_recursive(value[0], target, prefix="")

        elif isinstance(obj, list):
            # For numeric lists, take the first value or average
            if obj and all(isinstance(x, (int, float)) for x in obj):
                target[prefix] = obj[0] if len(obj) == 1 else sum(obj) / len(obj)

    def _extract_collected_data(self, crew_output: Any) -> dict[str, Any] | None:
        """
        Extract RAW tool outputs from crew for Python scoring.

        Bypasses AI-processed output to get actual tool results with raw metrics.
        AI generates scores (0.90), but Python scorer needs raw values (ROE=0.25).

        Args:
            crew_output: CrewAI crew execution result

        Returns:
            Dictionary of raw metrics for Python scoring, or None if extraction fails

        """
        try:
            self.logger.info(f"🔍 DEBUG: Starting extraction from crew_output (type={type(crew_output).__name__})")

            # Check crew_output attributes
            crew_attrs = [a for a in dir(crew_output) if not a.startswith('_')]
            self.logger.info(f"🔍 DEBUG: crew_output attributes: {crew_attrs[:20]}...")

            # Access tool outputs from tasks_output
            if not hasattr(crew_output, "tasks_output"):
                self.logger.error("❌ crew_output has no 'tasks_output' attribute!")
                return None

            if not crew_output.tasks_output:
                self.logger.error("❌ crew_output.tasks_output is empty!")
                return None

            self.logger.info(f"🔍 DEBUG: Found {len(crew_output.tasks_output)} tasks in tasks_output")

            # Get data_collection_task output (first task)
            data_task = crew_output.tasks_output[0]
            self.logger.info(f"🔍 DEBUG: Got first task from tasks_output")

            # DEBUG: Comprehensive task exploration
            self.logger.info(f"🔍 DEBUG: Task object type: {type(data_task).__name__}")
            task_attrs = [a for a in dir(data_task) if not a.startswith('_')]
            self.logger.info(f"🔍 DEBUG: Task attributes (non-private): {task_attrs}")

            # Check each attribute for potential data sources
            # NOTE: Removed 'json' from list - accessing it raises ValueError if output_json not set
            for attr in ['output', 'raw', 'pydantic', 'tool_output', 'result']:
                if hasattr(data_task, attr):
                    attr_value = getattr(data_task, attr)
                    self.logger.info(f"🔍 DEBUG: Task.{attr}: type={type(attr_value).__name__}")
                    # Special handling for raw - check if it's empty
                    if attr == 'raw':
                        if isinstance(attr_value, str):
                            self.logger.info(f"🔍 DEBUG:   Task.raw length: {len(attr_value)} chars")
                            if not attr_value:
                                self.logger.warning("⚠️ Task.raw is EMPTY STRING!")
                            else:
                                # Show preview with escaped newlines so we can see full content
                                preview = repr(attr_value[:500])  # repr() shows \n instead of actual newlines
                                self.logger.info(f"🔍 DEBUG:   Task.raw preview (repr): {preview}")
                    if attr == 'output' and attr_value:
                        output_attrs = [a for a in dir(attr_value) if not a.startswith('_')]
                        self.logger.info(f"🔍 DEBUG:   output attributes: {output_attrs}")

            # Look for tool outputs in the task.raw (task IS the TaskOutput)
            if hasattr(data_task, "raw") and data_task.raw:
                raw_output = data_task.raw
                self.logger.info(f"🔍 DEBUG: Found task.raw (length={len(raw_output)} chars)")

                if isinstance(raw_output, str):
                    import json
                    import re

                    cleaned = raw_output.strip()

                    # Remove markdown code fences if present
                    if cleaned.startswith('```'):
                        lines = cleaned.split('\n', 1)
                        cleaned = lines[1] if len(lines) > 1 else cleaned
                        cleaned = cleaned.rstrip('`').strip()
                        self.logger.info("🔍 Stripped markdown code fence")

                    # CRITICAL: Check if the output is already pure JSON (starts with {)
                    if cleaned.startswith('{'):
                        self.logger.info("🔍 Raw output is already JSON format")
                        # Ensure proper closing if malformed
                        open_braces = cleaned.count('{')
                        close_braces = cleaned.count('}')
                        if open_braces > close_braces:
                            missing = open_braces - close_braces
                            cleaned = cleaned + ('}' * missing)
                            self.logger.info(f"🔍 Fixed malformed JSON: added {missing} closing braces")
                    else:
                        # Try to extract JSON from Python assignment: context["x"] = {...}
                        match = re.search(r'=\s*(\{.+)', cleaned, re.DOTALL)  # More permissive: don't require closing }
                        if match:
                            cleaned = match.group(1).strip()
                            self.logger.info(f"🔍 Extracted JSON from assignment (length={len(cleaned)})")

                            # CRITICAL: Try to fix malformed JSON by ensuring proper closing
                            # Count braces and add missing closing braces
                            open_braces = cleaned.count('{')
                            close_braces = cleaned.count('}')
                            if open_braces > close_braces:
                                missing = open_braces - close_braces
                                cleaned = cleaned + ('}' * missing)
                                self.logger.info(f"🔍 Fixed malformed JSON: added {missing} closing braces")

                    # Try parsing as JSON
                    try:
                        parsed = json.loads(cleaned)
                        if isinstance(parsed, dict):
                            self.logger.info(f"✅ Parsed JSON with keys: {list(parsed.keys())[:10]}")

                            # CRITICAL: Unwrap 'collected_data' if present (some agents nest it)
                            if "collected_data" in parsed and len(parsed) == 1:
                                self.logger.info("🔍 Unwrapping 'collected_data' wrapper")
                                parsed = parsed["collected_data"]
                                self.logger.info(f"🔍 After unwrap, keys: {list(parsed.keys())[:10]}")

                            # CRITICAL: Flatten nested structures for Python scorer
                            # Scorer expects flat dict with fields like: current_price, roe, volatility, etc.
                            # But data comes nested in: quantitative_analysis.prices.current_price
                            flattened = self._flatten_collected_data(parsed)
                            self.logger.info(f"🔍 Flattened to {len(flattened)} top-level fields")

                            # DEBUG: Log what fields we actually have
                            available_fields = sorted([k for k in flattened.keys() if not k.startswith('_')])
                            self.logger.info(f"📋 Available fields: {available_fields}")

                            # DEBUG: Check for critical fields
                            critical_fields = ['current_price', 'roe', 'debt_to_equity', 'revenue_growth',
                                              'volatility', 'beta', 'expense_ratio', 'volume_24h']
                            missing = [f for f in critical_fields if f not in flattened]
                            if missing:
                                self.logger.warning(f"⚠️ Missing critical fields: {missing}")

                                # DEBUG: Check for similar field names that might be the data we need
                                for field in missing:
                                    similar = [k for k in flattened.keys() if field.replace('_', '') in k.lower().replace('_', '')
                                              or k.lower().replace('_', '') in field.replace('_', '')]
                                    if similar:
                                        self.logger.info(f"   → Possible match for '{field}': {similar}")

                            return flattened
                    except json.JSONDecodeError as e:
                        self.logger.warning(f"⚠️ JSON parse failed: {e}")
                        self.logger.info(f"Cleaned text preview: {cleaned[:300]}")

            # If pydantic output exists, try to extract raw metrics from it
            if hasattr(crew_output, "pydantic") and crew_output.pydantic:
                data = crew_output.pydantic
                if hasattr(data, "model_dump"):
                    data_dict = data.model_dump()
                elif hasattr(data, "dict"):
                    data_dict = data.dict()
                else:
                    data_dict = data if isinstance(data, dict) else None

                if data_dict:
                    self.logger.info(f"✅ Extracted pydantic data with keys: {list(data_dict.keys())[:5]}...")

                    # DEBUG: Comprehensive structure mapping
                    import json

                    # Log complete structure (truncated for readability)
                    full_json = json.dumps(data_dict, indent=2, default=str)
                    self.logger.info(f"🔍 DEBUG: Pydantic structure ({len(full_json)} chars):\n{full_json[:2000]}...")

                    # Map out all top-level keys and their types
                    self.logger.info("🔍 DEBUG: Structure map:")
                    for key, value in data_dict.items():
                        value_type = type(value).__name__
                        if isinstance(value, dict):
                            nested_keys = list(value.keys())[:5]
                            self.logger.info(f"🔍 DEBUG:   {key}: dict with keys {nested_keys}...")
                        elif isinstance(value, list):
                            self.logger.info(f"🔍 DEBUG:   {key}: list with {len(value)} items")
                        else:
                            self.logger.info(f"🔍 DEBUG:   {key}: {value_type} = {str(value)[:100]}")

                    # Check if metrics are nested in detailed_analysis
                    if "detailed_analysis" in data_dict:
                        detailed = data_dict["detailed_analysis"]
                        self.logger.info(f"🔍 DEBUG: Found detailed_analysis (type={type(detailed).__name__})")

                        if isinstance(detailed, dict):
                            self.logger.info(f"🔍 DEBUG:   detailed_analysis keys: {list(detailed.keys())}")

                            # Check component_scores (likely AI-generated scores, not raw values)
                            if "component_scores" in detailed:
                                scores = detailed["component_scores"]
                                self.logger.info(f"🔍 DEBUG:   component_scores type: {type(scores).__name__}")
                                if isinstance(scores, dict):
                                    self.logger.info(f"🔍 DEBUG:   component_scores content: {json.dumps(scores, indent=4, default=str)}")

                    return data_dict

            self.logger.warning("Could not extract tool outputs - no raw data found")
            return None

        except Exception as e:
            self.logger.error(f"Failed to extract tool outputs: {e}", exc_info=True)
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
