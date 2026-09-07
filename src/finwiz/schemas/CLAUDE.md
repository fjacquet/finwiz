# Schemas Module

This directory contains all Pydantic data models for the FinWiz platform. Every data structure used for validation, serialization, and API contracts is defined here.

## Directory Structure

```
schemas/
├── hybrid_analysis/           # Hybrid Python/AI analysis schemas
│   ├── collected.py           # Raw collected inputs
│   ├── enriched.py            # Enriched analysis results
│   ├── fact_pack.py           # Researched fact pack
│   ├── metadata.py            # Analysis metadata
│   ├── qualitative.py         # AI-generated insights
│   ├── quantitative.py        # Python-calculated metrics
│   └── strategic.py           # AI-rated strategic frameworks
├── integration/               # Data integration schemas
│   └── models.py
├── quantitative/              # Quantitative analysis schemas
│   ├── backtesting.py         # Backtest result schemas
│   ├── config_models.py       # Backtest, optimization configs
│   ├── data.py                # Data loading schemas
│   ├── enums.py               # Quantitative enums
│   ├── models.py              # Metrics, results
│   ├── portfolio.py           # Portfolio optimization schemas
│   ├── risk.py                # Risk calculation schemas
│   ├── screening.py           # Screening result schemas
│   └── technical.py           # Technical analysis schemas
├── rebalancing/               # Portfolio rebalancing schemas
│   ├── analysis.py            # Analysis results
│   ├── core.py                # Core data structures
│   ├── enums.py               # Status enums
│   ├── results.py             # Rebalancing results
│   └── trades.py              # Trade recommendations
├── tools/                     # Tool input/output schemas
│   └── inputs.py
│
├── # Root-level schemas
├── common.py                  # Shared schemas (RiskAssessment, etc.)
├── crew_exports.py            # MAIN: Export schemas per crew
├── crypto.py                  # Cryptocurrency schemas
├── economic_calendar.py       # Economic event schemas
├── etf.py                     # ETF schemas
├── export.py                  # Export configuration schemas
├── integration_models.py      # Integration data models (incl. DataSource)
├── investment_discovery.py    # A+ discovery schemas
├── legacy_compat.py           # Backward compatibility schemas
├── macro.py                   # Macro context schemas
├── migration.py               # Schema migration utilities
├── newcomer_discovery.py      # NewcomerCandidate, PortfolioGapProfile
├── perplexity.py              # Perplexity API schemas
├── portfolio_processing.py    # Portfolio processing schemas
├── portfolio_rebalancing.py   # Portfolio rebalancing schemas
├── portfolio_review.py        # Portfolio review schemas
├── portfolio_valuation.py     # Valuation schemas
├── python_analysis.py         # Python analysis result schemas
├── quantitative_crew.py       # Quantitative crew output schemas
├── report.py                  # Report generation schemas
├── run_ledger.py              # Per-run stage ledger records
├── sentiment.py               # Sentiment schemas
├── stage_contract.py          # Pipeline stage contract
├── stock.py                   # Stock schemas
├── stress_test.py             # Stress-scenario schemas
├── validate.py                # Validation helper functions
└── validation.py              # Validation utilities
```

There is no `schemas/api/`, `data_lineage.py`, `feedback.py`, or `session.py`.
`DataLineage` is a dataclass in `data/data_source_orchestrator.py`; `DataSource`
is a Pydantic model in `integration_models.py`.

## Major Entry Points

### Crew Export Schemas (PRIMARY)

`crew_exports.py` holds only `CrewExportBase` and `DeepAnalysisCrewExport` now.
The per-crew export schemas (`StockCrewExport`, `ETFCrewExport`,
`CryptoCrewExport`, `DiscoveryCrewExport`, `RebalancingCrewExport`,
`DiscoveryOpportunity`) and `ConsolidatedReportExport` were deleted: none had
a consumer outside their own schema test, because the six crews that would
have produced them were removed (see #187).

| File | Class | Purpose |
|------|-------|---------|
| `crew_exports.py` | `CrewExportBase` | Shared base fields for crew exports |
| `crew_exports.py` | `DeepAnalysisCrewExport` | Deep analysis output |

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

### Run & Data Management

| File | Class | Purpose |
|------|-------|---------|
| `run_ledger.py` | run-ledger records | Per-stage JSONL run record |
| `integration_models.py` | `DataSource` | Data source metadata |
| `migration.py` | `migrate_portfolio_review_if_needed()` | Schema migration utility |

Data provenance for a fetch is carried by `DataLineage`, a dataclass in
`data/data_source_orchestrator.py` — not a schema in this package.

### Integration & API Schemas

| File | Class | Purpose |
|------|-------|---------|
| `perplexity.py` | `PerplexitySearchRequest` | Perplexity API request |
| `perplexity.py` | `PerplexitySearchResponse` | Perplexity API response |
| `integration_models.py` | Data integration models | Integration data structures |
| `export.py` | Export configuration | Export settings |

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
from finwiz.schemas.crew_exports import DeepAnalysisCrewExport

# Create validated export
export = DeepAnalysisCrewExport(
    ticker="AAPL",
    session_id="abc123",
    composite_score=0.85,
    grade="A",
    recommendation="BUY",
    # ... other fields
)

# Save to JSON
export_path = f"output/reports/{session_id}/deep_analysis/{ticker}_export.json"
with open(export_path, "w") as f:
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
uv run pytest tests/unit/schemas/test_deep_analysis_result_schema.py -v

# Type checking
uv run mypy src/finwiz/schemas/
```

## Related Modules

- `finwiz.crews` - Uses export schemas for output
- `finwiz.validation` - Runtime validation logic
- `finwiz.reporting` - Uses schemas for report generation
- `finwiz.flow_state` - Flow state models
