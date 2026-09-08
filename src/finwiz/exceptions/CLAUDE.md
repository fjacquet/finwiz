# Exceptions Module

This directory contains custom exception classes for FinWiz error handling.

## Directory Structure

```
exceptions/
├── __init__.py           # Centralized exports
└── data_quality.py       # Data quality and validation exceptions
```

## Major Entry Points

| File | Class | Purpose |
|------|-------|---------|
| `data_quality.py` | `DataQualityError` | Base class for data quality issues |
| `data_quality.py` | `MissingRequiredFieldError` | Required data field is missing |
| `data_quality.py` | `GradeScoreMismatchError` | Grade doesn't match score |

## Usage Pattern

```python
from finwiz.exceptions import MissingRequiredFieldError

raise MissingRequiredFieldError(ticker="AAPL", field="volatility", context={"source": "quantitative_analysis"})
```

## Exception Hierarchy

```
Exception
└── DataQualityError
    ├── MissingRequiredFieldError
    └── GradeScoreMismatchError
```

## Related Modules

- `finwiz.validation` - Validation framework
