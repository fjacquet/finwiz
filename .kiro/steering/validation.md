---
inclusion: always
---

# Validation Standards for FinWiz

Data validation rules and quality standards for FinWiz development.

## Core Validation Principles

### 1. Schema Compliance

- Use strict Pydantic v2 models with `extra='forbid'`
- All outputs must conform to registered schemas
- Validate at crew boundaries
- Provide field-level error context

### 2. Validation Modes

Configure via `VALIDATION_STRICTNESS` environment variable:

- `off`: Validation disabled (development only)
- `warn`: Errors converted to warnings, processing continues (default)
- `error`: Strict enforcement, halt on validation errors (production)

### 3. Risk Assessment Standards

- Use `RiskAssessmentStandardized` schema
- 0-5 scale scoring (0=Very Low, 5=Very High)
- Include systematic and idiosyncratic risk components
- Follow standardized risk taxonomy

## Validation Manager Usage

```python
from finwiz.validation import get_validation_manager

manager = get_validation_manager()

# Validate crew output
result = manager.validate_crew_output(data, "stock", "analysis")

if result.is_valid:
    processed_data = result.sanitized_data
else:
    for error in result.errors:
        logger.error(f"Validation error at {error.field_path}: {error.message}")
```

## Schema Registry

All schemas must be registered:

```python
from finwiz.validation import get_registry

registry = get_registry()

# Register crew schema
registry.register_crew_schema("stock", "analysis", TenKInsight)

# Lookup schema
schema = registry.get_schema("TenKInsight")
```

## A+ Investment Validation Criteria

### Backtesting Requirements (25% weight)

- **Minimum Period**: 5 years historical data
- **Market Regimes**: Test across bull, bear, sideways markets
- **Minimum Return**: 8% annualized
- **Rejection**: <8% annual return

### Risk-Adjusted Performance (20% weight)

- **Sharpe Ratio**: Minimum 1.0
- **Sortino Ratio**: Downside risk assessment
- **Calmar Ratio**: Risk-adjusted with max drawdown
- **Rejection**: Sharpe <1.0

### Downside Risk Control (20% weight)

- **Maximum Drawdown**: -25% maximum
- **Value at Risk**: 95% confidence level
- **Expected Shortfall**: Tail risk assessment
- **Rejection**: Max drawdown >-25%

### Consistency Requirements (15% weight)

- **Win Rate**: Minimum 45%
- **Trade Consistency**: Across time periods
- **Performance Stability**: Across market conditions
- **Rejection**: Win rate <45%

### Regime Consistency (20% weight)

- **Multi-Regime Performance**: Reasonable across all regimes
- **Minimum Consistency**: 60% score
- **Regime Analysis**: Bull, bear, sideways markets
- **Rejection**: Consistency <60%

### Overall Validation

- **Passing Threshold**: 70% overall score
- **Grade Assignment**: Only ≥70% receive A+ recommendations

## Asset-Specific Validation

### ETFs

- Tracking error ≤0.20% (3-year)
- Expense ratio ≤0.15% (broad) or ≤0.25% (specialized)
- AUM ≥$1B
- UCITS compliant (for European investors)

### Stocks

- ROE ≥20%
- Revenue growth ≥15% annually
- Debt/equity ≤0.3
- Positive and growing free cash flow

### Crypto

- Market cap ≥$10B
- Daily volume ≥$500M
- Operating history ≥3 years
- Clear regulatory compliance pathway

## Data Quality Standards

### Required Fields

- All required fields must be present
- No null values for required fields
- Proper data types enforced
- Valid enum values only

### Data Freshness

- Validate data timestamps
- Check against freshness thresholds
- Flag stale data (>30 days)
- Reduce confidence for old data

### Data Sources

- Cite all data sources
- Include as-of dates
- Provide URLs where applicable
- Note data limitations

## Error Handling

### Validation Errors

```python
class ValidationError(BaseModel):
    field_path: str
    message: str
    error_type: str
    context: dict
```

### Error Response

- Provide clear error messages
- Include field path for context
- Suggest remediation steps
- Log for debugging

### Graceful Degradation

- Use cached data if available
- Fall back to baseline analysis
- Continue with partial data
- Flag for manual review

## Validation Checklist

Before accepting any data:

1. ✅ **Schema Validation**: Conforms to Pydantic model
2. ✅ **Required Fields**: All required fields present
3. ✅ **Data Types**: Correct types for all fields
4. ✅ **Value Ranges**: Within acceptable ranges
5. ✅ **Enum Values**: Valid enum selections
6. ✅ **Data Freshness**: Within freshness threshold
7. ✅ **Risk Assessment**: Standardized 0-5 scale
8. ✅ **Citations**: All sources cited
9. ✅ **Completeness**: No missing critical data
10. ✅ **Consistency**: Internally consistent data

## Rejection Documentation

When rejecting data/recommendations:

1. **Specific Reason**: Clear rejection reason
2. **Quantitative Evidence**: Numerical backing
3. **Threshold Violated**: Which threshold failed
4. **Alternative Suggestions**: Improvements needed
5. **Audit Trail**: Log all rejections

---

**Version**: 2.0  
**Last Updated**: 2025-03-10
