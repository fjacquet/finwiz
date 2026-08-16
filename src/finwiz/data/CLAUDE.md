# Data Module

This directory contains the data acquisition layer for fetching financial data from multiple external sources.

## Directory Structure

```
data/
├── adapters/                      # Data source adapters
│   ├── base_adapter.py            # Base adapter interface + FundamentalData
│   ├── yfinance_adapter.py        # Yahoo Finance (PRIMARY)
│   ├── alpha_vantage_adapter.py   # Alpha Vantage
│   ├── tiingo_adapter.py          # Tiingo
│   ├── eod_adapter.py             # EOD Historical Data
│   ├── economic_calendar_adapter.py
│   ├── fear_greed_adapter.py
│   ├── finnhub_news_adapter.py
│   ├── fred_adapter.py
│   └── industry_averages.py       # Industry benchmark data
│
├── __init__.py
├── data_source_orchestrator.py    # MAIN: Multi-source orchestration
├── exceptions.py                  # Data-specific exceptions
├── fx_rates.py                    # Currency conversion
├── news_utils.py                  # News fetch/normalize helpers
└── sentiment_collector.py         # Sentiment aggregation
```

## Major Entry Points

| File | Class/Function | Purpose |
|------|---------------|---------|
| `data_source_orchestrator.py` | `DataSourceOrchestrator` | Coordinate multiple data sources |
| `data_source_orchestrator.py` | `async get_fundamental_data()` | Waterfall fetch with fallback |
| `adapters/yfinance_adapter.py` | `YFinanceAdapter` | Yahoo Finance data |
| `adapters/alpha_vantage_adapter.py` | `AlphaVantageAdapter` | Alpha Vantage data |
| `adapters/base_adapter.py` | `BaseDataAdapter` | Abstract adapter interface |
| `adapters/base_adapter.py` | `FundamentalData` | Standardized per-source result |

## Data Source Priority

```
1. Yahoo Finance (FREE, PRIMARY)
   └── Historical prices, fundamentals, info

2. Alpha Vantage (API KEY required)
   └── Intraday, earnings, news

3. Tiingo (API KEY required)
   └── End-of-day, IEX real-time

4. EOD Historical Data (API KEY required)
   └── Global exchanges, splits, dividends
```

## Usage

### DataSourceOrchestrator

The orchestrator API is **async** and returns dataclasses, not dicts.

```python
from finwiz.data.data_source_orchestrator import DataSourceOrchestrator

orchestrator = DataSourceOrchestrator()

# Waterfall fetch across sources, with fallback
result = await orchestrator.get_fundamental_data(ticker="AAPL", sector="Technology")

# OrchestrationResult fields
print(result.return_on_equity)
print(result.debt_to_equity)
print(result.revenue_growth)
print(result.profit_margin)

# Provenance
print(result.confidence)          # 0.0-1.0
print(result.sources_attempted)   # e.g. ["yfinance", "alpha_vantage"]
print(result.lineage.to_dict())   # which source supplied which field
print(result.is_complete())
print(result.get_completeness_score())

# Introspection
orchestrator.get_available_adapters()
orchestrator.get_adapter_info()
```

### Individual Adapters

```python
from finwiz.data.adapters.yfinance_adapter import YFinanceAdapter

adapter = YFinanceAdapter()

if adapter.is_available():
    data = await adapter.get_fundamental_data("AAPL")   # -> FundamentalData
    print(adapter.source_name, data.confidence, data.return_on_equity)
```

## Adapter Interface

All adapters implement `BaseDataAdapter` — three abstract members, one of them
async:

```python
class BaseDataAdapter(ABC):
    """Base interface for all data adapters."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Name of this data source."""

    @abstractmethod
    async def get_fundamental_data(self, ticker: str) -> FundamentalData:
        """Get fundamental data for a ticker."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this data source is currently available."""
```

`FundamentalData` (a dataclass, `base_adapter.py:28`) carries `ticker`,
`source`, `timestamp`, `confidence`, the four core metrics
(`return_on_equity`, `debt_to_equity`, `revenue_growth`, `profit_margin`),
plus `raw_data` and `warnings`. Confidence outside `0.0-1.0` raises
`InvalidDataError` at construction.

## Fallback Strategy

Handled internally, not by a public method. `get_fundamental_data()` runs
`_orchestrate_data_acquisition()` under a total timeout; if that leaves fields
missing it calls `_apply_fallback()` (`data_source_orchestrator.py:239`), which
fills only the still-`None` fields from industry averages for the sector.

A fallback fill is never silent. It sets `used_fallback`, appends
`"IndustryAverages"` to `sources_attempted` / `sources_succeeded`, and adds the
warning `"Used industry averages for missing fields"`. Confidence is then
scaled by provenance (`_calculate_confidence`, :261):

| Source that succeeded | Confidence |
|---|---|
| YFinance | 0.95 × completeness |
| AlphaVantage | 0.85 × completeness |
| Tiingo / EOD | 0.75 × completeness |
| industry-average fallback | 0.50 × completeness |
| nothing | 0.30 × completeness |

## Environment Variables

```bash
# Optional API keys (Yahoo Finance works without)
ALPHA_VANTAGE_API_KEY=your_key
TIINGO_API_KEY=your_key
EOD_API_KEY=your_key

# Performance settings
ENABLE_ALPHA_VANTAGE=false  # Read by config/batch_prefetch_config.py:141
```

## Testing

```bash
# Test data adapters
uv run pytest tests/unit/data/ -v

# Per-adapter tests
uv run pytest tests/unit/data/adapters/ -v

# Integration tests (requires API keys)
uv run pytest tests/integration/test_data_source_orchestrator.py -v -m integration
```

## Related Modules

- `finwiz.integration` - Data integration layer
- `finwiz.tools` - Tools using data adapters
- `finwiz.integration.batch_data_prefetcher` - Batch data fetching
