# API Reference

Complete API documentation for FinWiz financial analysis platform.

## Quick Navigation

- [Crew APIs](api/crews.md) - AI agent crews for analysis
- [Tool APIs](api/tools.md) - Financial analysis tools
- [Schema APIs](api/schemas.md) - Data models and validation

## Analysis Crews

FinWiz provides specialized crews for different asset types:

### Stock Analysis

- **StockCrew** - Fundamental and technical stock analysis
- See [Stock Crew API](api/crews.md#stock-crew) for details

### ETF Analysis

- **ETFCrew** - Exchange-traded fund analysis
- See [ETF Crew API](api/crews.md#etf-crew) for details

### Cryptocurrency Analysis

- **CryptoCrew** - Cryptocurrency and digital asset analysis
- See [Crypto Crew API](api/crews.md#crypto-crew) for details

### Portfolio Analysis

- `PortfolioReviewCrew` does not exist. Portfolio holdings analysis and
  recommendations are handled by `ValidationOrchestrator` (Python, not a
  crew) — see `orchestrators/validation_orchestrator.py`.
- **PortfolioRebalancingCrew** - Portfolio optimization and rebalancing
- See [Portfolio Crews](api/crews.md) for details

### Discovery

- **InvestmentDiscoveryCrew** - A+ investment opportunity discovery
- See [Discovery Crew API](api/crews.md) for details

## Tool Reference

Essential tools for financial analysis:

- **Market Data Tools** - Real-time and historical market data
- **Sentiment Analysis** - News and social media sentiment
- **Quantitative Analysis** - Technical indicators and metrics
- **Backtesting** - Strategy testing and validation
- **Risk Assessment** - Portfolio risk analysis

See [Tool APIs](api/tools.md) for complete documentation.

## Schema Reference

Pydantic data models for type-safe analysis:

- **CrewExportSchemas** - Output schemas for each crew
- **PortfolioSchemas** - Portfolio structure and holdings
- **AnalysisSchemas** - Analysis results and recommendations
- **ValidationSchemas** - Data validation models

See [Schema APIs](api/schemas.md) for complete documentation.

## Flow Reference

CrewAI Flow orchestration:

- **FinwizFlow** - Main workflow orchestration
- **State Management** - Pydantic-based flow state
- **Flow Listeners** - Event-driven workflow steps

## Getting Started

New to the FinWiz API? Check out these resources:

- [Operations Guide](../how-to/OPERATIONS_GUIDE.md) - Deployment and operations
- [Developer Guide](../development/DEVELOPER_GUIDE.md) - Development guide
- [Tutorials](../tutorials/index.md) - Step-by-step tutorials

## API Examples

### Running Stock Analysis

`finwiz/crews/stock_crew/` has no `__init__.py` and re-exports nothing —
import from the submodule:

```python
from finwiz.crews.stock_crew.stock_crew import StockCrew

crew = StockCrew()
result = crew.crew().kickoff(inputs={"ticker": "AAPL"})
print(result.raw)
```

### Portfolio Review

There is no `finwiz/flows/flow_orchestrator.py` — `FinwizFlow` is defined in
`finwiz/flows/orchestrator.py`:

```python
from finwiz.flows.orchestrator import FinwizFlow

flow = FinwizFlow()
result = flow.kickoff()
```
