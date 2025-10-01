"""
Basic Technical Indicators.

Simple moving averages, exponential moving averages, and RSI calculations.
"""

from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

from .technical_indicators import TALibWrappers
from .technical_models import SignalStrength, SignalType, TechnicalIndicatorResult, TechnicalSignal


class BasicIndicators:
    """Calculator for basic technical indicators."""

    def __init__(self, logger: Any) -> None:
        """Initialize with logger."""
        self.logger = logger

    def calculate_sma(self, data: pd.DataFrame, periods: list[int]) -> TechnicalIndicatorResult:
        """
        Calculate Simple Moving Average using TA-Lib.

        Args:
            data: OHLCV data DataFrame
            periods: List of periods to calculate

        Returns:
            Technical indicator result with SMA values and signals

        """
        close_prices = data["Close"].values.astype(np.float64)
        sma_values = {}
        signals = []

        for period in periods:
            if len(close_prices) < period:
                self.logger.warning(f"Insufficient data for SMA({period}): need {period}, have {len(close_prices)}")
                continue

            sma = TALibWrappers.sma(close_prices, period)
            sma_values[f"SMA_{period}"] = sma.tolist()

            # Generate signals based on price vs SMA
            current_price = close_prices[-1]
            current_sma = sma[-1]

            if not np.isnan(current_sma):
                if current_price > current_sma * 1.02:  # 2% above SMA
                    signal_type = SignalType.BUY
                    strength = SignalStrength.MODERATE
                elif current_price < current_sma * 0.98:  # 2% below SMA
                    signal_type = SignalType.SELL
                    strength = SignalStrength.MODERATE
                else:
                    signal_type = SignalType.HOLD
                    strength = SignalStrength.WEAK

                confidence = min(0.9, abs(current_price - current_sma) / current_sma * 10)

                signals.append(
                    TechnicalSignal(
                        indicator=f"SMA_{period}",
                        signal_type=signal_type,
                        strength=strength,
                        confidence=confidence,
                        timestamp=datetime.now(),
                        price_level=current_price,
                        description=f"Price is {((current_price / current_sma - 1) * 100):.1f}% "
                        f"{'above' if current_price > current_sma else 'below'} SMA({period})",
                        metadata={"sma_value": current_sma, "period": period},
                    )
                )

        return TechnicalIndicatorResult(
            indicator_name="SMA",
            signals=signals,
            raw_values=sma_values,
            metadata={"periods": periods},
        )

    def calculate_ema(self, data: pd.DataFrame, periods: list[int]) -> TechnicalIndicatorResult:
        """
        Calculate Exponential Moving Average using TA-Lib.

        Args:
            data: OHLCV data DataFrame
            periods: List of periods to calculate

        Returns:
            Technical indicator result with EMA values and signals

        """
        close_prices = data["Close"].values.astype(np.float64)
        ema_values = {}
        signals = []

        for period in periods:
            if len(close_prices) < period:
                self.logger.warning(f"Insufficient data for EMA({period}): need {period}, have {len(close_prices)}")
                continue

            ema = TALibWrappers.ema(close_prices, period)
            ema_values[f"EMA_{period}"] = ema.tolist()

            # Generate signals based on price vs EMA
            current_price = close_prices[-1]
            current_ema = ema[-1]

            if not np.isnan(current_ema):
                if current_price > current_ema * 1.015:  # 1.5% above EMA
                    signal_type = SignalType.BUY
                    strength = SignalStrength.MODERATE
                elif current_price < current_ema * 0.985:  # 1.5% below EMA
                    signal_type = SignalType.SELL
                    strength = SignalStrength.MODERATE
                else:
                    signal_type = SignalType.HOLD
                    strength = SignalStrength.WEAK

                confidence = min(0.9, abs(current_price - current_ema) / current_ema * 15)

                signals.append(
                    TechnicalSignal(
                        indicator=f"EMA_{period}",
                        signal_type=signal_type,
                        strength=strength,
                        confidence=confidence,
                        timestamp=datetime.now(),
                        price_level=current_price,
                        description=f"Price is {((current_price / current_ema - 1) * 100):.1f}% "
                        f"{'above' if current_price > current_ema else 'below'} EMA({period})",
                        metadata={"ema_value": current_ema, "period": period},
                    )
                )

        return TechnicalIndicatorResult(
            indicator_name="EMA",
            signals=signals,
            raw_values=ema_values,
            metadata={"periods": periods},
        )

    def calculate_rsi(
        self, data: pd.DataFrame, period: int = 14, overbought: float = 70, oversold: float = 30
    ) -> TechnicalIndicatorResult:
        """
        Calculate Relative Strength Index using TA-Lib.

        Args:
            data: OHLCV data DataFrame
            period: RSI calculation period
            overbought: Overbought threshold
            oversold: Oversold threshold

        Returns:
            Technical indicator result with RSI values and signals

        """
        close_prices = data["Close"].values.astype(np.float64)

        if len(close_prices) < period + 1:
            raise ValueError(f"Insufficient data for RSI({period}): need {period + 1}, have {len(close_prices)}")

        rsi = TALibWrappers.rsi(close_prices, period)
        current_rsi = rsi[-1]
        signals = []

        if not np.isnan(current_rsi):
            current_price = close_prices[-1]

            if current_rsi > overbought:
                signal_type = SignalType.SELL
                strength = SignalStrength.STRONG if current_rsi > 80 else SignalStrength.MODERATE
                confidence = min(0.95, (current_rsi - overbought) / (100 - overbought))
                description = f"RSI is overbought at {current_rsi:.1f}"
            elif current_rsi < oversold:
                signal_type = SignalType.BUY
                strength = SignalStrength.STRONG if current_rsi < 20 else SignalStrength.MODERATE
                confidence = min(0.95, (oversold - current_rsi) / oversold)
                description = f"RSI is oversold at {current_rsi:.1f}"
            else:
                signal_type = SignalType.HOLD
                strength = SignalStrength.WEAK
                confidence = 0.3
                description = f"RSI is neutral at {current_rsi:.1f}"

            signals.append(
                TechnicalSignal(
                    indicator="RSI",
                    signal_type=signal_type,
                    strength=strength,
                    confidence=confidence,
                    timestamp=datetime.now(),
                    price_level=current_price,
                    description=description,
                    metadata={
                        "rsi_value": current_rsi,
                        "period": period,
                        "overbought": overbought,
                        "oversold": oversold,
                    },
                )
            )

        return TechnicalIndicatorResult(
            indicator_name="RSI",
            signals=signals,
            raw_values={"RSI": rsi.tolist()},
            metadata={"period": period, "overbought": overbought, "oversold": oversold},
        )
