# Schemas Module

This directory contains all Pydantic data models for the FinWiz platform. Every data structure used for validation, serialization, and API contracts is defined here.

## Directory Structure

```
schemas/
├── api/                   # API request/response models
│   └── models.py
├── hybrid_analysis/       # Hybrid Python/AI analysis schemas
│   ├── enriched.py        # Enriched analysis results
│   ├── metadata.py        # Analysis metadata
│   ├── qualitative.py     # AI-generated insights
│   └── quantitative.py    # Python-calculated metrics
├── integration/           # Data integration schemas
│   └── models.py
├── quantitative/          # Quantitative analysis schemas
│   ├── config_models.py   # Backtest, optimization configs
│   └── models.py          # Metrics, results
├── rebalancing/           # Portfolio rebalancing schemas
│   ├── analysis.py        # Analysis results
│   ├── core.py            # Core data structures
│   ├── enums.py           # Status enums
│   ├── results.py         # Rebalancing results
│   └── trades.py          # Trade recommendations
├── tools/                 # Tool input/output schemas
│   └── inputs.py
├── common.py              # Shared schemas (RiskAssessment, etc.)
├── crew_exports.py        # MAIN: Export schemas per crew
├── crypto.py              # Cryptocurrency schemas
├── etf.py                 # ETF schemas
├── stock.py               # Stock schemas
├── portfolio_review.py    # Portfolio review schemas
├── investment_discovery.py # A+ discovery schemas
├── report.py              # Report generation schemas
└── validation.py          # Validation utilities
```

## Major Entry Points

### Crew Export Schemas (PRIMARY)

| File | Class | Purpose |
|------|-------|---------|
| `crew_exports.py` | `StockCrewExport` | Stock crew output schema |
| `crew_exports.py` | `ETFCrewExport` | ETF crew output schema |
| `crew_exports.py` | `CryptoCrewExport` | Crypto crew output schema |
| `crew_exports.py` | `DiscoveryCrewExport` | Investment discovery output |
| `crew_exports.py` | `RebalancingCrewExport` | Rebalancing output |
| `crew_exports.py` | `DeepAnalysisExport` | Deep analysis output |

### Asset-Specific Schemas

| File | Class | Purpose |
|------|-------|---------|
| `stock.py` | `TenKInsight` | 10-K analysis insights |
| `stock.py` | `MarketSentiment` | Market sentiment data |
| `etf.py` | `ETFFactsheet` | ETF factsheet data |
| `etf.py` | `ETFTopHolding` | ETF holdings |
| `crypto.py` | `CryptoThesis` | Crypto investment thesis |
| `crypto.py` | `OnChainMetrics` | Blockchain metrics |

### Common Schemas

| File | Class | Purpose |
|------|-------|---------|
| `common.py` | `RiskAssessmentStandardized` | Risk assessment (all assets) |
| `common.py` | `PriceTarget` | Price targets |
| `common.py` | `TechnicalIndicators` | Technical analysis data |
| `portfolio_review.py` | `Grade` | Letter grade (A+ to F) |
| `portfolio_review.py` | `PortfolioHolding` | Single holding data |
| `portfolio_review.py` | `PortfolioReview` | Complete portfolio review |

### Quantitative Schemas

| File | Class | Purpose |
|------|-------|---------|
| `quantitative/config_models.py` | `BacktestConfig` | Backtest configuration |
| `quantitative/config_models.py` | `OptimizationConfig` | Optimization settings |
| `quantitative/models.py` | `PerformanceMetrics` | Performance calculations |
| `quantitative/models.py` | `RiskMetrics` | Risk calculations |

### Rebalancing Schemas

| File | Class | Purpose |
|------|-------|---------|
| `rebalancing/core.py` | `AllocationTarget` | Target allocations |
| `rebalancing/trades.py` | `TradeRecommendation` | Trade recommendations |
| `rebalancing/results.py` | `RebalancingResult` | Complete rebalancing output |

## Schema Design Rules

1. **Strict Validation**: All schemas use `extra='forbid'`
2. **Location**: ALL Pydantic models go in `schemas/`, not domain folders
3. **Field Constraints**: Use `Field()` with validation
4. **JSON Serialization**: Support `model_dump_json()` with `default=str`

## Base Schema Pattern

```python
from pydantic import BaseModel, Field
from typing import Literal

class CrewExportBase(BaseModel):
    """Base schema for all crew exports."""

    model_config = {"extra": "forbid", "str_strip_whitespace": True}

    crew_name: str = Field(..., description="Crew that generated this")
    ticker: str = Field(..., description="Asset ticker symbol")
    asset_class: Literal["stock", "etf", "crypto"] = Field(...)
    session_id: str = Field(..., description="Flow session ID")
```

## Using Schemas

### For Crew Output

```python
from finwiz.schemas.crew_exports import StockCrewExport

# Create validated export
export = StockCrewExport(
    ticker="AAPL",
    session_id="abc123",
    composite_score=0.85,
    grade="A",
    recommendation="BUY",
    # ... other fields
)

# Save to JSON
export_path = f"output/reports/{session_id}/stock/{ticker}_export.json"
with open(export_path, 'w') as f:
    f.write(export.model_dump_json(indent=2))
```

### For Task Output

```yaml
# In tasks.yaml
analysis_task:
  output_pydantic: "TenKInsight"
  output_json: true
```

### For Validation

```python
from pydantic import ValidationError
from finwiz.schemas.stock import TenKInsight

try:
    insight = TenKInsight(**data)
except ValidationError as e:
    logger.error(f"Validation failed: {e}")
```

## JSON Serialization

Always use `default=str` for complex types:

```python
# Pydantic (preferred)
json_str = model.model_dump_json(indent=2)

# Manual (fallback)
import json
json_str = json.dumps(data, default=str, indent=2)
```

## Testing

```bash
# Test all schemas
uv run pytest tests/unit/schemas/ -v

# Test specific schema
uv run pytest tests/unit/schemas/test_crew_exports.py -v

# Type checking
uv run mypy src/finwiz/schemas/
```

## Related Modules

- `finwiz.crews` - Uses export schemas for output
- `finwiz.validation` - Runtime validation logic
- `finwiz.reporting` - Uses schemas for report generation
- `finwiz.flow_state` - Flow state models
