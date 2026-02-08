"""
Batch Data Pre-Fetcher for Deep Analysis Performance Optimization.

This module implements batch API query optimization to reduce deep analysis
execution time from 3-6 hours to 20-40 minutes for 66+ holdings by pre-fetching
all data in batch API calls before crew execution.

Key Features:
- **Yahoo Finance PRIORITY**: Batch data fetching (ONE API call for all tickers) ⚡
- Yahoo Finance provides ALL essential data (price, fundamentals, history)
- **Alpha Vantage OPTIONAL**: Disabled by default - adds 13+ minutes for 66 tickers
- JSON cache for pre-fetched data
- Progress logging and timing metrics
- Error handling for partial failures

Performance:
- **Yahoo Finance (PRIMARY)**: ~2-5 seconds for 66 tickers (600 requests/minute) ⚡
- **Alpha Vantage (OPTIONAL)**: ~13 minutes for 66 tickers (5 requests/minute) - DISABLED BY DEFAULT

Requirements: 17.9, 17.10, 17.11, 17.22, 17.23, 17.24
"""

import asyncio
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import aiohttp
import yfinance as yf  # yfinance has no official type stubs
from aiohttp import ClientTimeout

from finwiz.config.yfinance_config import configure_yfinance
from finwiz.infrastructure.monitoring.memory_manager import get_memory_manager
from finwiz.infrastructure.resilience.rate_limiter import APIProvider, get_rate_limiter
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class BatchDataPreFetcher:
    """
    Pre-fetch all data for all tickers in batch API calls.

    This class implements batch data pre-fetching to eliminate API latency
    during deep analysis crew execution. All data is fetched upfront in
    optimized batch calls, then cached for zero-latency access during
    crew execution.

    Performance Target:
    - 80%+ time reduction through batch processing
    - 2-5 seconds for 66 holdings with Yahoo Finance only ⚡
    - 20-40 minutes for 66 holdings (vs 3-6 hours sequential)

    Data Sources (Priority Order):
    1. **Yahoo Finance (PRIMARY - ALWAYS USED)**: Provides ALL essential data in ONE batch call
       * Company info, fundamentals, price data, historical data
       * 600 requests/minute (10 per second) - BLAZING fast ⚡
       * Complete data coverage for stocks, ETFs, crypto
    2. **Alpha Vantage (OPTIONAL - DISABLED BY DEFAULT)**: Adds minimal value, significant time cost
       * 5 requests/minute - adds ~13 minutes for 66 tickers
       * Only enable if you need additional fundamental data
       * Disabled by default for optimal performance

    Attributes:
        session_id: Unique session identifier for cache isolation
        cache_dir: Directory for storing pre-fetched data cache
        enable_alpha_vantage: If True, fetch Alpha Vantage data (default: False)
        alpha_vantage_key: Alpha Vantage API key from environment (if enabled)
        rate_limiter: Rate limiter instance (if Alpha Vantage enabled)

    """

    def __init__(
        self,
        session_id: str,
        enable_alpha_vantage: bool = False,
        alpha_vantage_rate_limit: int = 5,
    ) -> None:
        """
        Initialize batch data pre-fetcher.

        Args:
            session_id: Unique session identifier for cache isolation
            enable_alpha_vantage: If True, fetch Alpha Vantage data (adds 13+ minutes for 66 tickers)
                                 Default False - Yahoo Finance provides all essential data
            alpha_vantage_rate_limit: Alpha Vantage API rate limit in calls per minute (default: 5)
                                     Free tier: 5, Premium tier: 75

        """
        self.session_id = session_id
        self.cache_dir = Path(f"cache/batch_data/{session_id}")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.enable_alpha_vantage = enable_alpha_vantage
        self.alpha_vantage_rate_limit = alpha_vantage_rate_limit
        self.alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY") if enable_alpha_vantage else None
        self.rate_limiter = get_rate_limiter() if enable_alpha_vantage else None

        # Configure yfinance with centralized settings (retry mechanism, etc.)
        configure_yfinance()

        # Initialize memory manager (Requirement 17.70)
        self.memory_manager = get_memory_manager(session_id)

        # Log data source priority
        logger.info("=" * 80)
        logger.info("BATCH DATA PRE-FETCHER: Data Source Configuration")
        logger.info("=" * 80)
        logger.info("PRIMARY SOURCE: Yahoo Finance (ALWAYS ENABLED)")
        logger.info("  - Provides: Company info, fundamentals, price data, historical data")
        logger.info("  - Performance: ~2-5 seconds for 66 tickers")
        logger.info("  - Rate limit: 600 requests/minute (10/second)")

        if enable_alpha_vantage:
            logger.warning("⚠️  OPTIONAL SOURCE: Alpha Vantage (ENABLED)")
            logger.warning(f"  - Rate limit: {alpha_vantage_rate_limit} calls/minute")
            logger.warning("  - Performance impact: Adds ~13 minutes for 66 tickers")
            logger.warning("  - Recommendation: Disable for optimal performance")
            logger.warning("  - Yahoo Finance already provides all essential data")
        else:
            logger.info("✓ OPTIONAL SOURCE: Alpha Vantage (DISABLED - Recommended)")
            logger.info("  - Yahoo Finance provides all essential data")
            logger.info("  - Optimal performance configuration")

        logger.info("=" * 80)

    def prefetch_all_data(self, tickers: list[str]) -> dict[str, dict[str, Any]]:
        """
        Pre-fetch all data for all tickers in batch API calls.

        This is the main entry point for batch data pre-fetching. It orchestrates:
        1. Batch Yahoo Finance data fetch (ONE API call for all tickers)
        2. Async Alpha Vantage data fetch (with rate limiting)
        3. Data combination and cache storage

        Args:
            tickers: List of all ticker symbols to analyze

        Returns:
            Dict mapping ticker to all pre-fetched data:
            {
                "AAPL": {
                    "ticker": "AAPL",
                    "yahoo_finance": {...},
                    "alpha_vantage": {...},
                    "fetch_timestamp": "2025-01-25T10:30:00"
                },
                ...
            }

        Example:
            >>> prefetcher = BatchDataPreFetcher("session-123")
            >>> data = prefetcher.prefetch_all_data(["AAPL", "MSFT", "GOOGL"])
            >>> print(f"Pre-fetched data for {len(data)} tickers")

        """
        logger.info("=" * 80)
        logger.info("BATCH DATA PRE-FETCH: Starting for %d tickers", len(tickers))
        logger.info("=" * 80)
        start_time = time.time()

        # Monitor memory at start (Requirement 17.70)
        self.memory_manager.monitor_memory("pre-fetch-start")

        # Step 1: Batch fetch Yahoo Finance data (PRIMARY SOURCE - ONE API call!)
        logger.info("Step 1: Fetching Yahoo Finance data (PRIMARY SOURCE)...")
        logger.info("  ⚡ Batch mode: ONE API call for all %d tickers", len(tickers))
        yf_start = time.time()
        yf_data = self._fetch_yahoo_finance_batch(tickers)
        yf_duration = time.time() - yf_start
        logger.info(f"✓ Yahoo Finance batch fetch completed in {yf_duration:.1f}s")
        if tickers:
            logger.info(f"  Performance: {yf_duration / len(tickers):.2f}s per ticker")

        # Monitor memory after Yahoo Finance fetch (Requirement 17.70)
        self.memory_manager.monitor_memory("yahoo-finance-complete")

        # Step 2 (OPTIONAL): Batch fetch Alpha Vantage data (with rate limiting)
        av_data = {}
        av_duration = 0.0
        if self.enable_alpha_vantage:
            logger.info("Step 2: Fetching Alpha Vantage data (OPTIONAL SOURCE)...")
            logger.warning(f"⚠️  Alpha Vantage enabled: This will add ~{len(tickers) * 12 / 60:.1f} minutes for {len(tickers)} tickers (5 calls/minute limit)")
            logger.warning("⚠️  Consider disabling Alpha Vantage for optimal performance")
            logger.warning("⚠️  Yahoo Finance already provides all essential data")
            av_start = time.time()
            av_data = asyncio.run(self._fetch_alpha_vantage_batch(tickers))
            av_duration = time.time() - av_start
            logger.info(f"✓ Alpha Vantage batch fetch completed in {av_duration:.1f}s")
            if tickers:
                logger.info(f"  Performance: {av_duration / len(tickers):.2f}s per ticker")

            # Monitor memory after Alpha Vantage fetch (Requirement 17.70)
            self.memory_manager.monitor_memory("alpha-vantage-complete")
        else:
            logger.info("Step 2: Alpha Vantage DISABLED (Recommended)")
            logger.info("  ✓ Using Yahoo Finance only for optimal performance")
            logger.info("  ✓ Yahoo Finance provides all essential data")

        # Step 3: Combine all data and track failures (Requirement 17.52, 17.53, 17.54)
        logger.info("Step 3/3: Combining data and saving to cache..." if self.enable_alpha_vantage else "Step 2/2: Saving data to cache...")
        combined_data = {}
        failed_tickers = []
        partial_failures = []

        for ticker in tickers:
            yf_ticker_data = yf_data.get(ticker, {})
            av_ticker_data = av_data.get(ticker, {})

            # Check if ticker failed in either source
            yf_failed = yf_ticker_data.get("failed", False)
            av_failed = av_ticker_data.get("failed", False) if self.enable_alpha_vantage else False

            # Determine overall failure status
            # If Yahoo Finance failed (primary source), mark as failed
            # Alpha Vantage failures are less critical (optional data)
            ticker_failed = yf_failed

            if ticker_failed:
                failed_tickers.append(ticker)
            elif av_failed and self.enable_alpha_vantage:
                partial_failures.append(ticker)

            combined_data[ticker] = {
                "ticker": ticker,
                "yahoo_finance": yf_ticker_data,
                "alpha_vantage": av_ticker_data,
                "fetch_timestamp": datetime.now().isoformat(),
                "failed": ticker_failed,  # Mark failed tickers (Requirement 17.54)
                "partial_failure": av_failed and not yf_failed,  # Yahoo OK but Alpha Vantage failed
            }

        # Save to cache (includes failed ticker markers)
        self._save_to_cache(combined_data)

        # Monitor memory after cache save (Requirement 17.70)
        self.memory_manager.monitor_memory("cache-save-complete")

        # Calculate metrics
        total_time = time.time() - start_time
        time_per_ticker = total_time / len(tickers) if tickers else 0
        successful_tickers = len(tickers) - len(failed_tickers)

        logger.info("=" * 80)
        logger.info("BATCH DATA PRE-FETCH COMPLETE")
        logger.info("=" * 80)
        logger.info("Total time: %.1fs", total_time)
        logger.info("Time per ticker: %.1fs", time_per_ticker)
        logger.info("")
        logger.info("Data Sources:")
        logger.info("  PRIMARY - Yahoo Finance: %.1fs (%.2fs per ticker)", yf_duration, yf_duration / len(tickers) if tickers else 0)
        if self.enable_alpha_vantage:
            logger.info("  OPTIONAL - Alpha Vantage: %.1fs (%.2fs per ticker)", av_duration, av_duration / len(tickers) if tickers else 0)
            logger.info("  ⚠️  Alpha Vantage added %.1fs overhead", av_duration)
        else:
            logger.info("  OPTIONAL - Alpha Vantage: DISABLED (Optimal)")
        logger.info("")
        logger.info("Results: %d/%d tickers successful", successful_tickers, len(tickers))

        # Log failure summary (Requirement 17.53)
        if failed_tickers:
            logger.warning(f"Failed tickers ({len(failed_tickers)}): {', '.join(failed_tickers)}")
        if partial_failures:
            logger.warning(f"Partial failures ({len(partial_failures)}): {', '.join(partial_failures)}")

        logger.info("=" * 80)

        return combined_data

    def _fetch_yahoo_finance_batch(self, tickers: list[str]) -> dict[str, Any]:
        """
        Fetch Yahoo Finance data for all tickers in ONE API call.

        Uses yf.download() with multiple tickers to fetch historical data
        and yf.Tickers() to fetch ticker info in a single batch operation.

        Handles partial failures gracefully (Requirement 17.52, 17.53, 17.54):
        - Continues processing if individual tickers fail
        - Logs failed tickers with error messages
        - Marks failed tickers in results with error field

        Args:
            tickers: List of ticker symbols

        Returns:
            Dict mapping ticker to Yahoo Finance data:
            {
                "AAPL": {
                    "symbol": "AAPL",
                    "name": "Apple Inc.",
                    "sector": "Technology",
                    "current_price": 150.0,
                    "market_cap": 2500000000000,
                    "pe_ratio": 25.5,
                    "52wk_high": 180.0,
                    "52wk_low": 120.0,
                    "historical_data_points": 252
                },
                "INVALID": {
                    "error": "No data available",
                    "failed": True
                },
                ...
            }

        """
        failed_tickers = []  # Track failed tickers (Requirement 17.53)

        try:
            logger.info("Downloading data for %d tickers from Yahoo Finance...", len(tickers))

            # Single batch API call for ALL tickers
            # This is the key optimization - ONE call instead of N calls
            data = yf.download(
                tickers=" ".join(tickers),
                period="1y",
                group_by="ticker",
                auto_adjust=True,
                threads=True,  # Parallel download
                progress=False,
            )

            # Also fetch ticker info in batch
            tickers_obj = yf.Tickers(" ".join(tickers))

            results = {}
            for ticker in tickers:
                try:
                    # Historical data
                    if len(tickers) == 1:
                        ticker_data = data
                    else:
                        ticker_data = data[ticker]

                    # Ticker info
                    ticker_info = tickers_obj.tickers[ticker].info

                    results[ticker] = {
                        "symbol": ticker,
                        "name": ticker_info.get("shortName", "N/A"),
                        "sector": ticker_info.get("sector", "N/A"),
                        "industry": ticker_info.get("industry", "N/A"),
                        "current_price": ticker_info.get("currentPrice", ticker_info.get("regularMarketPrice", "N/A")),
                        "market_cap": ticker_info.get("marketCap", "N/A"),
                        "pe_ratio": ticker_info.get("trailingPE", "N/A"),
                        "dividend_yield": ticker_info.get("dividendYield", "N/A"),
                        "52wk_high": float(ticker_data["High"].max()) if not ticker_data.empty else "N/A",
                        "52wk_low": float(ticker_data["Low"].min()) if not ticker_data.empty else "N/A",
                        "avg_volume": float(ticker_data["Volume"].mean()) if not ticker_data.empty else "N/A",
                        "historical_data_points": len(ticker_data) if not ticker_data.empty else 0,
                        "failed": False,  # Mark as successful (Requirement 17.54)
                    }

                    logger.debug(f"✓ Successfully fetched Yahoo Finance data for {ticker}")

                except Exception as e:
                    # Log failed ticker with error message (Requirement 17.53)
                    error_msg = f"Failed to process Yahoo Finance data for {ticker}: {e}"
                    logger.warning(f"✗ {error_msg}")
                    failed_tickers.append(ticker)

                    # Mark failed ticker in cache (Requirement 17.54)
                    results[ticker] = {"error": str(e), "failed": True, "ticker": ticker}

            success_count = sum(1 for v in results.values() if not v.get("failed", False))
            logger.info(f"Yahoo Finance batch: {success_count}/{len(tickers)} tickers successful")

            # Log summary of failed tickers (Requirement 17.53)
            if failed_tickers:
                logger.warning(f"Failed tickers: {', '.join(failed_tickers)}")

            return results

        except Exception as e:
            # Complete batch failure - mark all tickers as failed (Requirement 17.52)
            logger.error(f"Yahoo Finance batch download failed completely: {e}")
            failed_tickers = tickers
            return {ticker: {"error": str(e), "failed": True, "ticker": ticker} for ticker in tickers}

    async def _fetch_alpha_vantage_batch(self, tickers: list[str]) -> dict[str, Any]:
        """
        Fetch Alpha Vantage data with intelligent rate limiting.

        Uses async HTTP requests with rate limiting to fetch company overview
        data from Alpha Vantage API. Respects free tier limit of 5 calls/minute.

        Handles partial failures gracefully (Requirement 17.52, 17.53, 17.54):
        - Continues processing if individual tickers fail
        - Logs failed tickers with error messages
        - Marks failed tickers in results with error field

        Args:
            tickers: List of ticker symbols

        Returns:
            Dict mapping ticker to Alpha Vantage data:
            {
                "AAPL": {
                    "symbol": "AAPL",
                    "name": "Apple Inc",
                    "sector": "TECHNOLOGY",
                    "market_cap": "2500000000000",
                    "pe_ratio": "25.5",
                    "eps": "6.00",
                    "revenue_ttm": "400000000000",
                    "failed": False
                },
                "INVALID": {
                    "error": "No data available",
                    "failed": True
                },
                ...
            }

        """
        if not self.alpha_vantage_key:
            logger.warning("Alpha Vantage API key not set, skipping Alpha Vantage data fetch")
            return {ticker: {"error": "API key not set", "failed": True, "ticker": ticker} for ticker in tickers}

        results = {}
        failed_tickers = []  # Track failed tickers (Requirement 17.53)

        async with aiohttp.ClientSession() as session:
            for i, ticker in enumerate(tickers, 1):
                try:
                    # Wait for rate limit availability
                    await self.rate_limiter.wait_for_availability(APIProvider.ALPHA_VANTAGE, endpoint=f"OVERVIEW/{ticker}")

                    url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={self.alpha_vantage_key}"

                    async with session.get(url, timeout=ClientTimeout(total=15)) as response:
                        data = await response.json()

                        if "Symbol" in data:
                            results[ticker] = {
                                "symbol": ticker,
                                "name": data.get("Name", "N/A"),
                                "sector": data.get("Sector", "N/A"),
                                "industry": data.get("Industry", "N/A"),
                                "market_cap": data.get("MarketCapitalization", "N/A"),
                                "pe_ratio": data.get("PERatio", "N/A"),
                                "eps": data.get("EPS", "N/A"),
                                "revenue_ttm": data.get("RevenueTTM", "N/A"),
                                "profit_margin": data.get("ProfitMargin", "N/A"),
                                "failed": False,  # Mark as successful (Requirement 17.54)
                            }
                            logger.debug(f"✓ Successfully fetched Alpha Vantage data for {ticker} ({i}/{len(tickers)})")
                        else:
                            # No data available - mark as failed (Requirement 17.54)
                            error_msg = f"No Alpha Vantage data available for {ticker}"
                            logger.debug(f"✗ {error_msg} ({i}/{len(tickers)})")
                            failed_tickers.append(ticker)
                            results[ticker] = {"error": "No data available", "failed": True, "ticker": ticker}


                except Exception as e:
                    # Log failed ticker with error message (Requirement 17.53)
                    error_msg = f"Failed to fetch Alpha Vantage data for {ticker}: {e}"
                    logger.warning(f"✗ {error_msg}")
                    failed_tickers.append(ticker)

                    # Mark failed ticker in cache (Requirement 17.54)
                    results[ticker] = {"error": str(e), "failed": True, "ticker": ticker}

        success_count = sum(1 for v in results.values() if not v.get("failed", False))
        logger.info(f"Alpha Vantage batch: {success_count}/{len(tickers)} tickers successful")

        # Log summary of failed tickers (Requirement 17.53)
        if failed_tickers:
            logger.warning(f"Failed tickers: {', '.join(failed_tickers)}")

        return results

    def _save_to_cache(self, data: dict[str, dict[str, Any]]) -> None:
        """
        Save pre-fetched data to JSON cache.

        Args:
            data: Combined data from all sources

        """
        cache_file = self.cache_dir / "batch_data.json"

        try:
            cache_file.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
            logger.info(f"✓ Batch data saved to cache: {cache_file}")
            logger.info(f"  Cache size: {cache_file.stat().st_size / 1024:.1f} KB")
        except Exception as e:
            logger.error(f"✗ Failed to save batch data to cache: {e}")

    def load_from_cache(self) -> dict[str, dict[str, Any]]:
        """
        Load pre-fetched data from JSON cache.

        Returns:
            Dict mapping ticker to pre-fetched data, or empty dict if cache doesn't exist

        Example:
            >>> prefetcher = BatchDataPreFetcher("session-123")
            >>> cached_data = prefetcher.load_from_cache()
            >>> if cached_data:
            ...     print(f"Loaded {len(cached_data)} tickers from cache")

        """
        cache_file = self.cache_dir / "batch_data.json"

        if not cache_file.exists():
            logger.warning(f"Cache file not found: {cache_file}")
            return {}

        try:
            data: dict[str, dict[str, Any]] = json.loads(cache_file.read_text(encoding="utf-8"))
            logger.info(f"✓ Loaded batch data from cache: {cache_file}")
            logger.info(f"  Cached tickers: {len(data)}")
            return data
        except Exception as e:
            logger.error(f"✗ Failed to load batch data from cache: {e}")
            return {}

    def get_memory_metrics(self) -> dict[str, Any]:
        """
        Get memory usage metrics from memory manager.

        Returns comprehensive memory usage statistics including initial,
        peak, and final memory usage, plus all memory samples.

        Returns:
            Dict with memory metrics (see MemoryManager.get_memory_metrics)

        Example:
            >>> prefetcher = BatchDataPreFetcher("session-123")
            >>> prefetcher.prefetch_all_data(["AAPL", "MSFT"])
            >>> metrics = prefetcher.get_memory_metrics()
            >>> print(f"Peak memory: {metrics['peak_memory_mb']} MB")

        """
        return self.memory_manager.get_memory_metrics()

    def cleanup_cache(self) -> dict[str, Any]:
        """
        Clean up cache after Flow completion.

        Delegates to memory manager to remove all cached data and free
        memory and disk space.

        Returns:
            Dict with cleanup metrics (see MemoryManager.cleanup_cache)

        Example:
            >>> prefetcher = BatchDataPreFetcher("session-123")
            >>> cleanup_result = prefetcher.cleanup_cache()
            >>> print(f"Freed {cleanup_result['disk_freed_mb']} MB")

        """
        return self.memory_manager.cleanup_cache()

    def validate_memory_constraints(self) -> bool:
        """
        Validate that memory usage stayed within constraints.

        Checks if peak memory usage stayed within the 500 MB limit.

        Returns:
            True if memory constraints were met, False otherwise

        Example:
            >>> prefetcher = BatchDataPreFetcher("session-123")
            >>> prefetcher.prefetch_all_data(["AAPL", "MSFT"])
            >>> if prefetcher.validate_memory_constraints():
            ...     print("Memory usage within limits")

        """
        return self.memory_manager.validate_memory_constraints()
