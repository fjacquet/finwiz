# API Reference

Complete API documentation for FinWiz financial analysis platform.

## Quick Navigation

- [Crew APIs](api/crews.md) - AI agent crews for analysis
- [Tool APIs](api/tools.md) - Financial analysis tools
- [Schema APIs](api/schemas.md) - Data models and validation
- [Flow APIs](api/flows.md) - Workflow orchestration
- [CLI Commands](api/cli_commands.md) - Command-line interface
- [Configuration](api/configuration.md) - System configuration

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

- **PortfolioReviewCrew** - Portfolio holdings analysis and recommendations
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

See [Flow APIs](api/flows.md) for complete documentation.

## Configuration Reference

System and crew configuration:

- **Environment Variables** - API keys and settings
- **Agent Configuration** - Agent behavior and parameters
- **Task Configuration** - Task definitions and dependencies
- **Tool Configuration** - Tool initialization and settings

See [Configuration Reference](configuration.md) for complete documentation.

## Getting Started

New to the FinWiz API? Check out these resources:

- [User Guide](../USER_GUIDE.md) - End-user documentation
- [Developer Guide](../DEVELOPER_GUIDE.md) - Development guide
- [Tutorials](../tutorials/index.md) - Step-by-step tutorials

## API Examples

### Running Stock Analysis

```python
from finwiz.crews.stock_crew import StockCrew

crew = StockCrew()
result = crew.crew().kickoff(inputs={"ticker": "AAPL"})
print(result.raw)
```

### Portfolio Review

```python
from finwiz.flows.flow_orchestrator import FinwizFlow

flow = FinwizFlow()
result = flow.kickoff()
```

## See Also

- [CLI Options](../reference/cli_options.md) - Command-line options
- [Environment Variables](../reference/environment_variables.md) - Configuration
- [Rate Limits](../reference/rate_limits.md) - API rate limiting
- [Error Reference](../reference/api_errors.md) - Error codes and handling
