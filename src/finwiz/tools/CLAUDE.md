# Tools Module

This directory contains all custom CrewAI tools for financial data retrieval, analysis, and processing. Tools are the primary way agents interact with external data sources and perform calculations.

## Directory Structure

```
tools/
├── analysis/              # Analysis coordination tools
│   ├── analysis_coordinator.py
│   └── holding_processors.py
├── charts/                # Chart generation tools
│   ├── chart_analysis.py
│   └── chart_generator.py
├── etf/                   # ETF-specific tools
│   ├── etf_analyzers.py
│   └── etf_data_fetchers.py
├── rebalancing/           # Rebalancing report tools
│   ├── css_*.py           # Styling components
│   ├── template_*.py      # Template builders
│   └── rebalancing_html_builders.py
├── reporting/             # Report generation tools
│   ├── report_formatters.py
│   └── report_sections.py
├── scoring/               # Python scoring algorithms
│   ├── scoring_algorithms.py
│   └── scoring_criteria.py
├── sentiment/             # Sentiment analysis tools
│   ├── sentiment_aggregators.py
│   └── sentiment_calculators.py
├── twelve_data/           # TwelveData API integration
│   ├── transformers.py
│   └── validators.py
├── tool_factories.py      # MAIN: Centralized tool initialization
├── finance_tools.py       # Core financial data tools
├── quantitative_analysis_tool.py  # Quantitative metrics
├── rag_tools.py           # RAG knowledge tools
├── valuation_tool.py      # DCF, P/E valuation
└── [many more specialized tools]
```

## Major Entry Points

### Tool Factories (PRIMARY)

| File | Function | Purpose |
|------|----------|---------|
| `tool_factories.py` | `get_stock_crew_tools()` | Tools for stock analysis crews |
| `tool_factories.py` | `get_etf_crew_tools()` | Tools for ETF analysis crews |
| `tool_factories.py` | `get_crypto_crew_tools()` | Tools for crypto analysis crews |
| `tool_factories.py` | `get_discovery_crew_tools()` | Tools for investment discovery |
| `tool_factories.py` | `get_deep_analysis_tools()` | Tools for deep per-holding analysis |

### Core Research Tools

| File | Function | Purpose |
|------|----------|---------|
| `finance_tools.py` | `get_stock_research_tools()` | Yahoo Finance, SEC, news tools |
| `finance_tools.py` | `get_etf_research_tools()` | ETF holdings, expense analysis |
| `finance_tools.py` | `get_crypto_research_tools()` | CoinMarketCap, on-chain metrics |

### Quantitative Tools

| File | Class | Purpose |
|------|-------|---------|
| `quantitative_analysis_tool.py` | `QuantitativeAnalysisTool` | Backtrader, TA-Lib integration |
| `valuation_tool.py` | `ValuationTool` | DCF, P/E, technical targets |
| `backtesting_tool.py` | `BacktestingTool` | Strategy backtesting |
| `optimization_tool.py` | `OptimizationTool` | Portfolio optimization |

### Data Source Tools

| File | Class | Purpose |
|------|-------|---------|
| `yahoo_finance_tool.py` | `YahooFinanceTool` | Primary market data |
| `alpha_vantage_tool.py` | `AlphaVantageTool` | Fundamental data |
| `twelve_data_tool.py` | `TwelveDataTool` | Real-time quotes |
| `sec_tool.py` | `SECTool` | SEC filings (10-K, 10-Q) |
| `coinmarketcap_tool.py` | `CoinMarketCapTool` | Crypto market data |
| `kraken_api_tool.py` | `KrakenAPITool` | Crypto trading data |

### RAG and Knowledge Tools

| File | Function | Purpose |
|------|----------|---------|
| `rag_tools.py` | `get_rag_tools()` | RAG query and save tools |
| `save_to_rag_tool.py` | `SaveToRagTool` | Save to vector DB |
| `perplexity_search_tool.py` | `PerplexitySearchTool` | AI-powered research |

## Tool Factory Pattern

Always use factories to get tools, never instantiate directly:

```python
from finwiz.tools.tool_factories import get_stock_crew_tools

# Get standardized tool set
tools = get_stock_crew_tools(
    include_rag=True,
    include_quantitative=True,
    include_valuation=True,
    collection_suffix="stock",
    prefetched_data=None  # or dict for batch mode
)
```

## Creating a Custom Tool

```python
from crewai.tools import BaseTool
from pydantic import Field

class MyCustomTool(BaseTool):
    name: str = "my_custom_tool"
    description: str = "Description for the AI agent"

    # Input schema
    ticker: str = Field(..., description="Stock ticker symbol")

    def _run(self, ticker: str) -> str:
        # Tool implementation
        result = fetch_data(ticker)
        return json.dumps(result, default=str)
```

## Tool Best Practices

1. **Return JSON**: Always return `json.dumps(data, default=str)`
2. **Handle Errors**: Wrap in try/except, return error messages
3. **Rate Limiting**: Use `max_rpm` in agent config
4. **Caching**: Use `@cache_result` decorator for expensive calls
5. **Validation**: Validate inputs with Pydantic

## Tool Input/Output Validation

```python
from finwiz.tools.tool_input_validator import validate_tool_input
from finwiz.tools.tool_result import ToolResult

class SafeTool(BaseTool):
    def _run(self, **kwargs) -> str:
        # Validate input
        validated = validate_tool_input(self.input_schema, kwargs)

        # Execute
        result = self.execute(validated)

        # Return standardized result
        return ToolResult(
            success=True,
            data=result
        ).to_json()
```

## Batch Mode Support

For high-performance batch processing:

```python
def get_stock_crew_tools(
    prefetched_data: dict | None = None,  # Pre-fetched data for batch mode
) -> list[BaseTool]:
    if prefetched_data:
        # Use pre-fetched data (10-20x faster)
        return get_batch_mode_tools(prefetched_data)
    else:
        # Use live API calls (single ticker mode)
        return get_live_mode_tools()
```

## Testing

```bash
# Test tool factories
uv run pytest tests/unit/tools/test_tool_factories.py -v

# Test specific tool
uv run pytest tests/unit/tools/test_yahoo_finance_tool.py -v

# Test all tools
uv run pytest tests/unit/tools/ -v
```

## Related Modules

- `finwiz.data.adapters` - Data source adapters
- `finwiz.quantitative` - Quantitative analysis library
- `finwiz.integration` - Data integration layer
- `finwiz.schemas.tools.inputs` - Tool input schemas
