"""
Enhanced Twelve Data API Integration.

This module provides comprehensive technical indicator calculations using the Twelve Data API
with proper error handling, rate limiting, caching, and structured data models for
RSI, MACD, Bollinger Bands, and other advanced technical indicators.
"""

from __future__ import annotations

import asyncio
import os
import time
from datetime import datetime

import aiohttp
from pydantic import BaseModel, ConfigDict, Field

from finwiz.tools.logger import get_logger
from finwiz.utils.rate_limiter import APIProvider, with_rate_limit

logger = get_logger(__name__)


class TechnicalIndicatorValue(BaseModel):
    """Individual technical indicator data point."""

    model_config = ConfigDict(extra="forbid")

    datetime: str = Field(..., description="Timestamp of the data point")
    value: float = Field(..., description="Indicator value")


class RSIData(BaseModel):
    """RSI (Relative Strength Index) indicator data."""

    model_config = ConfigDict(extra="forbid")

    symbol: str = Field(..., description="Ticker symbol")
    interval: str = Field(..., description="Time interval")
    time_period: int = Field(..., description="RSI calculation period")
    values: list[TechnicalIndicatorValue] = Field(default_factory=list)
    current_value: float | None = Field(None, description="Most recent RSI value")
    signal: str = Field(..., description="overbought, oversold, or neutral")
    signal_strength: float = Field(..., ge=0.0, le=1.0, description="Signal strength")


class MACDValue(BaseModel):
    """Individual MACD data point."""

    model_config = ConfigDict(extra="forbid")

    datetime: str = Field(..., description="Timestamp")
    macd: float = Field(..., description="MACD line value")
    macd_signal: float = Field(..., description="MACD signal line value")
    macd_hist: float = Field(..., description="MACD histogram value")


class MACDData(BaseModel):
    """MACD (Moving Average Convergence Divergence) indicator data."""

    model_config = ConfigDict(extra="forbid")

    symbol: str = Field(..., description="Ticker symbol")
    interval: str = Field(..., description="Time interval")
    fast_period: int = Field(..., description="Fast EMA period")
    slow_period: int = Field(..., description="Slow EMA period")
    signal_period: int = Field(..., description="Signal line period")
    values: list[MACDValue] = Field(default_factory=list)
    current_macd: float | None = Field(None, description="Current MACD value")
    current_signal: float | None = Field(None, description="Current signal value")
    current_histogram: float | None = Field(None, description="Current histogram value")
    crossover_signal: str = Field(..., description="bullish, bearish, or neutral")
    signal_strength: float = Field(..., ge=0.0, le=1.0, description="Signal strength")


class BollingerBandsValue(BaseModel):
    """Individual Bollinger Bands data point."""

    model_config = ConfigDict(extra="forbid")

    datetime: str = Field(..., description="Timestamp")
    upper_band: float = Field(..., description="Upper Bollinger Band")
    middle_band: float = Field(..., description="Middle Bollinger Band (SMA)")
    lower_band: float = Field(..., description="Lower Bollinger Band")


class BollingerBandsData(BaseModel):
    """Bollinger Bands indicator data."""

    model_config = ConfigDict(extra="forbid")

    symbol: str = Field(..., description="Ticker symbol")
    interval: str = Field(..., description="Time interval")
    time_period: int = Field(..., description="Moving average period")
    std_dev: int = Field(..., description="Standard deviation multiplier")
    values: list[BollingerBandsValue] = Field(default_factory=list)
    current_upper: float | None = Field(None, description="Current upper band")
    current_middle: float | None = Field(None, description="Current middle band")
    current_lower: float | None = Field(None, description="Current lower band")
    band_width: float | None = Field(None, description="Current band width")
    squeeze_signal: str = Field(..., description="squeeze, expansion, or normal")
    position_signal: str = Field(..., description="above_upper, below_lower, or within_bands")


class StochasticValue(BaseModel):
    """Individual Stochastic oscillator data point."""

    model_config = ConfigDict(extra="forbid")

    datetime: str = Field(..., description="Timestamp")
    slow_k: float = Field(..., description="Slow %K value")
    slow_d: float = Field(..., description="Slow %D value")


class StochasticData(BaseModel):
    """Stochastic oscillator indicator data."""

    model_config = ConfigDict(extra="forbid")

    symbol: str = Field(..., description="Ticker symbol")
    interval: str = Field(..., description="Time interval")
    k_period: int = Field(..., description="%K period")
    d_period: int = Field(..., description="%D period")
    values: list[StochasticValue] = Field(default_factory=list)
    current_k: float | None = Field(None, description="Current %K value")
    current_d: float | None = Field(None, description="Current %D value")
    signal: str = Field(..., description="overbought, oversold, or neutral")
    crossover_signal: str = Field(..., description="bullish, bearish, or neutral")


class TechnicalIndicatorSummary(BaseModel):
    """Summary of all technical indicators for a symbol."""

    model_config = ConfigDict(extra="forbid")

    symbol: str = Field(..., description="Ticker symbol")
    interval: str = Field(..., description="Time interval")
    analysis_timestamp: datetime = Field(default_factory=datetime.now)

    rsi_data: RSIData | None = Field(None, description="RSI indicator data")
    macd_data: MACDData | None = Field(None, description="MACD indicator data")
    bollinger_data: BollingerBandsData | None = Field(None, description="Bollinger Bands data")
    stochastic_data: StochasticData | None = Field(None, description="Stochastic data")

    overall_signal: str = Field(..., description="buy, sell, or neutral")
    signal_confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence")
    consensus_indicators: int = Field(..., description="Number of indicators in agreement")


# Removed local RateLimiter class - now using centralized rate limiting system


class TwelveDataTool:
    """
    Enhanced Twelve Data API integration with comprehensive technical indicators.

    Provides RSI, MACD, Bollinger Bands, Stochastic, and other technical indicators
    with proper error handling, rate limiting, and structured data models.
    """

    def __init__(self) -> None:
        """Initialize the Twelve Data tool."""
        self.api_key = os.getenv("TWELVE_DATA_API_KEY")
        self.base_url = "https://api.twelvedata.com"

        # Cache for API responses (simple in-memory cache)
        self._cache: dict[str, dict] = {}
        self.cache_ttl = 300  # 5 minutes cache TTL

        # Default parameters
        self.default_outputsize = 100
        self.timeout = 30

    async def get_rsi(self, symbol: str, interval: str = "1day", time_period: int = 14, outputsize: int = None) -> RSIData:
        """
        Get RSI (Relative Strength Index) data for a symbol.

        Args:
            symbol: Ticker symbol
            interval: Time interval (1min, 5min, 1h, 1day, etc.)
            time_period: RSI calculation period (default: 14)
            outputsize: Number of data points to return

        Returns:
            RSI data with signal analysis

        """
        logger.info(f"Fetching RSI for {symbol} ({interval})")

        params = {
            "symbol": symbol,
            "interval": interval,
            "time_period": time_period,
            "outputsize": outputsize or self.default_outputsize,
        }

        data = await self._make_api_call("rsi", params)

        # Parse RSI data
        values = []
        if "values" in data:
            for item in data["values"]:
                values.append(TechnicalIndicatorValue(datetime=item["datetime"], value=float(item["rsi"])))

        # Analyze current RSI value
        current_value = values[0].value if values else None
        signal, signal_strength = self._analyze_rsi_signal(current_value)

        return RSIData(
            symbol=symbol,
            interval=interval,
            time_period=time_period,
            values=values,
            current_value=current_value,
            signal=signal,
            signal_strength=signal_strength,
        )

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
            symbol: Ticker symbol
            interval: Time interval
            fast_period: Fast EMA period (default: 12)
            slow_period: Slow EMA period (default: 26)
            signal_period: Signal line period (default: 9)
            outputsize: Number of data points to return

        Returns:
            MACD data with crossover analysis

        """
        logger.info(f"Fetching MACD for {symbol} ({interval})")

        params = {
            "symbol": symbol,
            "interval": interval,
            "fast": fast_period,
            "slow": slow_period,
            "signal": signal_period,
            "outputsize": outputsize or self.default_outputsize,
        }

        data = await self._make_api_call("macd", params)

        # Parse MACD data
        values = []
        if "values" in data:
            for item in data["values"]:
                values.append(
                    MACDValue(
                        datetime=item["datetime"],
                        macd=float(item["macd"]),
                        macd_signal=float(item["macd_signal"]),
                        macd_hist=float(item["macd_hist"]),
                    )
                )

        # Analyze current MACD values
        current_macd = values[0].macd if values else None
        current_signal = values[0].macd_signal if values else None
        current_histogram = values[0].macd_hist if values else None

        crossover_signal, signal_strength = self._analyze_macd_signal(values)

        return MACDData(
            symbol=symbol,
            interval=interval,
            fast_period=fast_period,
            slow_period=slow_period,
            signal_period=signal_period,
            values=values,
            current_macd=current_macd,
            current_signal=current_signal,
            current_histogram=current_histogram,
            crossover_signal=crossover_signal,
            signal_strength=signal_strength,
        )

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
            symbol: Ticker symbol
            interval: Time interval
            time_period: Moving average period (default: 20)
            std_dev: Standard deviation multiplier (default: 2)
            outputsize: Number of data points to return

        Returns:
            Bollinger Bands data with squeeze analysis

        """
        logger.info(f"Fetching Bollinger Bands for {symbol} ({interval})")

        params = {
            "symbol": symbol,
            "interval": interval,
            "time_period": time_period,
            "sd": std_dev,
            "outputsize": outputsize or self.default_outputsize,
        }

        data = await self._make_api_call("bbands", params)

        # Parse Bollinger Bands data
        values = []
        if "values" in data:
            for item in data["values"]:
                values.append(
                    BollingerBandsValue(
                        datetime=item["datetime"],
                        upper_band=float(item["upper_band"]),
                        middle_band=float(item["middle_band"]),
                        lower_band=float(item["lower_band"]),
                    )
                )

        # Analyze current Bollinger Bands
        current_upper = values[0].upper_band if values else None
        current_middle = values[0].middle_band if values else None
        current_lower = values[0].lower_band if values else None

        band_width = None
        if current_upper and current_lower:
            band_width = (current_upper - current_lower) / current_middle if current_middle else 0

        squeeze_signal = self._analyze_bollinger_squeeze(values)
        position_signal = self._analyze_bollinger_position(values, symbol)

        return BollingerBandsData(
            symbol=symbol,
            interval=interval,
            time_period=time_period,
            std_dev=std_dev,
            values=values,
            current_upper=current_upper,
            current_middle=current_middle,
            current_lower=current_lower,
            band_width=band_width,
            squeeze_signal=squeeze_signal,
            position_signal=position_signal,
        )

    async def get_stochastic(
        self,
        symbol: str,
        interval: str = "1day",
        k_period: int = 14,
        d_period: int = 3,
        outputsize: int = None,
    ) -> StochasticData:
        """
        Get Stochastic oscillator data for a symbol.

        Args:
            symbol: Ticker symbol
            interval: Time interval
            k_period: %K period (default: 14)
            d_period: %D period (default: 3)
            outputsize: Number of data points to return

        Returns:
            Stochastic data with overbought/oversold analysis

        """
        logger.info(f"Fetching Stochastic for {symbol} ({interval})")

        params = {
            "symbol": symbol,
            "interval": interval,
            "k_period": k_period,
            "d_period": d_period,
            "outputsize": outputsize or self.default_outputsize,
        }

        data = await self._make_api_call("stoch", params)

        # Parse Stochastic data
        values = []
        if "values" in data:
            for item in data["values"]:
                values.append(
                    StochasticValue(datetime=item["datetime"], slow_k=float(item["slow_k"]), slow_d=float(item["slow_d"]))
                )

        # Analyze current Stochastic values
        current_k = values[0].slow_k if values else None
        current_d = values[0].slow_d if values else None

        signal = self._analyze_stochastic_signal(current_k, current_d)
        crossover_signal = self._analyze_stochastic_crossover(values)

        return StochasticData(
            symbol=symbol,
            interval=interval,
            k_period=k_period,
            d_period=d_period,
            values=values,
            current_k=current_k,
            current_d=current_d,
            signal=signal,
            crossover_signal=crossover_signal,
        )

    async def get_comprehensive_analysis(
        self,
        symbol: str,
        interval: str = "1day",
        include_rsi: bool = True,
        include_macd: bool = True,
        include_bollinger: bool = True,
        include_stochastic: bool = True,
    ) -> TechnicalIndicatorSummary:
        """
        Get comprehensive technical indicator analysis for a symbol.

        Args:
            symbol: Ticker symbol
            interval: Time interval
            include_rsi: Whether to include RSI analysis
            include_macd: Whether to include MACD analysis
            include_bollinger: Whether to include Bollinger Bands
            include_stochastic: Whether to include Stochastic oscillator

        Returns:
            Comprehensive technical indicator summary

        """
        logger.info(f"Performing comprehensive analysis for {symbol} ({interval})")

        # Fetch all requested indicators concurrently
        tasks = []

        if include_rsi:
            tasks.append(self.get_rsi(symbol, interval))
        if include_macd:
            tasks.append(self.get_macd(symbol, interval))
        if include_bollinger:
            tasks.append(self.get_bollinger_bands(symbol, interval))
        if include_stochastic:
            tasks.append(self.get_stochastic(symbol, interval))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        rsi_data = None
        macd_data = None
        bollinger_data = None
        stochastic_data = None

        result_index = 0
        if include_rsi:
            if not isinstance(results[result_index], Exception):
                rsi_data = results[result_index]
            result_index += 1

        if include_macd:
            if not isinstance(results[result_index], Exception):
                macd_data = results[result_index]
            result_index += 1

        if include_bollinger:
            if not isinstance(results[result_index], Exception):
                bollinger_data = results[result_index]
            result_index += 1

        if include_stochastic:
            if not isinstance(results[result_index], Exception):
                stochastic_data = results[result_index]
            result_index += 1

        # Determine overall signal
        overall_signal, confidence, consensus = self._determine_overall_signal(rsi_data, macd_data, bollinger_data, stochastic_data)

        return TechnicalIndicatorSummary(
            symbol=symbol,
            interval=interval,
            rsi_data=rsi_data,
            macd_data=macd_data,
            bollinger_data=bollinger_data,
            stochastic_data=stochastic_data,
            overall_signal=overall_signal,
            signal_confidence=confidence,
            consensus_indicators=consensus,
        )

    async def _make_api_call(self, endpoint: str, params: dict) -> dict:
        """Make API call to Twelve Data with rate limiting and error handling."""
        if not self.api_key:
            raise ValueError("TWELVE_DATA_API_KEY environment variable not set")

        # Add API key to parameters
        params["apikey"] = self.api_key

        # Check cache first
        cache_key = f"{endpoint}_{hash(str(sorted(params.items())))}"
        if cache_key in self._cache:
            cache_entry = self._cache[cache_key]
            if time.time() - cache_entry["timestamp"] < self.cache_ttl:
                logger.debug(f"Using cached data for {endpoint}")
                return cache_entry["data"]

        url = f"{self.base_url}/{endpoint}"

        async def make_request():
            """Internal function to make the actual HTTP request."""
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=self.timeout)) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise RuntimeError(f"API error {response.status}: {error_text}")

                    data = await response.json()

                    # Check for API error in response
                    if "status" in data and data["status"] == "error":
                        raise RuntimeError(f"API error: {data.get('message', 'Unknown error')}")

                    # Cache successful response
                    self._cache[cache_key] = {"data": data, "timestamp": time.time()}

                    return data

        # Use centralized rate limiting
        try:
            return await with_rate_limit(APIProvider.TWELVE_DATA, make_request, endpoint=endpoint)
        except Exception as e:
            logger.error(f"Error fetching {endpoint} data: {e}")
            raise

    def _analyze_rsi_signal(self, rsi_value: float | None) -> tuple[str, float]:
        """Analyze RSI value for overbought/oversold signals."""
        if rsi_value is None:
            return "neutral", 0.0

        if rsi_value >= 70:
            strength = min(1.0, (rsi_value - 70) / 30)
            return "overbought", strength
        elif rsi_value <= 30:
            strength = min(1.0, (30 - rsi_value) / 30)
            return "oversold", strength
        else:
            return "neutral", 0.3

    def _analyze_macd_signal(self, macd_values: list[MACDValue]) -> tuple[str, float]:
        """Analyze MACD for crossover signals."""
        if len(macd_values) < 2:
            return "neutral", 0.0

        current = macd_values[0]
        previous = macd_values[1]

        # Check for crossover
        if current.macd > current.macd_signal and previous.macd <= previous.macd_signal:
            # Bullish crossover
            strength = min(
                1.0,
                abs(current.macd - current.macd_signal) / abs(current.macd_signal) if current.macd_signal != 0 else 0.5,
            )
            return "bullish", strength
        elif current.macd < current.macd_signal and previous.macd >= previous.macd_signal:
            # Bearish crossover
            strength = min(
                1.0,
                abs(current.macd - current.macd_signal) / abs(current.macd_signal) if current.macd_signal != 0 else 0.5,
            )
            return "bearish", strength
        else:
            return "neutral", 0.2

    def _analyze_bollinger_squeeze(self, bb_values: list[BollingerBandsValue]) -> str:
        """Analyze Bollinger Bands for squeeze conditions."""
        if len(bb_values) < 20:
            return "normal"

        # Calculate recent band widths
        recent_widths = []
        for value in bb_values[:10]:
            width = (value.upper_band - value.lower_band) / value.middle_band
            recent_widths.append(width)

        # Calculate historical average
        historical_widths = []
        for value in bb_values[10:]:
            width = (value.upper_band - value.lower_band) / value.middle_band
            historical_widths.append(width)

        if not historical_widths:
            return "normal"

        avg_recent = sum(recent_widths) / len(recent_widths)
        avg_historical = sum(historical_widths) / len(historical_widths)

        if avg_recent < avg_historical * 0.8:
            return "squeeze"
        elif avg_recent > avg_historical * 1.2:
            return "expansion"
        else:
            return "normal"

    def _analyze_bollinger_position(self, bb_values: list[BollingerBandsValue], symbol: str) -> str:
        """Analyze price position relative to Bollinger Bands."""
        if not bb_values:
            return "within_bands"

        # This is a simplified analysis - in practice, you'd need current price
        # For now, we'll use the middle band as a proxy
        bb_values[0]

        # Simplified logic - would need actual price data
        return "within_bands"

    def _analyze_stochastic_signal(self, k_value: float | None, d_value: float | None) -> str:
        """Analyze Stochastic for overbought/oversold conditions."""
        if k_value is None or d_value is None:
            return "neutral"

        avg_value = (k_value + d_value) / 2

        if avg_value >= 80:
            return "overbought"
        elif avg_value <= 20:
            return "oversold"
        else:
            return "neutral"

    def _analyze_stochastic_crossover(self, stoch_values: list[StochasticValue]) -> str:
        """Analyze Stochastic for crossover signals."""
        if len(stoch_values) < 2:
            return "neutral"

        current = stoch_values[0]
        previous = stoch_values[1]

        if current.slow_k > current.slow_d and previous.slow_k <= previous.slow_d:
            return "bullish"
        elif current.slow_k < current.slow_d and previous.slow_k >= previous.slow_d:
            return "bearish"
        else:
            return "neutral"

    def _determine_overall_signal(
        self,
        rsi_data: RSIData | None,
        macd_data: MACDData | None,
        bollinger_data: BollingerBandsData | None,
        stochastic_data: StochasticData | None,
    ) -> tuple[str, float, int]:
        """Determine overall signal from all indicators."""
        bullish_signals = 0
        bearish_signals = 0
        total_indicators = 0
        total_strength = 0

        # Analyze RSI
        if rsi_data:
            total_indicators += 1
            if rsi_data.signal == "oversold":
                bullish_signals += 1
                total_strength += rsi_data.signal_strength
            elif rsi_data.signal == "overbought":
                bearish_signals += 1
                total_strength += rsi_data.signal_strength
            else:
                total_strength += 0.2

        # Analyze MACD
        if macd_data:
            total_indicators += 1
            if macd_data.crossover_signal == "bullish":
                bullish_signals += 1
                total_strength += macd_data.signal_strength
            elif macd_data.crossover_signal == "bearish":
                bearish_signals += 1
                total_strength += macd_data.signal_strength
            else:
                total_strength += 0.2

        # Analyze Bollinger Bands
        if bollinger_data:
            total_indicators += 1
            if bollinger_data.position_signal == "below_lower":
                bullish_signals += 1
                total_strength += 0.6
            elif bollinger_data.position_signal == "above_upper":
                bearish_signals += 1
                total_strength += 0.6
            else:
                total_strength += 0.2

        # Analyze Stochastic
        if stochastic_data:
            total_indicators += 1
            if stochastic_data.signal == "oversold" or stochastic_data.crossover_signal == "bullish":
                bullish_signals += 1
                total_strength += 0.5
            elif stochastic_data.signal == "overbought" or stochastic_data.crossover_signal == "bearish":
                bearish_signals += 1
                total_strength += 0.5
            else:
                total_strength += 0.2

        if total_indicators == 0:
            return "neutral", 0.0, 0

        # Determine consensus
        consensus = max(bullish_signals, bearish_signals)
        confidence = (total_strength / total_indicators) * (consensus / total_indicators)

        if bullish_signals > bearish_signals:
            return "buy", confidence, consensus
        elif bearish_signals > bullish_signals:
            return "sell", confidence, consensus
        else:
            return "neutral", confidence * 0.5, consensus
