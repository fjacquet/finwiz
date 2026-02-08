"""
Momentum scanner for newcomer discovery.

Scans for momentum signals using RSI (via TA-Lib), volume anomalies,
and rate-of-change to identify trending investment candidates.
"""

from __future__ import annotations

from typing import ClassVar

import numpy as np
import pandas as pd
import talib
import yfinance as yf

from finwiz.schemas.newcomer_discovery import NewcomerCandidate
from finwiz.tools.logger import get_logger


class MomentumScanner:
    """Scans for momentum signals: volume anomaly, RSI, and price momentum."""

    RSI_PERIOD: ClassVar[int] = 14
    MOMENTUM_PERIOD: ClassVar[int] = 10
    VOLUME_SMA_PERIOD: ClassVar[int] = 20
    VOLUME_ANOMALY_THRESHOLD: ClassVar[float] = 2.0  # 2x SMA volume
    LOOKBACK_PERIOD: ClassVar[str] = "3mo"

    # Composite weights
    WEIGHT_VOLUME: ClassVar[float] = 0.3
    WEIGHT_RSI: ClassVar[float] = 0.4
    WEIGHT_MOMENTUM: ClassVar[float] = 0.3

    def __init__(self) -> None:
        """Initialize momentum scanner."""
        self._logger = get_logger(__name__)

    def scan(
        self,
        universe: list[str],
        max_candidates: int = 20,
    ) -> list[NewcomerCandidate]:
        """Scan universe for momentum candidates.

        Args:
            universe: List of ticker symbols to scan.
            max_candidates: Maximum number of candidates to return.

        Returns:
            List of NewcomerCandidate sorted by composite_score descending.
        """
        self._logger.info(
            "Scanning %d tickers for momentum signals",
            len(universe),
        )
        candidates: list[NewcomerCandidate] = []

        for ticker in universe:
            result = self._analyze_ticker(ticker)
            if result is not None:
                candidates.append(result)

        candidates.sort(key=lambda c: c.composite_score, reverse=True)
        top = candidates[:max_candidates]
        self._logger.info(
            "Momentum scan returned %d candidates from %d scanned",
            len(top),
            len(universe),
        )
        return top

    def _analyze_ticker(self, ticker: str) -> NewcomerCandidate | None:
        """Analyze a single ticker for momentum signals.

        Args:
            ticker: Stock ticker symbol.

        Returns:
            NewcomerCandidate if momentum signal detected, None otherwise.
        """
        try:
            ticker_obj = yf.Ticker(ticker)
            history = ticker_obj.history(period=self.LOOKBACK_PERIOD)

            if history is None or len(history) < 30:
                return None

            closes = history["Close"].to_numpy(dtype=np.float64)

            volume_signal = self._calculate_volume_anomaly(history)
            rsi_signal = self._calculate_rsi_signal(closes)
            momentum_signal = self._calculate_momentum_signal(closes)
            composite = self._composite_momentum_score(
                volume_signal,
                rsi_signal,
                momentum_signal,
            )

            if composite < 0.3:
                return None

            info = ticker_obj.info
            name = info.get("longName") or info.get("shortName") or ticker

            # Get raw indicator values for metadata
            rsi_values = talib.RSI(closes, timeperiod=self.RSI_PERIOD)
            rsi_value = float(rsi_values[-1]) if not np.isnan(rsi_values[-1]) else 0.0
            roc_values = talib.ROC(closes, timeperiod=self.MOMENTUM_PERIOD)
            roc_value = float(roc_values[-1]) if not np.isnan(roc_values[-1]) else 0.0
            volume_ratio = self._raw_volume_ratio(history)

            return NewcomerCandidate(
                ticker=ticker,
                source="momentum",
                asset_class="stock",
                composite_score=composite,
                grade="",
                market_cap=info.get("marketCap"),
                sector=info.get("sector"),
                name=name,
                momentum_score=momentum_signal,
                metadata={
                    "rsi": round(rsi_value, 2),
                    "volume_ratio": round(volume_ratio, 2),
                    "momentum_roc": round(roc_value, 4),
                    "rsi_signal": round(rsi_signal, 4),
                    "volume_signal": round(volume_signal, 4),
                    "momentum_signal": round(momentum_signal, 4),
                },
                rationale=(f"Momentum signals: RSI={rsi_value:.1f}, volume ratio={volume_ratio:.1f}x, ROC={roc_value:.2f}"),
            )
        except (ValueError, KeyError, TypeError):
            self._logger.warning(
                "Failed to analyze ticker %s for momentum",
                ticker,
                exc_info=True,
            )
            return None

    def _calculate_volume_anomaly(self, history: pd.DataFrame) -> float:
        """Calculate volume anomaly score (0.0-1.0).

        Args:
            history: Price/volume DataFrame.

        Returns:
            Score reflecting how anomalous current volume is vs SMA.
        """
        ratio = self._raw_volume_ratio(history)
        if ratio >= self.VOLUME_ANOMALY_THRESHOLD:
            return min(1.0, (ratio - 1.0) / 4.0)
        # Partial credit for above-average volume
        return max(0.0, ratio / self.VOLUME_ANOMALY_THRESHOLD * 0.5)

    def _raw_volume_ratio(self, history: pd.DataFrame) -> float:
        """Calculate current volume / SMA volume ratio.

        Args:
            history: Price/volume DataFrame.

        Returns:
            Volume ratio, or 0.0 if SMA is zero/NaN.
        """
        volumes = history["Volume"]
        sma = float(
            volumes.iloc[:-1].rolling(self.VOLUME_SMA_PERIOD).mean().iloc[-1],
        )
        if sma <= 0 or pd.isna(sma):
            return 0.0
        return float(volumes.iloc[-1]) / sma

    def _calculate_rsi_signal(self, closes: np.ndarray) -> float:
        """Calculate RSI-based momentum signal (0.0-1.0).

        Args:
            closes: Array of closing prices.

        Returns:
            Score based on RSI position (bullish momentum focus).
        """
        rsi = talib.RSI(closes, timeperiod=self.RSI_PERIOD)
        rsi_value = float(rsi[-1])
        if np.isnan(rsi_value):
            return 0.0

        if 50 <= rsi_value <= 70:
            return (rsi_value - 50) / 20  # 50->0, 70->1.0
        if 70 < rsi_value <= 80:
            return 0.8  # Strong but nearing overbought
        if rsi_value > 80:
            return 0.3  # Overbought, risky
        if 30 <= rsi_value < 50:
            return max(0.0, (rsi_value - 30) / 40) * 0.4  # Neutral-bearish
        # RSI < 30: oversold, potential reversal (contrarian signal)
        return 0.5

    def _calculate_momentum_signal(self, closes: np.ndarray) -> float:
        """Calculate price momentum signal via rate-of-change (0.0-1.0).

        Args:
            closes: Array of closing prices.

        Returns:
            Score based on ROC. Positive ROC = bullish momentum.
        """
        roc = talib.ROC(closes, timeperiod=self.MOMENTUM_PERIOD)
        roc_value = float(roc[-1])
        if np.isnan(roc_value):
            return 0.0

        if roc_value > 0:
            return min(1.0, roc_value / 20.0)  # 20% ROC = perfect score
        return 0.0

    def _composite_momentum_score(
        self,
        volume: float,
        rsi: float,
        momentum: float,
    ) -> float:
        """Calculate weighted composite momentum score.

        Args:
            volume: Volume anomaly signal (0-1).
            rsi: RSI signal (0-1).
            momentum: Momentum/ROC signal (0-1).

        Returns:
            Weighted composite clamped to [0.0, 1.0].
        """
        raw = self.WEIGHT_VOLUME * volume + self.WEIGHT_RSI * rsi + self.WEIGHT_MOMENTUM * momentum
        return max(0.0, min(1.0, raw))
