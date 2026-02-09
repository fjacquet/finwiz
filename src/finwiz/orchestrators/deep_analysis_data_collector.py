"""Data collection for deep analysis using Python tools."""

import json
from typing import Any

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class DeepAnalysisDataCollector:
    """Collects raw financial data using Python tool calls (not AI agents)."""

    def __init__(self, state: Any) -> None:
        self.state = state
        self.logger = get_logger(self.__class__.__name__)
        self._prefetched_data: dict[str, Any] | None = None

        # Initialize DataSourceOrchestrator for multi-source data acquisition
        from finwiz.data.data_source_orchestrator import DataSourceOrchestrator

        self.data_orchestrator = DataSourceOrchestrator(
            total_timeout=10.0,
            per_source_timeout=3.0,
            enable_validation=True,
        )

    def collect_data(
        self,
        ticker: str,
        asset_class: str,
        batch_enabled: bool = False,
        prefetched_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Python directly calls tools to collect raw financial data.

        Ensures 100% reliable data collection - agents can't "forget" to run tools.
        Python gets raw facts (current_price=150.0, roe=0.25) for scoring.

        Args:
            ticker: Ticker symbol
            asset_class: Asset class (stock/etf/crypto)
            batch_enabled: Whether batch mode is enabled
            prefetched_data: Batch-prefetched data dict (from BatchDataPreFetcher)

        Returns:
            Dictionary with raw metrics for Python scoring
        """
        self._prefetched_data = prefetched_data
        self.logger.info(f"🐍 Python collecting data for {ticker} ({asset_class})")

        collected_data = {
            "ticker": ticker,
            "asset_class": asset_class,
            "collection_timestamp": self.state.full_date,
        }

        # Step 0: Basic ticker info
        collected_data = self._collect_ticker_info(ticker, collected_data)

        # Step 0.5: Asset-specific data
        collected_data = self._collect_asset_specific_data(ticker, asset_class, collected_data)

        # Step 1: Quantitative analysis
        collected_data = self._collect_quantitative_data(ticker, asset_class, collected_data)

        # Step 2: Sentiment analysis
        collected_data = self._collect_sentiment_data(ticker, asset_class, collected_data)

        # Step 3: SEC analysis (stocks only)
        if asset_class.lower() == "stock":
            collected_data = self._collect_sec_data(ticker, collected_data)

        # Flatten nested structures for Python scorer
        flattened = self.flatten_collected_data(collected_data)

        self.logger.info(f"✅ Python collected {len(flattened)} fields: {list(flattened.keys())[:10]}")
        return flattened

    def _collect_ticker_info(self, ticker: str, collected_data: dict[str, Any]) -> dict[str, Any]:
        """Collect basic ticker info from Yahoo Finance or prefetched data."""
        # Use prefetched data if available for this ticker
        if self._prefetched_data and ticker in self._prefetched_data:
            yf_data = self._prefetched_data[ticker].get("yahoo_finance", {})
            if yf_data and not yf_data.get("failed", False):
                self.logger.info(f"⚡ Using prefetched Yahoo Finance data for {ticker}")
                if "current_price" in yf_data:
                    collected_data["current_price"] = yf_data["current_price"]
                collected_data["ticker_info"] = yf_data
                collected_data["ticker_info"]["data_source"] = "prefetched"
                return collected_data

        from finwiz.tools.yahoo_finance_ticker_info_tool import YahooFinanceTickerInfoTool

        try:
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

        return collected_data

    def _collect_asset_specific_data(self, ticker: str, asset_class: str, collected_data: dict[str, Any]) -> dict[str, Any]:
        """Collect asset-specific data based on asset class."""
        try:
            if asset_class.lower() == "crypto":
                return self._collect_crypto_data(ticker, collected_data)
            elif asset_class.lower() == "stock":
                return self._collect_stock_data(ticker, collected_data)
            elif asset_class.lower() == "etf":
                return self._collect_etf_data(ticker, collected_data)
        except Exception as e:
            self.logger.error(f"❌ Asset-specific data collection failed: {e}", exc_info=True)
            if asset_class.lower() == "crypto":
                collected_data["volume_24h"] = 1e9
                collected_data["age_years"] = 3.0
                collected_data["market_cap"] = 10e9
                collected_data["crypto_info"] = {}
            elif asset_class.lower() == "etf":
                collected_data["expense_ratio"] = None
            else:
                collected_data["company_info"] = {}

        return collected_data

    def _collect_crypto_data(self, ticker: str, collected_data: dict[str, Any]) -> dict[str, Any]:
        """Collect crypto-specific data."""
        from finwiz.tools.enhanced_crypto_tool import EnhancedCryptoAnalysisTool

        self.logger.info(f"🐍 Calling EnhancedCryptoAnalysisTool for {ticker}")
        crypto_tool = EnhancedCryptoAnalysisTool()
        crypto_result = crypto_tool._run(
            symbol=ticker,
            include_thesis=False,
            include_risk_assessment=False,
            include_perplexity=False,
        )

        if isinstance(crypto_result, dict):
            crypto_data = crypto_result.get("crypto_data", crypto_result)
            collected_data["volume_24h"] = crypto_data.get("total_volume", crypto_data.get("volume_24h", 0.0))

            market_cap_raw = crypto_data.get("market_cap", 0.0)
            collected_data["market_cap"] = market_cap_raw if market_cap_raw > 0 else 10e9

            collected_data["circulating_supply"] = crypto_data.get("circulating_supply", 0.0)
            collected_data["max_supply"] = crypto_data.get("max_supply", crypto_data.get("total_supply", 0.0))

            # Age mapping for known cryptos
            age_mapping = {
                "BTC": 15.0,
                "BTC-USD": 15.0,
                "ETH": 9.0,
                "ETH-USD": 9.0,
                "ADA": 7.0,
                "ADA-USD": 7.0,
                "SOL": 4.0,
                "SOL-USD": 4.0,
                "AVAX": 4.0,
                "AVAX-USD": 4.0,
                "DOT": 4.0,
                "DOT-USD": 4.0,
            }
            ticker_base = ticker.replace("-USD", "").upper()
            collected_data["age_years"] = age_mapping.get(ticker_base, 3.0)

            self.logger.info(f"✅ Got crypto data: volume_24h={collected_data['volume_24h']}, age_years={collected_data['age_years']}")
            collected_data["crypto_info"] = crypto_result
        else:
            collected_data["volume_24h"] = 1e9
            collected_data["age_years"] = 3.0
            collected_data["market_cap"] = 10e9

        return collected_data

    def _collect_stock_data(self, ticker: str, collected_data: dict[str, Any]) -> dict[str, Any]:
        """Collect stock-specific fundamental data using DataSourceOrchestrator."""
        import asyncio

        from finwiz.tools.yahoo_finance_company_info_tool import YahooFinanceCompanyInfoTool

        self.logger.info(f"🐍 Using DataSourceOrchestrator for {ticker} fundamental data")

        sector = None
        if "ticker_info" in collected_data and isinstance(collected_data["ticker_info"], dict):
            sector = collected_data["ticker_info"].get("sector")

        try:
            # Always use asyncio.run() when called from sync context (thread pool)
            # The caller (analyze_single_sync) runs in ThreadPoolExecutor, so no event loop exists
            orchestration_result = asyncio.run(self.data_orchestrator.get_fundamental_data(ticker, sector))

            # Extract metrics
            if orchestration_result.return_on_equity is not None:
                collected_data["roe"] = orchestration_result.return_on_equity
            if orchestration_result.debt_to_equity is not None:
                collected_data["debt_to_equity"] = orchestration_result.debt_to_equity
            if orchestration_result.revenue_growth is not None:
                collected_data["revenue_growth"] = orchestration_result.revenue_growth
            if orchestration_result.profit_margin is not None:
                collected_data["profit_margin"] = orchestration_result.profit_margin

            collected_data["data_lineage"] = orchestration_result.lineage.to_dict()
            collected_data["data_confidence"] = orchestration_result.confidence

        except Exception as orch_error:
            self.logger.error(f"❌ DataSourceOrchestrator failed: {orch_error}", exc_info=True)
            # Fallback to Yahoo Finance
            company_tool = YahooFinanceCompanyInfoTool()
            company_result = company_tool._run(ticker=ticker)

            if "financial_metrics" in company_result:
                metrics = company_result["financial_metrics"]
                for field, key in [("roe", "return_on_equity"), ("debt_to_equity", "debt_to_equity"), ("revenue_growth", "revenue_growth"), ("profit_margin", "profit_margin")]:
                    if key in metrics:
                        collected_data[field] = metrics[key]

            collected_data["company_info"] = company_result

        return collected_data

    def _collect_etf_data(self, ticker: str, collected_data: dict[str, Any]) -> dict[str, Any]:
        """Collect ETF-specific data, with fallback for European ETFs missing expense_ratio."""
        from finwiz.quantitative.etf.etf_expense_fallback import get_fallback_expense_ratio

        self.logger.info(f"Collecting ETF-specific data for {ticker}")

        # Try to extract expense_ratio from ticker_info (yfinance)
        expense_ratio = None
        if "ticker_info" in collected_data and isinstance(collected_data["ticker_info"], dict):
            raw_ratio = collected_data["ticker_info"].get("expense_ratio")
            if raw_ratio is not None and raw_ratio != "N/A":
                try:
                    expense_ratio = float(raw_ratio)
                except (ValueError, TypeError):
                    pass

        # Fallback to YAML config for European ETFs
        if expense_ratio is None:
            expense_ratio = get_fallback_expense_ratio(ticker)
            if expense_ratio is not None:
                self.logger.info(f"Using fallback expense_ratio for {ticker}: {expense_ratio}")

        if expense_ratio is not None:
            collected_data["expense_ratio"] = expense_ratio

        return collected_data

    def _collect_quantitative_data(self, ticker: str, asset_class: str, collected_data: dict[str, Any]) -> dict[str, Any]:
        """Collect quantitative analysis data."""
        from finwiz.tools.quantitative_analysis_tool import QuantitativeAnalysisTool

        try:
            self.logger.info(f"🐍 Calling QuantitativeAnalysisTool for {ticker}")
            quant_tool = QuantitativeAnalysisTool()
            quant_result = quant_tool._run(symbol=ticker, asset_class=asset_class, analysis_type="comprehensive", timeframe="1y", strategy="sma_crossover")

            # Handle different response types
            if isinstance(quant_result, dict):
                quant_data = quant_result
            elif isinstance(quant_result, str):
                # Check if it's valid JSON (starts with { or [)
                stripped = quant_result.strip()
                if stripped and (stripped.startswith("{") or stripped.startswith("[")):
                    quant_data = json.loads(stripped)
                else:
                    # Plain text error message from tool
                    self.logger.warning(f"⚠️ Quantitative tool returned non-JSON: {quant_result[:100]}")
                    quant_data = {"error": quant_result, "symbol": ticker}
            else:
                quant_data = {}

            collected_data["quantitative_analysis"] = quant_data
            if "error" not in quant_data:
                self.logger.info(f"✅ Got quantitative data with keys: {list(quant_data.keys())[:5]}")

        except Exception as e:
            self.logger.error(f"❌ Quantitative analysis failed: {e}", exc_info=True)
            collected_data["quantitative_analysis"] = {}

        return collected_data

    def _collect_sentiment_data(self, ticker: str, asset_class: str, collected_data: dict[str, Any]) -> dict[str, Any]:
        """Collect sentiment analysis data."""
        from finwiz.tools.enhanced_sentiment_tool import EnhancedSentimentAnalysisTool

        try:
            self.logger.info(f"🐍 Calling SentimentAnalysisTool for {ticker}")
            sentiment_tool = EnhancedSentimentAnalysisTool()
            sentiment_result = sentiment_tool._run(ticker=ticker, asset_type=asset_class, max_articles=20, days_back=30)

            if isinstance(sentiment_result, dict):
                collected_data["sentiment_score"] = sentiment_result.get("sentiment_score", 0.0)
                collected_data["overall_sentiment"] = sentiment_result.get("overall_sentiment", "neutral")
                collected_data["sentiment_confidence"] = sentiment_result.get("confidence", 0.0)
                collected_data["sentiment_analysis"] = sentiment_result
                self.logger.info(f"✅ Got sentiment: score={collected_data['sentiment_score']:.3f}")
            else:
                collected_data["sentiment_score"] = 0.0

        except Exception as e:
            self.logger.error(f"❌ Sentiment analysis failed: {e}", exc_info=True)
            collected_data["sentiment_analysis"] = {}
            collected_data["sentiment_score"] = 0.0

        return collected_data

    def _collect_sec_data(self, ticker: str, collected_data: dict[str, Any]) -> dict[str, Any]:
        """Collect SEC filing data for stocks."""
        from finwiz.tools.enhanced_sec_tool import EnhancedSECAnalysisTool

        try:
            self.logger.info(f"🐍 Calling SEC Analysis for {ticker}")
            sec_tool = EnhancedSECAnalysisTool()
            sec_result = sec_tool._run(
                ticker=ticker,
                form_type="10-K",
                sections=["Item 1", "Item 1A", "Item 7"],
                risk_assessment=True,
                include_perplexity=False,
            )

            if isinstance(sec_result, str):
                if sec_result.startswith("Error:") or sec_result.startswith("No SEC"):
                    collected_data["sec_analysis"] = {"error": sec_result}
                else:
                    collected_data["sec_analysis"] = {"analysis_text": sec_result}
            else:
                collected_data["sec_analysis"] = sec_result

        except Exception as e:
            self.logger.error(f"❌ SEC analysis failed: {e}", exc_info=True)
            collected_data["sec_analysis"] = {}

        return collected_data

    def flatten_collected_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Flatten nested tool output structures for Python scorer.

        The scorer expects flat dict with fields like: current_price, roe, volatility, beta.
        """
        flattened = {}

        # Keep top-level primitives
        for key, value in data.items():
            if key not in ["ticker_info", "company_info", "quantitative_analysis", "sec_analysis", "sentiment_analysis", "ticker_validation"]:
                if isinstance(value, (int, float, str, bool, type(None))):
                    flattened[key] = value

        # First, extract fundamental beta from ticker_info (yfinance source)
        yfinance_beta = None
        if "ticker_info" in data and isinstance(data["ticker_info"], dict):
            yfinance_beta = data["ticker_info"].get("beta")
            if yfinance_beta is not None and yfinance_beta != "N/A":
                flattened["beta"] = yfinance_beta
                self.logger.debug(f"Using yfinance fundamental beta: {yfinance_beta}")

        # Extract from quantitative_analysis
        if "quantitative_analysis" in data and isinstance(data["quantitative_analysis"], dict):
            quant = data["quantitative_analysis"]

            if "performance_metrics" in quant and isinstance(quant["performance_metrics"], dict):
                perf = quant["performance_metrics"]
                for field in ["volatility", "max_drawdown", "sharpe_ratio", "total_return"]:
                    if field in perf and perf[field] is not None:
                        flattened[field] = perf[field]

                # Use calculated beta ONLY if yfinance beta was not available
                # AND calculated beta is not the default value (1.0)
                calc_beta = perf.get("beta")
                if calc_beta is not None and "beta" not in flattened:
                    if calc_beta != 1.0:
                        flattened["beta"] = calc_beta
                        self.logger.debug(f"Using calculated beta: {calc_beta}")
                    else:
                        self.logger.debug("Skipping default calculated beta (1.0)")

            if "technical_analysis" in quant and isinstance(quant["technical_analysis"], dict):
                tech = quant["technical_analysis"]
                if "technical_indicators" in tech and isinstance(tech["technical_indicators"], dict):
                    indicators = tech["technical_indicators"]
                    for field in ["rsi", "macd", "macd_signal", "moving_avg_50", "moving_avg_200", "sma_50", "sma_200"]:
                        if field in indicators and indicators[field] is not None:
                            flattened[field] = indicators[field]

                    # Map alternative naming
                    if "sma_50" in flattened and "moving_avg_50" not in flattened:
                        flattened["moving_avg_50"] = flattened["sma_50"]
                    if "sma_200" in flattened and "moving_avg_200" not in flattened:
                        flattened["moving_avg_200"] = flattened["sma_200"]

        # Process nested sections
        for section in ["ticker_info", "company_info", "quantitative_analysis", "sec_analysis", "sentiment_analysis"]:
            if section in data and isinstance(data[section], dict):
                self._flatten_recursive(data[section], flattened)

        # Ensure expense_ratio is extracted from ticker_info if not already present
        if "expense_ratio" not in flattened and "ticker_info" in data and isinstance(data["ticker_info"], dict):
            raw_ratio = data["ticker_info"].get("expense_ratio")
            if raw_ratio is not None and raw_ratio != "N/A":
                try:
                    flattened["expense_ratio"] = float(raw_ratio)
                except (ValueError, TypeError):
                    pass

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
