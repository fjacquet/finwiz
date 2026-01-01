"""Holding analyzer orchestrator - coordinates deep analysis across crews."""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any

from finwiz.schemas.portfolio_review import AssetClass
from finwiz.tools.analysis.holding_processors import HoldingAnalysis, HoldingProcessor
from finwiz.tools.logger import get_logger
from finwiz.utils.cache_manager import CacheConfig, CacheManager, cache_key
from finwiz.utils.rate_limiter import RateLimiter, get_rate_limiter

logger = get_logger(__name__)


class HoldingAnalyzerOrchestrator:
    """Orchestrate deep analysis for portfolio holdings across crews with performance optimizations."""

    def __init__(
        self,
        output_dir: Path = Path("output"),
        enable_caching: bool = True,
        enable_rate_limiting: bool = True,
        parallel_batch_size: int = 10,
    ) -> None:
        """
        Initialize the orchestrator with performance optimizations.

        Args:
            output_dir: Base output directory for crew outputs
            enable_caching: Enable intelligent caching (default: True)
            enable_rate_limiting: Enable rate limiting (default: True)
            parallel_batch_size: Number of holdings to process in parallel (default: 10)

        """
        self.output_dir = output_dir
        self.stock_output_dir = output_dir / "stock"
        self.etf_output_dir = output_dir / "etf"
        self.crypto_output_dir = output_dir / "crypto"

        # Performance optimization settings
        self.enable_caching = enable_caching
        self.enable_rate_limiting = enable_rate_limiting
        self.parallel_batch_size = parallel_batch_size

        # Initialize cache manager with custom config for portfolio analysis
        self.cache_manager: CacheManager | None = None
        if self.enable_caching:
            self.cache_manager = CacheManager(
                config=CacheConfig(
                    default_ttl=604800,  # 7 days for crew analysis
                    max_memory_items=500,  # Support large portfolios
                    cache_directory="cache/portfolio_analysis",
                    auto_cleanup=True,
                    cleanup_interval=3600,  # Cleanup every hour
                )
            )
            logger.info("Cache manager initialized for portfolio analysis")

        # Initialize rate limiter
        self.rate_limiter: RateLimiter | None = None
        if self.enable_rate_limiting:
            self.rate_limiter = get_rate_limiter()
            logger.info("Rate limiter initialized")

    async def analyze_holdings_parallel(
        self,
        holdings: list[dict[str, Any]],
    ) -> list[HoldingAnalysis]:
        """
        Analyze multiple holdings in parallel with batching and rate limiting.

        Args:
            holdings: List of holding dicts with ticker, asset_class, currency, name

        Returns:
            List of HoldingAnalysis results

        """
        logger.info(f"Starting parallel analysis of {len(holdings)} holdings")
        start_time = datetime.now()

        results = []
        total_batches = (len(holdings) + self.parallel_batch_size - 1) // self.parallel_batch_size

        # Process holdings in batches to avoid overwhelming the system
        for batch_idx in range(0, len(holdings), self.parallel_batch_size):
            batch = holdings[batch_idx : batch_idx + self.parallel_batch_size]
            batch_num = batch_idx // self.parallel_batch_size + 1

            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} holdings)")

            # Create async tasks for batch
            tasks = [
                self.analyze_holding_async(
                    ticker=h.get("ticker", ""),
                    asset_class=h.get("asset_class", "stock"),
                    currency=h.get("currency", "USD"),
                    name=h.get("name", ""),
                )
                for h in batch
            ]

            # Execute batch in parallel
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Handle results and exceptions
            for holding, result in zip(batch, batch_results):
                analysis: HoldingAnalysis
                if isinstance(result, BaseException):
                    logger.error(
                        f"Error analyzing {holding.get('ticker')}: {result}",
                        extra={"ticker": holding.get("ticker"), "error": str(result)},
                    )
                    # Create baseline analysis for failed holdings
                    analysis = HoldingProcessor.create_baseline_analysis(
                        ticker=holding.get("ticker", ""),
                        asset_class=holding.get("asset_class", "stock"),
                        currency=holding.get("currency", "USD"),
                        name=holding.get("name", ""),
                    )
                else:
                    analysis = result

                results.append(analysis)

            # Small delay between batches to respect rate limits
            if batch_idx + self.parallel_batch_size < len(holdings):
                await asyncio.sleep(1.0)

        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(
            f"Completed parallel analysis of {len(holdings)} holdings in {elapsed:.2f}s",
            extra={
                "total_holdings": len(holdings),
                "elapsed_seconds": elapsed,
                "avg_per_holding": elapsed / len(holdings) if holdings else 0,
            },
        )

        return results

    async def analyze_holding_async(
        self,
        ticker: str,
        asset_class: AssetClass,
        currency: str,
        name: str = "",
    ) -> HoldingAnalysis:
        """
        Async version of analyze_holding for parallel processing.

        Args:
            ticker: Ticker symbol
            asset_class: Asset class (stock/etf/crypto)
            currency: Currency denomination
            name: Holding name (optional)

        Returns:
            HoldingAnalysis with crew-specific data mapped to schema

        """
        logger.debug(
            "Analyzing holding (async)",
            extra={
                "ticker": ticker,
                "asset_class": asset_class,
                "currency": currency,
            },
        )

        # Check cache first (with async support)
        if self.enable_caching and self.cache_manager:
            cache_key_str = cache_key("holding_analysis", ticker, asset_class)
            cached_result = await self.cache_manager.get(cache_key_str)

            if cached_result:
                logger.info(
                    "Cache hit for holding analysis",
                    extra={"ticker": ticker, "asset_class": asset_class},
                )
                result: HoldingAnalysis = cached_result
                return result

        # Check for crew output files
        cached_analysis = self.get_cached_analysis(ticker, asset_class, max_age_days=7)

        if cached_analysis:
            logger.info(
                "Using cached crew output",
                extra={
                    "ticker": ticker,
                    "cache_age_days": cached_analysis.get("age_days", 0),
                },
            )
            result = HoldingProcessor.map_cached_to_holding_analysis(
                ticker=ticker,
                asset_class=asset_class,
                currency=currency,
                name=name,
                cached_data=cached_analysis,
            )

            # Store in cache manager for faster future access
            if self.enable_caching and self.cache_manager:
                await self.cache_manager.set(
                    cache_key_str,
                    result,
                    ttl=604800,  # 7 days
                    tags={"holding_analysis", asset_class},
                )

            return result

        # No cache - return baseline with warning
        logger.warning(
            "No fresh crew analysis available, using baseline",
            extra={"ticker": ticker, "asset_class": asset_class},
        )

        result = HoldingProcessor.create_baseline_analysis(
            ticker=ticker,
            asset_class=asset_class,
            currency=currency,
            name=name,
        )

        # Cache baseline result with shorter TTL
        if self.enable_caching and self.cache_manager:
            await self.cache_manager.set(
                cache_key_str,
                result,
                ttl=3600,  # 1 hour for baseline
                tags={"holding_analysis", "baseline", asset_class},
            )

        return result

    def analyze_holding(
        self,
        ticker: str,
        asset_class: AssetClass,
        currency: str,
        name: str = "",
    ) -> HoldingAnalysis:
        """
        Analyze a single holding (synchronous version).

        This is the main entry point for synchronous usage.
        For async usage, use analyze_holding_async() directly.

        Args:
            ticker: Ticker symbol
            asset_class: Asset class (stock/etf/crypto)
            currency: Currency denomination
            name: Holding name (optional)

        Returns:
            HoldingAnalysis with crew-specific data mapped to schema

        """
        logger.debug(
            "Analyzing holding (sync)",
            extra={
                "ticker": ticker,
                "asset_class": asset_class,
                "currency": currency,
            },
        )

        # Check for crew output files
        cached_analysis = self.get_cached_analysis(ticker, asset_class, max_age_days=7)

        if cached_analysis:
            logger.info(
                "Using cached crew output",
                extra={
                    "ticker": ticker,
                    "cache_age_days": cached_analysis.get("age_days", 0),
                },
            )
            return HoldingProcessor.map_cached_to_holding_analysis(
                ticker=ticker,
                asset_class=asset_class,
                currency=currency,
                name=name,
                cached_data=cached_analysis,
            )

        # No cache - return baseline with warning
        logger.warning(
            "No fresh crew analysis available, using baseline",
            extra={"ticker": ticker, "asset_class": asset_class},
        )

        return HoldingProcessor.create_baseline_analysis(
            ticker=ticker,
            asset_class=asset_class,
            currency=currency,
            name=name,
        )

    def get_cached_analysis(
        self,
        ticker: str,
        asset_class: AssetClass,
        max_age_days: int = 7,
    ) -> dict | None:
        """
        Check for recent crew analysis output.

        Args:
            ticker: Ticker symbol
            asset_class: Asset class to determine output directory
            max_age_days: Maximum age in days for cache validity

        Returns:
            Cached analysis dict if found and fresh, None otherwise

        """
        # Determine output directory based on asset class
        output_dir = self._get_output_dir(asset_class)
        if not output_dir:
            return None

        return HoldingProcessor.load_cached_analysis(
            ticker=ticker,
            output_dir=output_dir,
            asset_class=asset_class,
            max_age_days=max_age_days,
        )

    def _get_output_dir(self, asset_class: AssetClass) -> Path | None:
        """Get output directory for asset class."""
        if asset_class == "stock":
            return self.stock_output_dir
        elif asset_class == "etf":
            return self.etf_output_dir
        elif asset_class == "crypto":
            return self.crypto_output_dir
        else:
            logger.warning(f"Unknown asset class: {asset_class}")
            return None

    def trigger_crew_analysis(
        self,
        ticker: str,
        asset_class: AssetClass,
    ) -> dict[str, Any]:
        """
        Trigger appropriate crew for fresh analysis.

        Note: This is a placeholder for future implementation.
        In production, this would actually kick off the crew.

        Args:
            ticker: Ticker symbol
            asset_class: Asset class to determine which crew to use

        Returns:
            Crew analysis output

        """
        logger.info(
            "Triggering crew analysis",
            extra={"ticker": ticker, "asset_class": asset_class},
        )

        # Placeholder - would actually trigger crew in production
        raise NotImplementedError("Crew triggering not yet implemented - use cached analysis or baseline")
