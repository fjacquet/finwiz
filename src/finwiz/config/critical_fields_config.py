"""
Critical Fields Configuration for FinWiz.

Defines which fields are CRITICAL (must have real data) vs OPTIONAL (can use defaults).
Missing critical fields should cause analysis to FAIL rather than use fallback values.
"""

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


def is_critical_field(field_name: str, asset_class: Literal["stock", "etf", "crypto"]) -> bool:
    """
    Check if field is critical for given asset class.

    Args:
        field_name: Field name to check
        asset_class: Asset class

    Returns:
        True if field is critical, False otherwise

    """
    critical_fields = get_critical_fields(asset_class)
    return field_name in critical_fields


def get_safe_default(field_name: str) -> float | None:
    """
    Get safe default value for OPTIONAL field.

    Args:
        field_name: Field name

    Returns:
        Default value if field is optional, None if field is critical

    """
    return SAFE_DEFAULTS.get(field_name)


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
        # Stock metrics that should NEVER be exactly 0.0 for real companies
        "roe": lambda v: v is not None and (v < -0.5 or v > 2.0 or v == 0.0),  # ROE exactly 0.0 is suspicious
        "current_price": lambda v: v is not None and v <= 0.0,  # Price must be positive
        # These CAN be 0.0 legitimately, so only check for None or extreme values
        "debt_to_equity": lambda v: v is None or v < 0.0 or v > 100.0,
        "revenue_growth": lambda v: v is None or v < -0.95 or v > 10.0,  # -95% to 1000%
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
