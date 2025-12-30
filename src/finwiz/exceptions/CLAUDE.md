# Exceptions Module

This directory contains custom exception classes for FinWiz error handling.

## Directory Structure

```
exceptions/
├── __init__.py           # Centralized exports
├── data_quality.py       # Data quality and validation exceptions
└── orchestrator.py       # Orchestrator and rebalancing exceptions
```

## Major Entry Points

| File | Class | Purpose |
|------|-------|---------|
| `data_quality.py` | `DataQualityError` | Base class for data quality issues |
| `data_quality.py` | `MissingRequiredFieldError` | Required data field is missing |
| `data_quality.py` | `GradeScoreMismatchError` | Grade doesn't match score |
| `orchestrator.py` | `PortfolioRebalancingError` | Base for rebalancing errors |
| `orchestrator.py` | `InsufficientPriceDataError` | Price data unavailable |
| `orchestrator.py` | `OptimizationFailedError` | Portfolio optimization failed |

## Usage Pattern

```python
# Import from centralized location
from finwiz.exceptions import (
    PortfolioRebalancingError,
    InsufficientPriceDataError,
    DataQualityError,
)

# Or from specific module
from finwiz.exceptions.orchestrator import PortfolioRebalancingError

def rebalance_portfolio(symbols: list[str]) -> dict:
    try:
        prices = fetch_prices(symbols)
    except PriceUnavailableError as e:
        raise InsufficientPriceDataError(missing_symbols=[e.symbol]) from e

    if not validate_prices(prices):
        raise PortfolioRebalancingError("Invalid price data")

    return calculate_trades(prices)
```

## Exception Hierarchy

```
Exception
├── DataQualityError
│   ├── MissingRequiredFieldError
│   └── GradeScoreMismatchError
│
├── PortfolioRebalancingError
│   └── InsufficientPriceDataError
│
└── OptimizationFailedError
```

## Related Modules

- `finwiz.validation` - Validation framework
- `finwiz.orchestrators` - Uses orchestrator exceptions
- `finwiz.quantitative` - Uses optimization exceptions
