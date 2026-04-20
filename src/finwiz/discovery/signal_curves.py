"""Rebalanced signal curves for discovery scanners.

Replaces the cliff-heavy helpers in ``MomentumScanner`` (and shares the
volume curve with ``BreakoutDetector``) with monotone / smooth-hump
shapes so normal-volume tickers aren't silently penalized and RSI
above 80 doesn't invert. Also hosts the signal-strength gate used by
the discovery quality filter.
"""

from __future__ import annotations

from typing import Final

from finwiz.scoring.utils import interpolate_threshold_score

_MIN_VOLUME_RATIO_STRONG: Final[float] = 1.5
_MIN_RSI_STRONG: Final[float] = 60.0
_MAX_RSI_STRONG: Final[float] = 80.0
_MIN_ROC_STRONG: Final[float] = 0.10

_ROC_THRESHOLDS: Final[list[tuple[float, float]]] = [
    (0.0, 0.0),
    (0.05, 0.3),
    (0.10, 0.5),
    (0.15, 0.7),
    (0.20, 0.85),
    (0.30, 0.95),
    (0.50, 1.0),
]


def volume_anomaly_score(ratio: float) -> float:
    """Score a volume-to-SMA ratio on ``[0, 1]`` with a neutral band at 1x.

    Shape::

        ratio <= 0.0   -> 0.0   (bad data)
        0.0  - 0.5     -> 0.1   (drought, flat)
        0.5  - 0.8     -> ramp 0.1 -> 0.5
        0.8  - 1.2     -> 0.5   (neutral band: normal volume is neither signal nor penalty)
        1.2  - 3.0     -> ramp 0.5 -> 1.0
        > 3.0          -> 1.0   (strong volume inflection)
    """
    if ratio <= 0.0:
        return 0.0
    if ratio < 0.5:
        return 0.1
    if ratio < 0.8:
        return 0.1 + (ratio - 0.5) / (0.8 - 0.5) * (0.5 - 0.1)
    if ratio <= 1.2:
        return 0.5
    if ratio < 3.0:
        return 0.5 + (ratio - 1.2) / (3.0 - 1.2) * (1.0 - 0.5)
    return 1.0


def rsi_signal_score(rsi: float) -> float:
    """Smooth-hump RSI curve on ``[0, 1]``, peaking at RSI 65.

    Shape (monotone taper on each side of the bullish peak)::

        rsi <= 30     -> 0.5   (oversold reversal candidate)
        30  - 50      -> ramp 0.2 -> 0.4
        50  - 65      -> ramp 0.4 -> 1.0
        65  - 80      -> ramp 1.0 -> 0.7
        80  - 90      -> ramp 0.7 -> 0.4
        > 90          -> 0.3
    """
    if rsi <= 30.0:
        return 0.5
    if rsi < 50.0:
        return 0.2 + (rsi - 30.0) / (50.0 - 30.0) * (0.4 - 0.2)
    if rsi <= 65.0:
        return 0.4 + (rsi - 50.0) / (65.0 - 50.0) * (1.0 - 0.4)
    if rsi <= 80.0:
        return 1.0 - (rsi - 65.0) / (80.0 - 65.0) * (1.0 - 0.7)
    if rsi <= 90.0:
        return 0.7 - (rsi - 80.0) / (90.0 - 80.0) * (0.7 - 0.4)
    return 0.3


def momentum_signal_score(roc: float) -> float:
    """Score rate-of-change (decimal form, e.g. ``0.28`` for 28%) on ``[0, 1]``.

    Non-positive ROC returns ``0.0``. Positive ROC interpolates through
    ``_ROC_THRESHOLDS`` so strong movers (ENJ at 111%) separate from
    merely decent ones (AMD at 28%).
    """
    if roc <= 0.0:
        return 0.0
    return interpolate_threshold_score(roc, _ROC_THRESHOLDS)


def has_at_least_one_strong_signal(
    volume_ratio: float,
    rsi: float,
    roc: float,
    asset_class: str,
) -> bool:
    """Return ``True`` iff at least one signal fires above its strong threshold.

    A candidate with drifting volume, neutral RSI, and low ROC carries
    no real signal — emitting it into the opportunity list is noise.
    The discovery gate rejects such candidates outright rather than
    giving them a low grade.
    """
    _ = asset_class  # reserved for future asset-specific thresholds
    if volume_ratio >= _MIN_VOLUME_RATIO_STRONG:
        return True
    if _MIN_RSI_STRONG <= rsi <= _MAX_RSI_STRONG:
        return True
    return roc >= _MIN_ROC_STRONG
