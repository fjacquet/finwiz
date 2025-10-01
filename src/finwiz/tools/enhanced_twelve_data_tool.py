"""
Enhanced Twelve Data API Integration.

This module provides comprehensive technical indicator calculations using the Twelve Data API
with proper error handling, rate limiting, caching, and structured data models for
RSI, MACD, Bollinger Bands, and other advanced technical indicators.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from finwiz.tools.logger import get_logger
from finwiz.tools.twelve_data_client import TwelveDataClient
from finwiz.tools.twelve_data_transformers import (
    BollingerBandsData,
    MACDData,
    RSIData,
    StochasticData,
    TechnicalIndicatorSummary,
    TwelveDataTransformers,
)

logger = get_logger(__name__)


class TwelveDataTool:
    """
    Enhanced Twelve Data API integration with comprehensive technical indicators.

    This class provides a high-level interface for fetching and analyzing technical
    indicators using the Twelve Data API. It combines the API client functionality
    with data transformation and analysis capabilities.
    """

    def __init__(self) -> None:
        """Initialize the Twelve Data tool."""
        self.client = TwelveDataClient()
        self.transformers = TwelveDataTransformers()

    async def get_rsi(self, symbol: str, interval: str = "1day", time_period: int = 14, outputsize: int = None) -> RSIData:
        """
        Get RSI (Relative Strength Index) data for a symbol.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            interval: Time interval (1min, 5min, 15min, 30min, 45min, 1h, 2h, 4h, 1day, 1week, 1month)
            time_period: RSI calculation period (default: 14)
            outputsize: Number of data points to return (default: 30)

        Returns:
            RSIData object with RSI values and signal analysis

        Raises:
            ValueError: If API key is not configured
            RuntimeError: If API returns an error

        """
        params = {
            "symbol": symbol,
            "interval": interval,
            "time_period": time_period,
        }

        if outputsize is not None:
            params["outputsize"] = outputsize

        try:
            response = await self.client.make_api_call("rsi", params)
            return self.transformers.transform_rsi_response(response, symbol, interval, time_period)

        except Exception as e:
            logger.error(f"Error fetching RSI data for {symbol}: {e}")
            raise

    async def get_macd(
        self,
        symbol: str,
        interval: str = "1day",
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        outputsize: int = None,
    ) -> MACDData:
        """
        Get MACD (Moving Average Convergence Divergence) data for a symbol.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            interval: Time interval
            fast_period: Fast EMA period (default: 12)
            slow_period: Slow EMA period (default: 26)
            signal_period: Signal line EMA period (default: 9)
            outputsize: Number of data points to return

        Returns:
            MACDData object with MACD values and crossover analysis

        Raises:
            ValueError: If API key is not configured
            RuntimeError: If API returns an error

        """
        params = {
            "symbol": symbol,
            "interval": interval,
            "fast_period": fast_period,
            "slow_period": slow_period,
            "signal_period": signal_period,
        }

        if outputsize is not None:
            params["outputsize"] = outputsize

        try:
            response = await self.client.make_api_call("macd", params)
            return self.transformers.transform_macd_response(response, symbol, interval, fast_period, slow_period, signal_period)

        except Exception as e:
            logger.error(f"Error fetching MACD data for {symbol}: {e}")
            raise

    async def get_bollinger_bands(
        self,
        symbol: str,
        interval: str = "1day",
        time_period: int = 20,
        std_dev: int = 2,
        outputsize: int = None,
    ) -> BollingerBandsData:
        """
        Get Bollinger Bands data for a symbol.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            interval: Time interval
            time_period: Moving average period (default: 20)
            std_dev: Standard deviation multiplier (default: 2)
            outputsize: Number of data points to return

        Returns:
            BollingerBandsData object with bands and squeeze analysis

        Raises:
            ValueError: If API key is not configured
            RuntimeError: If API returns an error

        """
        params = {
            "symbol": symbol,
            "interval": interval,
            "time_period": time_period,
            "sd": std_dev,
        }

        if outputsize is not None:
            params["outputsize"] = outputsize

        try:
            response = await self.client.make_api_call("bbands", params)
            return self.transformers.transform_bollinger_response(response, symbol, interval, time_period, std_dev)

        except Exception as e:
            logger.error(f"Error fetching Bollinger Bands data for {symbol}: {e}")
            raise

    async def get_stochastic(
        self,
        symbol: str,
        interval: str = "1day",
        fastkperiod: int = 14,
        slowkperiod: int = 3,
        slowdperiod: int = 3,
        outputsize: int = None,
    ) -> StochasticData:
        """
        Get Stochastic oscillator data for a symbol.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            interval: Time interval
            fastkperiod: Fast %K period (default: 14)
            slowkperiod: Slow %K period (default: 3)
            slowdperiod: Slow %D period (default: 3)
            outputsize: Number of data points to return

        Returns:
            StochasticData object with oscillator values and signal analysis

        Raises:
            ValueError: If API key is not configured
            RuntimeError: If API returns an error

        """
        params = {
            "symbol": symbol,
            "interval": interval,
            "fastkperiod": fastkperiod,
            "slowkperiod": slowkperiod,
            "slowdperiod": slowdperiod,
        }

        if outputsize is not None:
            params["outputsize"] = outputsize

        try:
            response = await self.client.make_api_call("stoch", params)
            return self.transformers.transform_stochastic_response(
                response, symbol, interval, fastkperiod, slowkperiod, slowdperiod
            )

        except Exception as e:
            logger.error(f"Error fetching Stochastic data for {symbol}: {e}")
            raise

    async def get_comprehensive_analysis(
        self,
        symbol: str,
        interval: str = "1day",
        outputsize: int = 30,
    ) -> TechnicalIndicatorSummary:
        """
        Get comprehensive technical analysis for a symbol.

        This method fetches all major technical indicators and provides
        an overall signal analysis with confidence scoring.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            interval: Time interval
            outputsize: Number of data points to return for each indicator

        Returns:
            TechnicalIndicatorSummary with all indicators and overall signal

        Raises:
            ValueError: If API key is not configured
            RuntimeError: If API returns an error

        """
        logger.info(f"Starting comprehensive technical analysis for {symbol}")

        # Fetch all indicators concurrently
        try:
            import asyncio

            rsi_task = self.get_rsi(symbol, interval, outputsize=outputsize)
            macd_task = self.get_macd(symbol, interval, outputsize=outputsize)
            bb_task = self.get_bollinger_bands(symbol, interval, outputsize=outputsize)
            stoch_task = self.get_stochastic(symbol, interval, outputsize=outputsize)

            # Wait for all tasks to complete
            results = await asyncio.gather(rsi_task, macd_task, bb_task, stoch_task, return_exceptions=True)

            # Extract results, handling any exceptions
            rsi_data = results[0] if not isinstance(results[0], Exception) else None
            macd_data = results[1] if not isinstance(results[1], Exception) else None
            bollinger_data = results[2] if not isinstance(results[2], Exception) else None
            stochastic_data = results[3] if not isinstance(results[3], Exception) else None

            # Log any exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    indicator_names = ["RSI", "MACD", "Bollinger Bands", "Stochastic"]
                    logger.warning(f"Failed to fetch {indicator_names[i]} for {symbol}: {result}")

        except Exception as e:
            logger.error(f"Error during comprehensive analysis for {symbol}: {e}")
            # Create empty data objects if all requests fail
            rsi_data = macd_data = bollinger_data = stochastic_data = None

        # Determine overall signal
        overall_signal, confidence, consensus = self.transformers.determine_overall_signal(
            rsi_data, macd_data, bollinger_data, stochastic_data
        )

        logger.info(
            f"Comprehensive analysis completed for {symbol}: "
            f"Signal={overall_signal}, Confidence={confidence:.2f}, Consensus={consensus}"
        )

        return TechnicalIndicatorSummary(
            symbol=symbol,
            interval=interval,
            timestamp=datetime.now().isoformat(),
            rsi_data=rsi_data,
            macd_data=macd_data,
            bollinger_data=bollinger_data,
            stochastic_data=stochastic_data,
            overall_signal=overall_signal,
            signal_confidence=confidence,
            consensus_indicators=consensus,
        )

    def clear_cache(self) -> None:
        """Clear the API response cache."""
        self.client.clear_cache()

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        return self.client.get_cache_stats()
