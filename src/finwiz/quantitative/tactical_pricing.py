# src/finwiz/quantitative/tactical_pricing.py
"""Tactical (3-6 month) price targets and sell-level floors per holding.

Thin orchestration over existing primitives:
- ``calculate_support_resistance_targets`` for technical levels.
- A close-only ATR proxy for volatility-adjusted floor.
- Log-return drift over the trailing window for forward projection.

Returns a :class:`PriceTargets` Pydantic model already wired into
``HoldingDecision``. AI-Minimalism (ADR-003) preserved — pure Python.

See ADR-011 for the full design rationale.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Literal

import numpy as np
import pandas as pd
from crewai_custom_tools.tools.analytics.price_targets import calculate_support_resistance_targets

from finwiz.schemas.portfolio_review import PriceTargets

logger = logging.getLogger(__name__)


# Drift caps — keep upside projections tied to plausibility.
_DRIFT_CAP_STOCK_ETF = 0.25
_DRIFT_CAP_CRYPTO = 0.40

# Minimum history before any computation is meaningful.
_MIN_HISTORY_DAYS = 60
_LOW_CONFIDENCE_THRESHOLD_DAYS = 120

# Reject a price series whose last bar is older than this — stale anchor risk.
_MAX_HISTORY_LAG_DAYS = 7


def _atr(prices: pd.Series, period: int = 14) -> float:
    """Average True Range proxy from a close-only series."""
    if len(prices) < period + 1:
        return float("nan")
    daily_changes = prices.diff().abs().dropna()
    if daily_changes.empty:
        return float("nan")
    rolled = daily_changes.rolling(window=period, min_periods=period).mean()
    last = rolled.iloc[-1]
    return float(last) if np.isfinite(last) else float("nan")


def _annualized_log_return(prices: pd.Series) -> float:
    """Compute annualized log return over the supplied window."""
    if len(prices) < 2:
        return 0.0
    if prices.iloc[0] <= 0 or prices.iloc[-1] <= 0:
        return 0.0
    log_ret = np.log(prices.iloc[-1] / prices.iloc[0])
    days = (prices.index[-1] - prices.index[0]).days or 1
    annualized = float(log_ret) * (365.25 / days)
    if not np.isfinite(annualized):
        return 0.0
    return annualized


def _confidence(prices: pd.Series, target: float, drift_target: float, current: float) -> str:
    """Three-bucket confidence label."""
    if len(prices) < _LOW_CONFIDENCE_THRESHOLD_DAYS:
        return "low"
    if current <= 0 or target <= 0 or drift_target <= 0:
        return "low"
    pct_diff = abs(target - drift_target) / current
    if pct_diff <= 0.10:
        return "high"
    if pct_diff <= 0.20:
        return "medium"
    return "low"


def _is_history_fresh(prices: pd.Series) -> bool:
    """Reject obviously stale price history."""
    if prices.empty:
        return False
    last_dt = prices.index[-1]
    if not isinstance(last_dt, pd.Timestamp):
        last_dt = pd.Timestamp(last_dt)
    # Match the timezone of the input so the subtraction never crashes.
    if last_dt.tzinfo is not None:
        now = pd.Timestamp.now(tz=last_dt.tzinfo)
    else:
        now = pd.Timestamp.now()
    age = now.normalize() - last_dt.normalize()
    return age <= pd.Timedelta(days=_MAX_HISTORY_LAG_DAYS)


def compute_tactical_pricing(
    ticker: str,
    asset_class: Literal["stock", "etf", "crypto"],
    price_history: pd.Series,
    current_price: float,
    *,
    horizon_months: int = 4,
    currency: str = "USD",
) -> PriceTargets | None:
    """Compute a 3-6 month tactical target and a stop-loss floor.

    Returns ``None`` when input is unusable:
    - fewer than 60 trading days of history
    - last price more than 7 calendar days old
    - current_price not finite or non-positive
    """
    if not np.isfinite(current_price) or current_price <= 0:
        logger.warning(f"tactical_pricing: invalid current_price={current_price} for {ticker}")
        return None
    if len(price_history) < _MIN_HISTORY_DAYS:
        logger.warning(
            f"tactical_pricing: insufficient history for {ticker} ({len(price_history)} < {_MIN_HISTORY_DAYS} days)",
        )
        return None
    if not _is_history_fresh(price_history):
        logger.warning(f"tactical_pricing: stale history for {ticker} — skipping")
        return None

    # ADR-011 follow-up: reject degenerate price history (NaN-heavy, all-zero).
    clean = price_history.replace([np.inf, -np.inf], np.nan).dropna()
    if len(clean) < _MIN_HISTORY_DAYS:
        logger.warning(
            f"tactical_pricing: only {len(clean)} clean bars for {ticker} after NaN/inf filter (< {_MIN_HISTORY_DAYS}); skipping",
        )
        return None
    if clean.max() <= 0:
        logger.warning(f"tactical_pricing: non-positive price series for {ticker}; skipping")
        return None

    # ---- target: max(technical resistance, drift) capped per asset class ----
    sr = calculate_support_resistance_targets(clean, current_price=current_price)
    resistance = float(sr["resistance"].target_price) or current_price * 1.10
    support = float(sr["support"].target_price) or current_price * 0.90

    horizon_years = horizon_months / 12.0
    annual_log_ret = _annualized_log_return(clean)
    drift_target = float(current_price * np.exp(annual_log_ret * horizon_years))
    if not np.isfinite(drift_target) or drift_target <= 0:
        drift_target = current_price

    cap = _DRIFT_CAP_CRYPTO if asset_class == "crypto" else _DRIFT_CAP_STOCK_ETF
    drift_target_capped = float(min(drift_target, current_price * (1.0 + cap)))

    # Breakout: current price has exceeded the historical trading range top.
    # The S/R function may still return a projected resistance above current price
    # in this scenario; use the historical high as the breakout detector instead.
    historical_high = float(clean.max())
    is_breakout = current_price > historical_high
    if is_breakout:
        target = drift_target_capped
        target_method = "cassure haussière — projection par dérive"
    else:
        target = float(max(resistance, drift_target_capped))
        target = float(min(target, current_price * (1.0 + cap)))
        target_method = "max(résistance technique, dérive projetée)"

    # ---- sell-level: max(support, current - 2*ATR) ----
    atr = _atr(clean)
    if not np.isfinite(atr) or atr == 0.0:
        atr_floor = current_price * 0.85
    else:
        atr_floor = current_price - 2.0 * atr

    sell_level = float(max(support, atr_floor))
    if sell_level >= current_price:
        sell_level = atr_floor
    if not np.isfinite(sell_level) or sell_level <= 0:
        sell_level = current_price * 0.85

    confidence = _confidence(clean, target, drift_target_capped, current_price)
    confidence_fr = {"high": "élevée", "medium": "moyenne", "low": "faible"}[confidence]

    buy_rationale = f"Objectif: {target_method} sur {horizon_months} mois — confiance {confidence_fr}."
    sell_rationale = f"Plancher: max(support technique, prix − 2×ATR) — confiance {confidence_fr}."

    return PriceTargets(
        current_price=current_price,
        currency=currency,
        fair_value_estimate=None,
        buy_target_primary=target,
        buy_target_secondary=None,
        buy_rationale=buy_rationale,
        sell_target_primary=sell_level,
        sell_target_secondary=None,
        stop_loss_level=sell_level,
        sell_rationale=sell_rationale,
        calculation_method="tactical_pricing/support_resistance+drift+atr",
        confidence_level={"high": 0.8, "medium": 0.6, "low": 0.4}[confidence],
        data_as_of=datetime.now(tz=UTC),
        data_sources=["price_history"],
    )
