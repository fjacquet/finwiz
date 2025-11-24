"""
Technical Indicator Fallback Calculator.

Provides on-the-fly calculation of missing technical indicators when they're not
available from data collection. Uses simple, fast calculations to ensure scoring
can proceed even with incomplete data.
"""

import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


def calculate_missing_technical_indicators(data: dict[str, Any], price_history: pd.Series | None = None) -> dict[str, Any]:
    """
    Calculate missing technical indicators using fallback methods.

    This function fills in missing technical indicators when they're not provided
    by the quantitative analysis tool. Uses simple calculations to ensure the
    scorer has all needed data.

    Args:
        data: Current data dictionary (will be modified in-place)
        price_history: Optional price history Series for calculations

    Returns:
        Updated data dictionary with calculated indicators

    """
    current_price = data.get("current_price")

    # Skip if no current price available
    if current_price is None or current_price <= 0:
        logger.debug("⏭️ No current_price available, skipping technical indicator fallback")
        return data

    # Calculate moving averages if missing
    if price_history is not None and len(price_history) > 0:
        _calculate_moving_averages(data, price_history, current_price)
        _calculate_rsi(data, price_history)
        _calculate_macd(data, price_history)
    else:
        # Use current price as proxy when no history available
        _use_current_price_fallback(data, current_price)

    # Calculate beta if missing (requires market data, so we use a neutral default)
    if "beta" not in data or data["beta"] is None:
        data["beta"] = 1.0  # Neutral beta assumption
        logger.debug("📊 Calculated beta fallback: 1.0 (neutral)")

    return data


def _calculate_moving_averages(data: dict[str, Any], prices: pd.Series, current_price: float) -> None:
    """Calculate 50-day and 200-day moving averages."""
    # 50-day moving average
    if "moving_avg_50" not in data or data["moving_avg_50"] is None:
        if len(prices) >= 50:
            ma_50 = prices.iloc[-50:].mean()
            data["moving_avg_50"] = float(ma_50)
            logger.debug(f"📊 Calculated moving_avg_50: {ma_50:.2f}")
        else:
            # Not enough data, use current price
            data["moving_avg_50"] = current_price
            logger.debug(f"📊 Insufficient data for MA50, using current_price: {current_price:.2f}")

    # 200-day moving average
    if "moving_avg_200" not in data or data["moving_avg_200"] is None:
        if len(prices) >= 200:
            ma_200 = prices.iloc[-200:].mean()
            data["moving_avg_200"] = float(ma_200)
            logger.debug(f"📊 Calculated moving_avg_200: {ma_200:.2f}")
        else:
            # Not enough data, use current price
            data["moving_avg_200"] = current_price
            logger.debug(f"📊 Insufficient data for MA200, using current_price: {current_price:.2f}")


def _calculate_rsi(data: dict[str, Any], prices: pd.Series, period: int = 14) -> None:
    """Calculate Relative Strength Index (RSI)."""
    if "rsi" not in data or data["rsi"] is None:
        if len(prices) >= period + 1:
            # Calculate price changes
            delta = prices.diff()

            # Separate gains and losses
            gains = delta.where(delta > 0, 0.0)
            losses = -delta.where(delta < 0, 0.0)

            # Calculate average gains and losses
            avg_gain = gains.rolling(window=period).mean().iloc[-1]
            avg_loss = losses.rolling(window=period).mean().iloc[-1]

            # Calculate RSI
            if avg_loss == 0:
                rsi = 100.0  # No losses means maximum RSI
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))

            data["rsi"] = float(rsi)
            logger.debug(f"📊 Calculated RSI: {rsi:.2f}")
        else:
            # Not enough data, use neutral RSI
            data["rsi"] = 50.0
            logger.debug("📊 Insufficient data for RSI, using neutral: 50.0")


def _calculate_macd(data: dict[str, Any], prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> None:
    """Calculate MACD and signal line."""
    # Only calculate if BOTH are missing (they're interdependent)
    macd_missing = "macd" not in data or data["macd"] is None
    signal_missing = "macd_signal" not in data or data["macd_signal"] is None

    if macd_missing and signal_missing:
        if len(prices) >= slow + signal:
            # Calculate exponential moving averages
            ema_fast = prices.ewm(span=fast, adjust=False).mean()
            ema_slow = prices.ewm(span=slow, adjust=False).mean()

            # Calculate MACD line
            macd_line = ema_fast - ema_slow

            # Calculate signal line (EMA of MACD)
            signal_line = macd_line.ewm(span=signal, adjust=False).mean()

            data["macd"] = float(macd_line.iloc[-1])
            data["macd_signal"] = float(signal_line.iloc[-1])
            logger.debug(f"📊 Calculated MACD: {data['macd']:.4f}, Signal: {data['macd_signal']:.4f}")
        else:
            # Not enough data, use neutral values
            data["macd"] = 0.0
            data["macd_signal"] = 0.0
            logger.debug("📊 Insufficient data for MACD, using neutral: 0.0")


def _use_current_price_fallback(data: dict[str, Any], current_price: float) -> None:
    """Use current price as fallback when no price history is available."""
    if "moving_avg_50" not in data or data["moving_avg_50"] is None:
        data["moving_avg_50"] = current_price
        logger.debug(f"📊 No price history, using current_price for MA50: {current_price:.2f}")

    if "moving_avg_200" not in data or data["moving_avg_200"] is None:
        data["moving_avg_200"] = current_price
        logger.debug(f"📊 No price history, using current_price for MA200: {current_price:.2f}")

    if "rsi" not in data or data["rsi"] is None:
        data["rsi"] = 50.0
        logger.debug("📊 No price history, using neutral RSI: 50.0")

    if "macd" not in data or data["macd"] is None:
        data["macd"] = 0.0
        logger.debug("📊 No price history, using neutral MACD: 0.0")

    if "macd_signal" not in data or data["macd_signal"] is None:
        data["macd_signal"] = 0.0
        logger.debug("📊 No price history, using neutral MACD signal: 0.0")


def get_price_history_from_data(data: dict[str, Any]) -> pd.Series | None:
    """
    Extract price history from data if available, or fetch it if ticker is provided.

    Args:
        data: Data dictionary that might contain price history or ticker

    Returns:
        Price Series or None if not available

    """
    # Check for various price history formats in data
    if "price_history" in data and isinstance(data["price_history"], (pd.Series, pd.DataFrame)):
        prices = data["price_history"]
        if isinstance(prices, pd.DataFrame):
            # Try to find Close column
            if "Close" in prices.columns:
                return prices["Close"]
            elif "close" in prices.columns:
                return prices["close"]
            elif len(prices.columns) == 1:
                return prices.iloc[:, 0]
        return prices

    if "historical_prices" in data and isinstance(data["historical_prices"], (pd.Series, pd.DataFrame)):
        prices = data["historical_prices"]
        if isinstance(prices, pd.DataFrame) and "Close" in prices.columns:
            return prices["Close"]
        return prices

    # Fallback: Try to fetch price history if ticker is available
    ticker = data.get("ticker") or data.get("symbol")
    if ticker:
        try:
            from datetime import datetime, timedelta

            from finwiz.quantitative.data import get_historical_data_manager

            data_manager = get_historical_data_manager()
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)  # Get 1 year of data

            logger.debug(f"📊 Fetching price history for {ticker} (fallback)")
            hist_data = data_manager.fetch_historical_data(ticker, start_date, end_date)

            if not hist_data.empty and "Close" in hist_data.columns:
                logger.info(f"✅ Fetched {len(hist_data)} days of price history for {ticker}")
                return hist_data["Close"]
        except Exception as e:
            logger.debug(f"⚠️ Could not fetch price history for {ticker}: {e}")

    return None
