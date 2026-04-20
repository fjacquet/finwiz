"""Adapter from yfinance ``Ticker.info`` dicts to the shape ``FundamentalScorer`` expects.

``FundamentalScorer.calculate_fundamental_score`` (via ``StockAnalyzer`` /
``ETFAnalyzer``) consumes a small dict of well-known keys (``roe``,
``debt_to_equity``, ...). yfinance exposes the same economics under
different names and conventions — notably ``debtToEquity`` in percent
points instead of a ratio. This module is the one place that
translation lives.

Returns ``None`` when required primary fields are missing, so callers
know to skip the fundamentals blend rather than score on defaults.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

_STOCK_REQUIRED_FIELDS: tuple[str, ...] = (
    "returnOnEquity",
    "revenueGrowth",
    "profitMargins",
)
_ETF_REQUIRED_FIELDS: tuple[str, ...] = ("annualReportExpenseRatio", "totalAssets")


def yfinance_info_to_fundamentals_data(
    info: dict[str, Any],
    asset_class: str,
) -> dict[str, Any] | None:
    """Map yfinance ``Ticker.info`` to the dict shape ``FundamentalScorer`` expects.

    Args:
        info: The raw ``Ticker.info`` dict (or any dict with yfinance-style keys).
        asset_class: ``"stock"`` or ``"etf"``. Any other value returns ``None``
            (crypto has no fundamentals surface in yfinance).

    Returns:
        A dict suitable for ``FundamentalScorer.calculate_fundamental_score``,
        or ``None`` when the required primary fields are missing.
    """
    if asset_class == "stock":
        return _stock_fundamentals(info)
    if asset_class == "etf":
        return _etf_fundamentals(info)
    return None


def _stock_fundamentals(info: dict[str, Any]) -> dict[str, Any] | None:
    if not _has_all(info, _STOCK_REQUIRED_FIELDS):
        return None
    raw_debt_to_equity = info.get("debtToEquity")
    # yfinance reports debtToEquity in percent (e.g. 45.2 means 0.452 ratio).
    debt_to_equity = float(raw_debt_to_equity) / 100.0 if raw_debt_to_equity is not None else 0.5
    return {
        "roe": float(info["returnOnEquity"]),
        "debt_to_equity": debt_to_equity,
        "revenue_growth": float(info["revenueGrowth"]),
        "profit_margin": float(info["profitMargins"]),
        "market_cap": info.get("marketCap", 0),
        "name": info.get("longName") or info.get("shortName", ""),
    }


def _etf_fundamentals(info: dict[str, Any]) -> dict[str, Any] | None:
    if not _has_all(info, _ETF_REQUIRED_FIELDS):
        return None
    return {
        "expense_ratio": float(info["annualReportExpenseRatio"]),
        "aum": float(info["totalAssets"]),
        "tracking_error": float(info.get("trackingError", 0.01)),
        "history_years": _inception_to_years(info.get("fundInceptionDate")),
        "name": info.get("longName") or info.get("shortName", ""),
    }


def _has_all(info: dict[str, Any], fields: tuple[str, ...]) -> bool:
    return all(info.get(f) is not None for f in fields)


def _inception_to_years(inception_date: Any) -> float:
    """Convert a yfinance ``fundInceptionDate`` (unix timestamp) to years of history."""
    if inception_date is None:
        return 0.0
    try:
        inception = datetime.fromtimestamp(int(inception_date), tz=UTC)
    except (TypeError, ValueError, OSError):
        return 0.0
    delta = datetime.now(tz=UTC) - inception
    return max(0.0, delta.days / 365.25)
