---
inclusion: always
---


# FinWiz Product Requirements

## Core Mission
AI-powered financial research platform using autonomous CrewAI agents to analyze cryptocurrencies, stocks, and ETFs with actionable investment recommendations.

## Analysis Requirements

### Asset Coverage
- **Cryptocurrencies**: Technical analysis, volatility patterns, regulatory risks
- **Stocks**: Fundamental analysis (10-K filings), technical indicators, sector comparisons  
- **ETFs**: Expense ratios, tracking error, holdings diversification

### Output Standards
- **Recommendations**: Clear BUY/HOLD/SELL with rationale and time horizon
- **Risk Assessment**: Standardized 1-10 scale with systematic vs idiosyncratic risks
- **Data Sources**: Always cite sources with as-of dates
- **Report Format**: HTML with PDF conversion, multi-language support (French default)

### Quality Requirements
- Real-time market data integration
- Multiple data provider validation
- Professional financial terminology
- Regulatory compliance considerations
- Portfolio context and diversification analysis

## User Experience
- Autonomous agent execution with minimal user input
- Structured output with strict schema validation
- Comprehensive reports with charts and visualizations
- Portfolio review with keep/sell recommendations and alternatives

## Technical Constraints
- Asynchronous execution for performance
- Modular architecture for extensibility
- YAML-based configuration for agent behavior
- Strict Pydantic validation for all outputs