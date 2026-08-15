"""
Critical Fields Configuration for FinWiz.

Defines which fields are CRITICAL (must have real data) vs OPTIONAL (can use defaults).
Missing critical fields should cause analysis to FAIL rather than use fallback values.
"""

import math
from typing import Any, Literal

# Critical fields by asset class - MUST have real data or analysis fails
CRITICAL_FIELDS = {
    "stock": [
        "current_price",  # Cannot analyze without price
        "roe",  # Core fundamental metric
        "debt_to_equity",  # Core risk metric
        "revenue_growth",  # Core growth metric
        "volatility",  # Core risk metric
        "beta",  # Core risk metric
    ],
    "etf": [
        "current_price",  # Cannot analyze without price
        "expense_ratio",  # Core cost metric
        "volatility",  # Core risk metric
        # Note: tracking_error moved to optional - many international ETFs lack benchmark data
        # Note: aum moved to optional - not available for all exchanges
    ],
    "crypto": [
        "current_price",  # Cannot analyze without price
        "market_cap",  # Core size metric
        "volume_24h",  # Core liquidity metric
        "volatility",  # Core risk metric
        "age_years",  # Core maturity metric
    ],
}

# Optional fields - can use reasonable defaults if missing
OPTIONAL_FIELDS = {
    "stock": [
        "profit_margin",  # Nice to have but not critical
        "rsi",  # Technical indicator
        "macd",  # Technical indicator
        "moving_avg_50",  # Technical indicator
        "moving_avg_200",  # Technical indicator
    ],
    "etf": [
        "tracking_error",  # Important but not always available (international ETFs)
        "aum",  # Important but not always available (all exchanges)
        "dividend_yield",  # Nice to have
        "rsi",  # Technical indicator
        "macd",  # Technical indicator
    ],
    "crypto": [
        "circulating_supply",  # Nice to have
        "max_supply",  # Nice to have
        "rsi",  # Technical indicator
        "macd",  # Technical indicator
    ],
}

# Reasonable defaults for OPTIONAL fields only
SAFE_DEFAULTS = {
    # Technical indicators - neutral values
    "rsi": 50.0,  # Neutral RSI
    "macd": 0.0,  # Neutral MACD
    "macd_signal": 0.0,  # Neutral signal
    # Optional fundamentals
    "profit_margin": 0.10,  # Conservative 10% margin
    "dividend_yield": 0.0,  # No dividend assumption
    # Optional ETF metrics
    "tracking_error": None,  # No default - will be flagged in reports
    "aum": None,  # No default - will be flagged in reports
    # Optional crypto metrics
    "circulating_supply": 0.0,  # Unknown supply
    "max_supply": 0.0,  # Unknown max
}

# Minimum data quality thresholds
MIN_QUALITY_SCORE = 0.70  # Below this, analysis should fail
MIN_COMPLETENESS_SCORE = 0.80  # Below this, analysis should fail
MIN_CRITICAL_FIELDS_RATIO = 1.0  # 100% of critical fields must be present


class CriticalFieldError(Exception):
    """Raised when critical field is missing and cannot proceed with analysis."""

    def __init__(self, ticker: str, asset_class: str, missing_fields: list[str]):
        self.ticker = ticker
        self.asset_class = asset_class
        self.missing_fields = missing_fields
        super().__init__(
            f"Cannot analyze {ticker} ({asset_class}): Missing critical fields: {', '.join(missing_fields)}. Analysis would be based on assumptions rather than real data."
        )


def get_critical_fields(asset_class: Literal["stock", "etf", "crypto"]) -> list[str]:
    """
    Get list of critical fields for asset class.

    Args:
        asset_class: Asset class

    Returns:
        List of critical field names

    """
    return CRITICAL_FIELDS.get(asset_class, [])


def get_optional_fields(asset_class: Literal["stock", "etf", "crypto"]) -> list[str]:
    """
    Get list of optional fields for asset class.

    Args:
        asset_class: Asset class

    Returns:
        List of optional field names

    """
    return OPTIONAL_FIELDS.get(asset_class, [])


def get_safe_default(field_name: str) -> float | None:
    """
    Get safe default value for OPTIONAL field.

    Args:
        field_name: Field name

    Returns:
        Default value if field is optional, None if field is critical

    """
    return SAFE_DEFAULTS.get(field_name)


# Annualized volatility above this is not a real reading — it is a units error
# or corrupt data. Below it, values > 5.0 are treated as percent-scaled and
# divided by 100 (two producers in-tree disagree on units; see
# quantitative/performance_metrics.py:90 vs quantitative/backtesting_performance.py:246).
_VOLATILITY_ABSURD_CEILING = 500.0


def normalize_volatility(value: float | int | None) -> float | None:
    """Coerce a volatility reading to the fractional scale, or None if unusable.

    Args:
        value: Raw volatility, fractional (0.25) or percent-scaled (25.0).

    Returns:
        Fractional volatility, or None when the value is missing, non-finite (NaN/inf),
        negative, or absurd.

    """
    if value is None:
        return None
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(v):
        # Covers NaN, +inf, and -inf: comparisons against NaN are always False, so the
        # range checks below would otherwise let it slide through as "valid".
        return None
    if v < 0.0 or v >= _VOLATILITY_ABSURD_CEILING:
        return None
    if v > 5.0:
        return v / 100.0
    return v


def validate_critical_fields(ticker: str, asset_class: Literal["stock", "etf", "crypto"], data: dict[str, Any]) -> None:
    """
    Validate that all critical fields are present with real data.

    Args:
        ticker: Asset ticker
        asset_class: Asset class
        data: Data dictionary to validate

    Raises:
        CriticalFieldError: If any critical field is missing or has nonsensical values

    """
    critical_fields = get_critical_fields(asset_class)
    missing_fields = []

    # Sanity check ranges for critical numeric fields
    # These catch data extraction errors (e.g., defaults of 0.0 that passed through)
    SANITY_CHECKS = {
        # Stock metrics — only flag extreme outliers likely caused by data errors
        "roe": lambda v: v is not None and (v < -5.0 or v > 5.0),  # ROE outside -500%..500% is suspicious
        "current_price": lambda v: v is not None and v <= 0.0,  # Price must be positive
        # These CAN be 0.0 legitimately, so only check for None or extreme values
        "debt_to_equity": lambda v: v is None or v < 0.0 or v > 100.0,
        "revenue_growth": lambda v: v is None or v < -0.95 or v > 10.0,  # -95% to 1000%
        # Backstop only — normalize_volatility() already rejects/rescales upstream in the
        # loop below, so a normalized value can never trip this. Kept so the field's
        # contract doesn't silently depend on the caller remembering to normalize first.
        "volatility": lambda v: v is None or v < 0.0 or v > 5.0,
        "beta": lambda v: v is None or v < -5.0 or v > 10.0,
        # ETF metrics
        "expense_ratio": lambda v: v is None or v < 0.0 or v > 0.10,  # 0-10%
        # Crypto metrics
        "market_cap": lambda v: v is None or v <= 0.0,
        "volume_24h": lambda v: v is None or v < 0.0,
        "age_years": lambda v: v is None or v < 0.0 or v > 50.0,
    }

    for field in critical_fields:
        value = data.get(field)

        if field == "volatility":
            normalized = normalize_volatility(value)
            if normalized is not None:
                value = normalized
                data[field] = value
            elif value is not None:
                # Present but unusable (negative or absurd) — a units/data error,
                # not a missing field. Report it honestly instead of masking it
                # as "missing".
                missing_fields.append(f"{field} (invalid value: {value})")
                continue

        # Check if field is missing or None
        if field not in data or value is None:
            missing_fields.append(f"{field} (missing)")
            continue

        # Apply sanity checks for known problematic fields
        if field in SANITY_CHECKS:
            sanity_check = SANITY_CHECKS[field]
            if sanity_check(value):
                missing_fields.append(f"{field} (invalid value: {value})")

    if missing_fields:
        raise CriticalFieldError(ticker, asset_class, missing_fields)
