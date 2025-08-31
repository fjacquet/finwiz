# FinWiz Data Schemas (Pydantic v2)

This folder hosts JSON Schemas exported from Pydantic models in `src/finwiz/schemas/`.

## Core Schemas

### Reporter & Flow Contracts
- **`ReporterInput`**: Aggregate input for the final tool-less reporter
- **`RiskAssessmentStandardized`**: Standardized 0-5 risk scoring across all asset classes

### Asset-Specific Contracts
- **Stock Analysis**: `TenKInsight`, `MarketSentiment`
- **ETF Analysis**: `ETFFactsheet`, `ETFTopHolding`
- **Crypto Analysis**: `CryptoThesis`

### Standardized Analysis Tools

The project includes standardized analysis tools that provide consistent output formats across asset classes:

- **`StandardizedSentimentAnalysisTool`**: Provides comprehensive sentiment analysis with weighted scoring, trending topics, and confidence intervals. Output includes mean_score, weighted_score, confidence_interval, counts, top_pos/top_neg articles, and trending_topics.
- **`CrossAssetSentimentComparatorTool`**: Enables comparative sentiment analysis across different asset classes.

These tools complement the existing schema-validated crew outputs and provide additional analytical capabilities with their own structured output formats.

### Validation & Portfolio
- **`ValidatedTicker`**: Ticker existence validation results
- **`PortfolioReview`**: Complete portfolio analysis with metadata and holdings list
- **`HoldingDecision`**: Individual holding analysis with keep/sell decision and rationale
- **`Alternative`**: Alternative investment suggestions with scoring and thesis

## Schema Export

Generate JSON schemas from Pydantic models:

```bash
uv run python -m finwiz.schemas.export
```

This writes `*.schema.json` files into this folder.

## Examples & Validation

Examples live under `docs/schemas/examples/`.

All schemas use strict Pydantic v2 models with `extra='forbid'` to prevent schema drift and ensure data contract compliance.

## Validation Infrastructure

FinWiz implements a centralized validation system with the following components:

- **ValidationManager**: Central orchestrator for all validation operations
- **SchemaRegistry**: Centralized registry for Pydantic models with automatic registration
- **ValidationResult**: Structured validation outcomes with detailed error context
- **ValidationMode**: Configurable strictness levels

### Validation Modes

Configure validation strictness via `VALIDATION_STRICTNESS` environment variable:
- `off`: No validation (development only)
- `warn`: Log validation errors but continue (default)
- `error`: Fail on validation errors (production)

### Usage

```python
from finwiz.validation import get_validation_manager

manager = get_validation_manager()
result = manager.validate_crew_output(data, "stock", "analysis")

if result.is_valid:
    clean_data = result.sanitized_data
else:
    for error in result.errors:
        print(f"Error at {error.field_path}: {error.message}")
```

See `docs/validation_system.md` for complete documentation.

These schemas implement change requests CR-2025-08-09-01, CR-2025-08-09-02, CR-2025-08-09-03, and CR-2025-08-10-01.
