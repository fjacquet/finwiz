"""
Breakout detector for newcomer discovery.

Identifies price and volume breakout signals on small/mid-cap stocks
($200M-$50B market cap) using yfinance price history.
"""

from __future__ import annotations

from typing import ClassVar

import pandas as pd
import yfinance as yf

from finwiz.schemas.newcomer_discovery import NewcomerCandidate
from finwiz.tools.logger import get_logger


class BreakoutDetector:
    """Detects price and volume breakout signals on small/mid-cap stocks."""

    MIN_MARKET_CAP: ClassVar[float] = 200e6  # $200M
    MAX_MARKET_CAP: ClassVar[float] = 50e9  # $50B
    LOOKBACK_PERIOD: ClassVar[str] = "3mo"
    VOLUME_SPIKE_THRESHOLD: ClassVar[float] = 2.0  # 2x average volume
    PRICE_BREAKOUT_WINDOW: ClassVar[int] = 20  # 20-day high lookback

    def __init__(self) -> None:
        """Initialize breakout detector."""
        self._logger = get_logger(__name__)

    def detect(
        self,
        universe: list[str],
        max_candidates: int = 20,
    ) -> list[NewcomerCandidate]:
        """Detect breakout candidates from a ticker universe.

        Args:
            universe: List of ticker symbols to scan.
            max_candidates: Maximum number of candidates to return.

        Returns:
            List of NewcomerCandidate objects sorted by composite_score descending.
        """
        self._logger.info(
            "Scanning %d tickers for breakout signals",
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
            "Breakout detection returned %d candidates from %d scanned",
            len(top),
            len(universe),
        )
        return top

    def _analyze_ticker(self, ticker: str) -> NewcomerCandidate | None:
        """Analyze a single ticker for breakout signals.

        Args:
            ticker: Stock ticker symbol.

        Returns:
            NewcomerCandidate if breakout detected, None otherwise.
        """
        try:
            market_cap = self._get_market_cap(ticker)
            if not self._passes_market_cap_filter(market_cap):
                return None

            ticker_obj = yf.Ticker(ticker)
            history = ticker_obj.history(period=self.LOOKBACK_PERIOD)

            if history is None or len(history) < self.PRICE_BREAKOUT_WINDOW:
                return None

            price_score = self._check_price_breakout(history)
            volume_score = self._check_volume_breakout(history)
            composite = 0.5 * price_score + 0.5 * volume_score

            if composite < 0.3:
                return None

            info = ticker_obj.info
            name = info.get("longName") or info.get("shortName") or ticker

            return NewcomerCandidate(
                ticker=ticker,
                source="breakout",
                asset_class="stock",
                composite_score=composite,
                grade="",
                market_cap=market_cap,
                sector=info.get("sector"),
                name=name,
                metadata={
                    "price_breakout_score": round(price_score, 4),
                    "volume_breakout_score": round(volume_score, 4),
                    "20d_high": float(history["Close"].iloc[-self.PRICE_BREAKOUT_WINDOW : -1].max()),
                    "volume_ratio": self._volume_ratio(history),
                },
                rationale=(
                    f"Price/volume breakout detected: "
                    f"price score {price_score:.2f}, volume score {volume_score:.2f}"
                ),
            )
        except Exception:
            self._logger.warning(
                "Failed to analyze ticker %s for breakout",
                ticker,
                exc_info=True,
            )
            return None

    def _check_price_breakout(self, history: pd.DataFrame) -> float:
        """Calculate price breakout score (0.0-1.0).

        Args:
            history: DataFrame with at least PRICE_BREAKOUT_WINDOW rows.

        Returns:
            Score from 0.0 (no breakout) to 1.0 (strong breakout).
        """
        closes = history["Close"]
        current = float(closes.iloc[-1])
        n_day_high = float(closes.iloc[-self.PRICE_BREAKOUT_WINDOW : -1].max())

        if current > n_day_high and n_day_high > 0:
            return min(1.0, (current - n_day_high) / n_day_high * 10)
        return 0.0

    def _check_volume_breakout(self, history: pd.DataFrame) -> float:
        """Calculate volume breakout score (0.0-1.0).

        Args:
            history: DataFrame with volume data.

        Returns:
            Score from 0.0 (no spike) to 1.0 (extreme volume spike).
        """
        ratio = self._volume_ratio(history)
        if ratio >= self.VOLUME_SPIKE_THRESHOLD:
            return min(1.0, (ratio - 1.0) / 4.0)
        return 0.0

    def _volume_ratio(self, history: pd.DataFrame) -> float:
        """Calculate current volume / 20-day average volume.

        Args:
            history: DataFrame with volume data.

        Returns:
            Volume ratio. 0.0 if average volume is zero or NaN.
        """
        volumes = history["Volume"]
        avg_volume = float(volumes.iloc[:-1].tail(self.PRICE_BREAKOUT_WINDOW).mean())
        if avg_volume <= 0 or pd.isna(avg_volume):
            return 0.0
        current_volume = float(volumes.iloc[-1])
        return current_volume / avg_volume

    def _get_market_cap(self, ticker: str) -> float | None:
        """Get market capitalization for a ticker.

        Args:
            ticker: Stock ticker symbol.

        Returns:
            Market cap in USD, or None on failure.
        """
        try:
            return yf.Ticker(ticker).info.get("marketCap")
        except Exception:
            self._logger.warning(
                "Failed to get market cap for %s",
                ticker,
                exc_info=True,
            )
            return None

    def _passes_market_cap_filter(self, market_cap: float | None) -> bool:
        """Check if market cap is within the small/mid-cap range.

        Args:
            market_cap: Market cap value or None.

        Returns:
            True if within MIN_MARKET_CAP..MAX_MARKET_CAP range.
        """
        return (
            market_cap is not None
            and self.MIN_MARKET_CAP <= market_cap <= self.MAX_MARKET_CAP
        )
