"""
TA-Lib Wrapper Functions for Technical Indicators.

This module provides clean wrapper functions around TA-Lib indicators,
standardizing input/output formats and error handling across all technical indicators.
"""

import numpy as np
import pandas as pd
import talib


class TALibWrappers:
    """Wrapper class for TA-Lib technical indicator functions."""

    @staticmethod
    def sma(close_prices: np.ndarray, period: int) -> np.ndarray:
        """
        Calculate Simple Moving Average.

        Args:
            close_prices: Array of closing prices
            period: Period for SMA calculation

        Returns:
            Array of SMA values

        """
        return talib.SMA(close_prices.astype(np.float64), timeperiod=period)

    @staticmethod
    def ema(close_prices: np.ndarray, period: int) -> np.ndarray:
        """
        Exponential Moving Average wrapper.

        Args:
            close_prices: Array of closing prices
            period: Period for EMA calculation

        Returns:
            Array of EMA values

        """
        return talib.EMA(close_prices.astype(np.float64), timeperiod=period)

    @staticmethod
    def rsi(close_prices: np.ndarray, period: int = 14) -> np.ndarray:
        """
        Relative Strength Index wrapper.

        Args:
            close_prices: Array of closing prices
            period: Period for RSI calculation

        Returns:
            Array of RSI values

        """
        return talib.RSI(close_prices.astype(np.float64), timeperiod=period)

    @staticmethod
    def macd(close_prices: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        MACD (Moving Average Convergence Divergence) wrapper.

        Args:
            close_prices: Array of closing prices
            fast: Fast EMA period
            slow: Slow EMA period
            signal: Signal line EMA period

        Returns:
            Tuple of (MACD line, Signal line, Histogram)

        """
        return talib.MACD(close_prices.astype(np.float64), fastperiod=fast, slowperiod=slow, signalperiod=signal)

    @staticmethod
    def bollinger_bands(close_prices: np.ndarray, period: int = 20, std_dev: float = 2.0) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Bollinger Bands wrapper.

        Args:
            close_prices: Array of closing prices
            period: Period for moving average
            std_dev: Standard deviation multiplier

        Returns:
            Tuple of (Upper band, Middle band, Lower band)

        """
        return talib.BBANDS(close_prices.astype(np.float64), timeperiod=period, nbdevup=std_dev, nbdevdn=std_dev)

    @staticmethod
    def atr(high_prices: np.ndarray, low_prices: np.ndarray, close_prices: np.ndarray, period: int = 14) -> np.ndarray:
        """
        Average True Range wrapper.

        Args:
            high_prices: Array of high prices
            low_prices: Array of low prices
            close_prices: Array of closing prices
            period: Period for ATR calculation

        Returns:
            Array of ATR values

        """
        return talib.ATR(high_prices.astype(np.float64), low_prices.astype(np.float64), close_prices.astype(np.float64), timeperiod=period)

    @staticmethod
    def stochastic(high_prices: np.ndarray, low_prices: np.ndarray, close_prices: np.ndarray, k_period: int = 14, d_period: int = 3) -> tuple[np.ndarray, np.ndarray]:
        """
        Stochastic Oscillator wrapper.

        Args:
            high_prices: Array of high prices
            low_prices: Array of low prices
            close_prices: Array of closing prices
            k_period: %K period
            d_period: %D period

        Returns:
            Tuple of (%K, %D)

        """
        return talib.STOCH(
            high_prices.astype(np.float64),
            low_prices.astype(np.float64),
            close_prices.astype(np.float64),
            fastk_period=k_period,
            slowk_period=d_period,
            slowd_period=d_period,
        )

    @staticmethod
    def adx(high_prices: np.ndarray, low_prices: np.ndarray, close_prices: np.ndarray, period: int = 14) -> np.ndarray:
        """
        Average Directional Index wrapper.

        Args:
            high_prices: Array of high prices
            low_prices: Array of low prices
            close_prices: Array of closing prices
            period: Period for ADX calculation

        Returns:
            Array of ADX values

        """
        return talib.ADX(high_prices.astype(np.float64), low_prices.astype(np.float64), close_prices.astype(np.float64), timeperiod=period)

    @staticmethod
    def cci(high_prices: np.ndarray, low_prices: np.ndarray, close_prices: np.ndarray, period: int = 14) -> np.ndarray:
        """
        Commodity Channel Index wrapper.

        Args:
            high_prices: Array of high prices
            low_prices: Array of low prices
            close_prices: Array of closing prices
            period: Period for CCI calculation

        Returns:
            Array of CCI values

        """
        return talib.CCI(high_prices.astype(np.float64), low_prices.astype(np.float64), close_prices.astype(np.float64), timeperiod=period)

    @staticmethod
    def williams_r(high_prices: np.ndarray, low_prices: np.ndarray, close_prices: np.ndarray, period: int = 14) -> np.ndarray:
        """
        Williams %R wrapper.

        Args:
            high_prices: Array of high prices
            low_prices: Array of low prices
            close_prices: Array of closing prices
            period: Period for Williams %R calculation

        Returns:
            Array of Williams %R values

        """
        return talib.WILLR(high_prices.astype(np.float64), low_prices.astype(np.float64), close_prices.astype(np.float64), timeperiod=period)

    @staticmethod
    def obv(close_prices: np.ndarray, volume: np.ndarray) -> np.ndarray:
        """
        On Balance Volume wrapper.

        Args:
            close_prices: Array of closing prices
            volume: Array of volume data

        Returns:
            Array of OBV values

        """
        return talib.OBV(close_prices.astype(np.float64), volume.astype(np.float64))

    @staticmethod
    def momentum(close_prices: np.ndarray, period: int = 10) -> np.ndarray:
        """
        Momentum wrapper.

        Args:
            close_prices: Array of closing prices
            period: Period for momentum calculation

        Returns:
            Array of momentum values

        """
        return talib.MOM(close_prices.astype(np.float64), timeperiod=period)

    @staticmethod
    def roc(close_prices: np.ndarray, period: int = 10) -> np.ndarray:
        """
        Rate of Change wrapper.

        Args:
            close_prices: Array of closing prices
            period: Period for ROC calculation

        Returns:
            Array of ROC values

        """
        return talib.ROC(close_prices.astype(np.float64), timeperiod=period)

    @staticmethod
    def trix(close_prices: np.ndarray, period: int = 14) -> np.ndarray:
        """
        TRIX wrapper.

        Args:
            close_prices: Array of closing prices
            period: Period for TRIX calculation

        Returns:
            Array of TRIX values

        """
        return talib.TRIX(close_prices.astype(np.float64), timeperiod=period)

    @staticmethod
    def dmi(high_prices: np.ndarray, low_prices: np.ndarray, close_prices: np.ndarray, period: int = 14) -> tuple[np.ndarray, np.ndarray]:
        """
        Directional Movement Index wrapper.

        Args:
            high_prices: Array of high prices
            low_prices: Array of low prices
            close_prices: Array of closing prices
            period: Period for DMI calculation

        Returns:
            Tuple of (Plus DI, Minus DI)

        """
        plus_di = talib.PLUS_DI(high_prices.astype(np.float64), low_prices.astype(np.float64), close_prices.astype(np.float64), timeperiod=period)
        minus_di = talib.MINUS_DI(high_prices.astype(np.float64), low_prices.astype(np.float64), close_prices.astype(np.float64), timeperiod=period)
        return plus_di, minus_di

    @staticmethod
    def aroon(high_prices: np.ndarray, low_prices: np.ndarray, period: int = 14) -> tuple[np.ndarray, np.ndarray]:
        """
        Aroon wrapper.

        Args:
            high_prices: Array of high prices
            low_prices: Array of low prices
            period: Period for Aroon calculation

        Returns:
            Tuple of (Aroon Up, Aroon Down)

        """
        return talib.AROON(high_prices.astype(np.float64), low_prices.astype(np.float64), timeperiod=period)

    @staticmethod
    def mfi(high_prices: np.ndarray, low_prices: np.ndarray, close_prices: np.ndarray, volume: np.ndarray, period: int = 14) -> np.ndarray:
        """
        Money Flow Index wrapper.

        Args:
            high_prices: Array of high prices
            low_prices: Array of low prices
            close_prices: Array of closing prices
            volume: Array of volume data
            period: Period for MFI calculation

        Returns:
            Array of MFI values

        """
        return talib.MFI(
            high_prices.astype(np.float64),
            low_prices.astype(np.float64),
            close_prices.astype(np.float64),
            volume.astype(np.float64),
            timeperiod=period,
        )

    @staticmethod
    def parabolic_sar(high_prices: np.ndarray, low_prices: np.ndarray, acceleration: float = 0.02, maximum: float = 0.2) -> np.ndarray:
        """
        Parabolic SAR wrapper.

        Args:
            high_prices: Array of high prices
            low_prices: Array of low prices
            acceleration: Acceleration factor
            maximum: Maximum acceleration

        Returns:
            Array of Parabolic SAR values

        """
        return talib.SAR(high_prices.astype(np.float64), low_prices.astype(np.float64), acceleration=acceleration, maximum=maximum)

    @staticmethod
    def ultimate_oscillator(
        high_prices: np.ndarray,
        low_prices: np.ndarray,
        close_prices: np.ndarray,
        period1: int = 7,
        period2: int = 14,
        period3: int = 28,
    ) -> np.ndarray:
        """
        Ultimate Oscillator wrapper.

        Args:
            high_prices: Array of high prices
            low_prices: Array of low prices
            close_prices: Array of closing prices
            period1: First period
            period2: Second period
            period3: Third period

        Returns:
            Array of Ultimate Oscillator values

        """
        return talib.ULTOSC(
            high_prices.astype(np.float64),
            low_prices.astype(np.float64),
            close_prices.astype(np.float64),
            timeperiod1=period1,
            timeperiod2=period2,
            timeperiod3=period3,
        )


# Convenience functions for direct access
def calculate_sma(data: pd.DataFrame, period: int) -> pd.Series:
    """Calculate Simple Moving Average from DataFrame."""
    return pd.Series(TALibWrappers.sma(data["Close"].values, period), index=data.index)


def calculate_ema(data: pd.DataFrame, period: int) -> pd.Series:
    """Calculate Exponential Moving Average from DataFrame."""
    return pd.Series(TALibWrappers.ema(data["Close"].values, period), index=data.index)


def calculate_rsi(data: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate RSI from DataFrame."""
    return pd.Series(TALibWrappers.rsi(data["Close"].values, period), index=data.index)


def calculate_macd(data: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> dict[str, pd.Series]:
    """Calculate MACD from DataFrame."""
    macd_line, signal_line, histogram = TALibWrappers.macd(data["Close"].values, fast, slow, signal)
    return {
        "MACD": pd.Series(macd_line, index=data.index),
        "Signal": pd.Series(signal_line, index=data.index),
        "Histogram": pd.Series(histogram, index=data.index),
    }


def calculate_bollinger_bands(data: pd.DataFrame, period: int = 20, std_dev: float = 2.0) -> dict[str, pd.Series]:
    """Calculate Bollinger Bands from DataFrame."""
    upper, middle, lower = TALibWrappers.bollinger_bands(data["Close"].values, period, std_dev)
    return {
        "Upper": pd.Series(upper, index=data.index),
        "Middle": pd.Series(middle, index=data.index),
        "Lower": pd.Series(lower, index=data.index),
    }


def calculate_atr(data: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate ATR from DataFrame."""
    atr = TALibWrappers.atr(data["High"].values, data["Low"].values, data["Close"].values, period)
    return pd.Series(atr, index=data.index)
