# Data Module

This directory contains the data acquisition layer for fetching financial data from multiple external sources.

## Directory Structure

```
data/
├── adapters/                    # Data source adapters
│   ├── base_adapter.py          # Base adapter interface
│   ├── yfinance_adapter.py      # Yahoo Finance (PRIMARY)
│   ├── alpha_vantage_adapter.py # Alpha Vantage
│   ├── tiingo_adapter.py        # Tiingo
│   ├── eod_adapter.py           # EOD Historical Data
│   ├── intrinio_adapter.py      # Intrinio
│   ├── industry_averages.py     # Industry benchmark data
│   └── yfinance_adapter_old.py  # Legacy adapter (deprecated)
│
├── __init__.py
├── data_source_orchestrator.py  # MAIN: Multi-source orchestration
└── exceptions.py                # Data-specific exceptions
```

## Major Entry Points

| File | Class/Function | Purpose |
|------|---------------|---------|
| `data_source_orchestrator.py` | `DataSourceOrchestrator` | Coordinate multiple data sources |
| `data_source_orchestrator.py` | `fetch_comprehensive_data()` | Get data with fallbacks |
| `adapters/yfinance_adapter.py` | `YFinanceAdapter` | Yahoo Finance data |
| `adapters/alpha_vantage_adapter.py` | `AlphaVantageAdapter` | Alpha Vantage data |
| `adapters/base_adapter.py` | `BaseDataAdapter` | Abstract adapter interface |

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

5. Intrinio (API KEY required)
   └── SEC filings, fundamentals
```

## Usage

### DataSourceOrchestrator

```python
from finwiz.data.data_source_orchestrator import DataSourceOrchestrator

orchestrator = DataSourceOrchestrator()

# Fetch with automatic fallback
data = orchestrator.fetch_comprehensive_data(
    ticker="AAPL",
    include_history=True,
    include_fundamentals=True,
    include_news=True
)

# Access data
print(data["history"])      # Price history
print(data["fundamentals"]) # Key metrics
print(data["info"])         # Company info
```

### Individual Adapters

```python
from finwiz.data.adapters.yfinance_adapter import YFinanceAdapter

adapter = YFinanceAdapter()

# Get historical data
history = adapter.get_history(
    ticker="AAPL",
    period="1y",
    interval="1d"
)

# Get fundamentals
fundamentals = adapter.get_fundamentals("AAPL")

# Get company info
info = adapter.get_info("AAPL")
```

## Adapter Interface

All adapters implement `BaseDataAdapter`:

```python
from abc import ABC, abstractmethod

class BaseDataAdapter(ABC):
    """Base interface for all data adapters."""

    @abstractmethod
    def get_history(
        self,
        ticker: str,
        period: str = "1y",
        interval: str = "1d"
    ) -> pd.DataFrame:
        """Get historical price data."""
        pass

    @abstractmethod
    def get_fundamentals(self, ticker: str) -> dict:
        """Get fundamental metrics."""
        pass

    @abstractmethod
    def get_info(self, ticker: str) -> dict:
        """Get company/asset information."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if data source is available."""
        pass
```

## Fallback Strategy

```python
# In DataSourceOrchestrator
def fetch_with_fallback(self, ticker: str, method: str) -> dict:
    """Fetch data with automatic fallback to secondary sources."""

    # Try sources in priority order
    for adapter in self.adapters:
        try:
            if adapter.is_available():
                return getattr(adapter, method)(ticker)
        except Exception as e:
            self.logger.warning(f"{adapter.name} failed: {e}")
            continue

    raise DataUnavailableError(f"All sources failed for {ticker}")
```

## Environment Variables

```bash
# Optional API keys (Yahoo Finance works without)
ALPHA_VANTAGE_API_KEY=your_key
TIINGO_API_KEY=your_key
EOD_API_KEY=your_key
INTRINIO_API_KEY=your_key

# Performance settings
ENABLE_ALPHA_VANTAGE=false  # Disable if not needed
DATA_CACHE_TTL=3600         # Cache TTL in seconds
```

## Testing

```bash
# Test data adapters
uv run pytest tests/unit/data/ -v

# Test with mocked APIs
uv run pytest tests/unit/data/test_adapters.py -v

# Integration tests (requires API keys)
uv run pytest tests/integration/data/ -v -m integration
```

## Related Modules

- `finwiz.integration` - Data integration layer
- `finwiz.tools` - Tools using data adapters
- `finwiz.utils.batch_data_prefetcher` - Batch data fetching
