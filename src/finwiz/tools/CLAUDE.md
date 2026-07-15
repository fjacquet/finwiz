# Tools Module

Custom CrewAI tools for financial data retrieval, analysis, and processing. Tools are how agents interact with external data and perform calculations.

## Directory Structure

```
tools/
├── tool_factories.py                # MAIN: get_stock/etf/crypto/discovery_crew_tools()
├── finance_tools.py                 # Core research tool bundles
├── logger.py                        # get_logger() — project-wide logging
│
├── # Data source tools
├── (Yahoo Finance, Perplexity, ticker validation, Kraken, AlphaVantage news sentiment, ChartImg, and DeFi metrics tools now come from crewai-custom-tools — see "Centralized tools" below)
├── alpha_vantage_tool.py            # AlphaVantageTool (company overview; still local)
├── twelve_data_tool.py              # TwelveDataTool
├── sec_tool.py                      # SECTool (10-K, 10-Q filings)
│
├── # Analysis tools
├── quantitative_analysis_tool.py    # QuantitativeAnalysisTool
├── valuation_tool.py                # ValuationTool (DCF, P/E)
├── backtesting_tool.py              # BacktestingTool
├── optimization_tool.py             # OptimizationTool
├── risk_assessment_tool.py          # RiskAssessmentTool
├── portfolio_analysis_tool.py       # PortfolioAnalysisTool
├── market_screening_tool.py         # MarketScreeningTool
├── chart_analyzer.py                # Chart analysis
│
├── # Enhanced tools (per-asset specialization)
├── enhanced_crypto_tool.py          # EnhancedCryptoAnalysisTool
├── enhanced_etf_tool.py             # Enhanced ETF analysis
├── enhanced_sec_tool.py             # Enhanced SEC filing analysis
├── a_plus_scoring_tool.py           # A+ scoring
├── regulatory_compliance_tool.py    # Compliance checking
├── alternative_finder_tool.py       # Alternative investments
├── price_target_calculator.py       # Price targets
├── position_sizing_tool.py          # Position sizing
│
├── # Screening
├── screening_criteria.py            # ScreeningCriteria (A+ thresholds)
├── screening_utils.py               # Screening utilities
├── screening_ranking.py             # Ranking logic
│
├── # Infrastructure
├── tool_result.py                   # ToolResult class
├── run_helpers.py                   # json_ok()/json_error() — shared _run JSON envelopes
├── robust_tool_wrapper.py           # Error wrapping
├── base_tools.py                    # AsyncFeedbackTool base
├── crewai_retry_patch.py            # Retry patch
├── llm_retry.py                     # LLM retry logic
│
├── # Perplexity subsystem
├── perplexity_logging.py
├── perplexity_errors.py
├── perplexity_analysis_integration.py
├── perplexity_feature_utils.py
├── perplexity_performance.py
│
├── # Subdirectories
├── analysis/                        # Analysis coordination
│   ├── analysis_coordinator.py      # HoldingAnalyzerOrchestrator
│   └── holding_processors.py        # HoldingProcessor
├── charts/                          # Chart generation
├── etf/                             # ETF data fetchers
│   └── etf_data_fetchers.py         # ETFDataFetcher (9 methods)
├── reporting/                       # Report formatters
│   ├── report_formatters.py         # HTMLReportFormatter
│   └── report_sections.py
├── scoring/                         # Scoring helpers
│   ├── scoring_criteria.py          # assess_market_regime(), get_dynamic_criteria()
│   └── scoring_algorithms.py
└── twelve_data/                     # TwelveData helpers
    ├── transformers.py
    └── validators.py
```

## Entry Points

| File | Function/Class | Purpose |
|------|---------------|---------|
| `tool_factories.py` | `get_stock_crew_tools()` | Stock crew tool set |
| `tool_factories.py` | `get_etf_crew_tools()` | ETF crew tool set |
| `tool_factories.py` | `get_crypto_crew_tools()` | Crypto crew tool set |
| `tool_factories.py` | `get_discovery_crew_tools()` | Discovery crew tool set |
| `tool_factories.py` | `get_deep_analysis_tools()` | Deep analysis tool set |
| `logger.py` | `get_logger()` | Project-wide logger |
| `screening_criteria.py` | `ScreeningCriteria` | A+ thresholds for screening |

## Usage

Always use factories, never instantiate tools directly:

```python
from finwiz.tools.tool_factories import get_stock_crew_tools

tools = get_stock_crew_tools(include_quantitative=True)
```

Tool `_run` JSON envelopes should use `json_ok`/`json_error` from `run_helpers`; adopt opportunistically when touching older tools.

## Related Modules

- `finwiz.quantitative` — Quantitative analysis library
- `finwiz.integration` — Data integration layer
- `finwiz.schemas.tools.inputs` — Tool input schemas
- `finwiz.crews` — Crews that use these tools

## Centralized tools (crewai-custom-tools)

Generic tools come from the `crewai-custom-tools` package, pinned to a git tag
in `pyproject.toml`. To co-develop against the local checkout, add (do NOT
commit this):

```toml
[tool.uv.sources]
crewai-custom-tools = { path = "../crewai_custom_tools", editable = true }
```

then `uv sync`. Remove the override and re-run `uv lock && uv sync` before
committing. Programmatic callers parse tool output with
`crewai_custom_tools.core.results.parse_tool_result()` — central tools return
the `{"success", "data", "error"}` JSON envelope, never bare dicts.
