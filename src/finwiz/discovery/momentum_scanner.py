"""
Momentum scanner for newcomer discovery.

Scans for momentum signals using RSI (via TA-Lib), volume anomalies,
and rate-of-change to identify trending investment candidates.
"""

from __future__ import annotations

from typing import Any, ClassVar

import numpy as np
import pandas as pd
import talib
import yfinance as yf

from finwiz.discovery.fundamentals_adapter import yfinance_info_to_fundamentals_data
from finwiz.discovery.signal_curves import (
    has_at_least_one_strong_signal,
    momentum_signal_score,
    rsi_signal_score,
    volume_anomaly_score,
)
from finwiz.discovery.ticker_utils import to_yfinance_symbol
from finwiz.schemas.newcomer_discovery import NewcomerCandidate
from finwiz.scoring.fundamental_scorer import FundamentalScorer
from finwiz.tools.logger import get_logger

_FUND_SCORE_FLOOR: float = 0.40
_MIN_COMPOSITE_FLOOR: float = 0.55
_FUNDAMENTALS_WEIGHT: float = 0.40
_MOMENTUM_WEIGHT: float = 1.0 - _FUNDAMENTALS_WEIGHT


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
        asset_class: str = "stock",
        max_candidates: int = 20,
    ) -> list[NewcomerCandidate]:
        """Scan universe for momentum candidates.

        Args:
            universe: List of ticker symbols to scan.
            asset_class: Asset class of the universe ("stock", "etf", "crypto").
                Drives yfinance symbol normalization and the ``asset_class``
                field on each emitted ``NewcomerCandidate``.
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
            result = self._analyze_ticker(ticker, asset_class)
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

    def _analyze_ticker(
        self,
        ticker: str,
        asset_class: str,
    ) -> NewcomerCandidate | None:
        """Analyze a single ticker for momentum signals.

        Args:
            ticker: Bare ticker symbol (``BTC``, ``AAPL``, ...). The yfinance
                query form is derived via :func:`to_yfinance_symbol` so crypto
                tickers get a ``-USD`` suffix only at the query boundary.
            asset_class: Asset class used for yfinance normalization and
                propagated onto the returned ``NewcomerCandidate``.

        Returns:
            NewcomerCandidate if momentum signal detected, None otherwise.
        """
        try:
            query_symbol = to_yfinance_symbol(ticker, asset_class)
            ticker_obj = yf.Ticker(query_symbol)
            history = ticker_obj.history(period=self.LOOKBACK_PERIOD)

            if history is None or len(history) < 30:
                return None

            closes = history["Close"].to_numpy(dtype=np.float64)

            volume_signal = self._calculate_volume_anomaly(history)
            rsi_signal = self._calculate_rsi_signal(closes)
            momentum_signal = self._calculate_momentum_signal(closes)
            momentum_composite = self._composite_momentum_score(
                volume_signal,
                rsi_signal,
                momentum_signal,
            )

            info = ticker_obj.info
            name = info.get("longName") or info.get("shortName") or ticker

            rsi_values = talib.RSI(closes, timeperiod=self.RSI_PERIOD)
            rsi_value = float(rsi_values[-1]) if not np.isnan(rsi_values[-1]) else 0.0
            roc_values = talib.ROC(closes, timeperiod=self.MOMENTUM_PERIOD)
            roc_value_pct = float(roc_values[-1]) if not np.isnan(roc_values[-1]) else 0.0
            roc_decimal = roc_value_pct / 100.0
            volume_ratio = self._raw_volume_ratio(history)

            composite, fund_score = self._blend_with_fundamentals(
                momentum_composite,
                info,
                asset_class,
            )

            if not self._passes_quality_gate(
                composite,
                volume_ratio,
                rsi_value,
                roc_decimal,
                fund_score,
                asset_class,
            ):
                return None

            metadata: dict[str, Any] = {
                "rsi": round(rsi_value, 2),
                "volume_ratio": round(volume_ratio, 2),
                "momentum_roc": round(roc_value_pct, 4),
                "rsi_signal": round(rsi_signal, 4),
                "volume_signal": round(volume_signal, 4),
                "momentum_signal": round(momentum_signal, 4),
                "momentum_composite": round(momentum_composite, 4),
            }
            if fund_score is not None:
                metadata["fundamental_score"] = round(fund_score, 4)

            return NewcomerCandidate(
                ticker=ticker,
                source="momentum",
                asset_class=asset_class,  # type: ignore[arg-type]
                composite_score=composite,
                grade="",
                market_cap=info.get("marketCap"),
                sector=info.get("sector"),
                name=name,
                momentum_score=momentum_signal,
                metadata=metadata,
                rationale=(f"Momentum signals: RSI={rsi_value:.1f}, volume ratio={volume_ratio:.1f}x, ROC={roc_value_pct:.2f}"),
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

        Delegates to the shared ``volume_anomaly_score`` curve so gating
        agrees across ``MomentumScanner`` and ``BreakoutDetector``.
        """
        return volume_anomaly_score(self._raw_volume_ratio(history))

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

        Delegates to the shared smooth-hump ``rsi_signal_score`` curve,
        replacing the previous cliff at RSI 80.
        """
        rsi = talib.RSI(closes, timeperiod=self.RSI_PERIOD)
        rsi_value = float(rsi[-1])
        if np.isnan(rsi_value):
            return 0.0
        return rsi_signal_score(rsi_value)

    def _calculate_momentum_signal(self, closes: np.ndarray) -> float:
        """Calculate price momentum signal via rate-of-change (0.0-1.0).

        Delegates to the shared ``momentum_signal_score`` curve which
        extends the ceiling so strong movers are distinguishable.
        ``talib.ROC`` returns percentage points, so divide by 100 to
        match the decimal-form contract expected by the scorer.
        """
        roc = talib.ROC(closes, timeperiod=self.MOMENTUM_PERIOD)
        roc_value = float(roc[-1])
        if np.isnan(roc_value):
            return 0.0
        return momentum_signal_score(roc_value / 100.0)

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

    def _blend_with_fundamentals(
        self,
        momentum_composite: float,
        info: dict[str, Any],
        asset_class: str,
    ) -> tuple[float, float | None]:
        """Blend momentum composite with fundamentals for stocks/ETFs.

        Crypto stays momentum-only: yfinance ``info`` has no ROE / expense
        ratio surface, so no blend is performed.

        Returns:
            Tuple ``(composite, fund_score)``. ``fund_score`` is ``None``
            when the blend wasn't applied (crypto, or missing primary
            fields).
        """
        if asset_class not in ("stock", "etf"):
            return momentum_composite, None
        fundamentals_data = yfinance_info_to_fundamentals_data(info, asset_class)
        if fundamentals_data is None:
            return momentum_composite, None
        fund_score, _ = FundamentalScorer().calculate_fundamental_score(
            asset_class,
            fundamentals_data,
        )
        blended = _MOMENTUM_WEIGHT * momentum_composite + _FUNDAMENTALS_WEIGHT * fund_score
        return max(0.0, min(1.0, blended)), fund_score

    def _passes_quality_gate(
        self,
        composite: float,
        volume_ratio: float,
        rsi_value: float,
        roc_decimal: float,
        fund_score: float | None,
        asset_class: str,
    ) -> bool:
        """Minimum-quality gate — weak-signal candidates are excluded, not low-graded.

        Three independent tests; all must pass:

        * Composite clears ``_MIN_COMPOSITE_FLOOR``.
        * At least one signal (volume, RSI, ROC) fires above its strong threshold.
        * For stocks/ETFs with usable fundamentals, ``fund_score`` ≥ floor — so
          a ticker riding entirely on momentum with actively bad fundamentals
          gets dropped rather than surfaced.
        """
        if composite < _MIN_COMPOSITE_FLOOR:
            return False
        if not has_at_least_one_strong_signal(volume_ratio, rsi_value, roc_decimal, asset_class):
            return False
        if fund_score is not None and fund_score < _FUND_SCORE_FLOOR:
            return False
        return True
