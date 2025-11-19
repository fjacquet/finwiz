---
title: "Crews Reference"
description: "Complete reference for FinWiz CrewAI crews and their capabilities"
category: "reference"
tags:
  - "crews"
  - "crewai"
  - "api"
  - "reference"
date: "2025-10-26"
---

# Crews Reference

Complete reference documentation for FinWiz's CrewAI crews, including configuration, inputs, outputs, and usage examples.

## Overview

FinWiz uses CrewAI crews for autonomous financial analysis. Each crew specializes in analyzing specific asset classes or performing particular analysis tasks.

## Available Crews

### Stock Crew

Comprehensive analysis of individual stocks using fundamental and technical analysis.

**Location**: `src/finwiz/crews/stock_crew/stock_crew.py`

**Purpose**: Analyze individual stocks for investment recommendations

**Inputs**:

```python
{
    "ticker": "AAPL"  # Required: Stock ticker symbol
}
```

**Output Schema**: `TenKInsight`

**Example Usage**:

```python
from finwiz.crews.stock_crew.stock_crew import StockCrew

crew = StockCrew()
result = crew.crew().kickoff(inputs={"ticker": "AAPL"})

print(f"Recommendation: {result.recommendation}")
print(f"Grade: {result.grade}")
```

**Agents**:

- **Stock Analyst**: Performs fundamental analysis
- **Technical Analyst**: Conducts technical analysis
- **Risk Assessor**: Evaluates investment risks
- **Investment Reporter**: Consolidates findings

**Tools Used**:

- `YahooFinanceTickerInfoTool`
- `EnhancedSECAnalysisTool`
- `QuantitativeAnalysisTool`
- `StandardizedSentimentTool`
- `TickerValidationTool`

### ETF Crew

Specialized analysis of Exchange-Traded Funds (ETFs) including expense ratios, holdings, and tracking performance.

**Location**: `src/finwiz/crews/etf_crew/etf_crew.py`

**Purpose**: Analyze ETFs for investment suitability

**Inputs**:

```python
{
    "ticker": "SPY"  # Required: ETF ticker symbol
}
```

**Output Schema**: `ETFFactsheet`

**Example Usage**:

```python
from finwiz.crews.etf_crew.etf_crew import EtfCrew

crew = EtfCrew()
result = crew.crew().kickoff(inputs={"ticker": "SPY"})

print(f"Expense Ratio: {result.expense_ratio}")
print(f"Tracking Error: {result.tracking_error}")
```

**Agents**:

- **ETF Analyst**: Analyzes fund structure and holdings
- **Cost Analyst**: Evaluates fees and expenses
- **Performance Analyst**: Assesses tracking and returns
- **ETF Reporter**: Generates comprehensive report

**Tools Used**:

- `YahooFinanceTickerInfoTool`
- `EnhancedETFAnalysisTool`
- `QuantitativeAnalysisTool`
- `TickerValidationTool`

### Crypto Crew

Analysis of cryptocurrencies including market dynamics, technology assessment, and regulatory considerations.

**Location**: `src/finwiz/crews/crypto_crew/crypto_crew.py`

**Purpose**: Analyze cryptocurrencies for investment potential

**Inputs**:

```python
{
    "ticker": "BTC"  # Required: Crypto ticker symbol
}
```

**Output Schema**: `CryptoThesis`

**Example Usage**:

```python
from finwiz.crews.crypto_crew.crypto_crew import CryptoCrew

crew = CryptoCrew()
result = crew.crew().kickoff(inputs={"ticker": "BTC"})

print(f"Market Cap: {result.market_cap}")
print(f"Technology Score: {result.technology_score}")
```

**Agents**:

- **Crypto Analyst**: Analyzes blockchain and tokenomics
- **Market Analyst**: Evaluates market dynamics
- **Regulatory Analyst**: Assesses regulatory risks
- **Crypto Reporter**: Consolidates analysis

**Tools Used**:

- `CoinMarketCapTool`
- `EnhancedCryptoAnalysisTool`
- `QuantitativeAnalysisTool`
- `TickerValidationTool`

### Deep Analysis Crew

Unified crew for comprehensive analysis of any asset class with detailed grading and scoring.

**Location**: `src/finwiz/crews/deep_analysis/deep_analysis.py`

**Purpose**: Perform deep, comprehensive analysis for portfolio evaluation

**Inputs**:

```python
{
    "ticker": "AAPL",        # Required: Asset ticker
    "asset_class": "stock"   # Required: "stock", "etf", or "crypto"
}
```

**Output Schema**: `DeepAnalysisResult`

**Example Usage**:

```python
from finwiz.crews.deep_analysis.deep_analysis import DeepAnalysisCrew

crew = DeepAnalysisCrew()
result = crew.crew().kickoff(inputs={
    "ticker": "AAPL",
    "asset_class": "stock"
})

print(f"Grade: {result.grade}")
print(f"Composite Score: {result.composite_score}")
```

**Agents**:

- **Deep Analyst**: Performs comprehensive analysis
- **Risk Assessor**: Detailed risk evaluation
- **Grading Specialist**: Assigns grades and scores

**Dynamic Tool Routing**:

- **Stock**: SEC analysis, fundamental metrics
- **ETF**: Fund analysis, expense evaluation
- **Crypto**: Blockchain analysis, market metrics

### Report Crew

Consolidates analysis results from multiple crews into comprehensive reports.

**Location**: `src/finwiz/crews/report_crew/report_crew.py`

**Purpose**: Generate consolidated investment reports

**Inputs**:

```python
{
    "analysis_results": [...],  # Results from other crews
    "report_type": "portfolio"  # Type of report to generate
}
```

**Output Schema**: `ConsolidatedReport`

**Example Usage**:

```python
from finwiz.crews.report_crew.report_crew import ReportCrew

crew = ReportCrew()
result = crew.crew().kickoff(inputs={
    "analysis_results": analysis_data,
    "report_type": "portfolio"
})
```

**Agents**:

- **Report Analyst**: Consolidates findings
- **Investment Reporter**: Generates final report

**Tools Used**:

- No external tools (consolidation only)

## Crew Configuration

### Agent Configuration

All crews use YAML configuration files for agents:

```yaml
# config/agents.yaml
stock_analyst:
  role: "Senior Stock Analyst"
  goal: "Analyze stock fundamentals and provide investment recommendations"
  backstory: "Expert financial analyst with deep knowledge of equity markets"
```

### Task Configuration

Tasks are defined in YAML configuration:

```yaml
# config/tasks.yaml
stock_analysis_task:
  description: "Analyze stock with quantitative metrics and risk assessment"
  expected_output: "Structured analysis with risk assessment and technical indicators"
  output_pydantic: "TenKInsight"
  output_json: true
  agent: stock_analyst
  async_execution: true
```

### Crew Settings

Standard crew configuration:

```python
@crew
def crew(self) -> Crew:
    return Crew(
        agents=self.agents,
        tasks=self.tasks,
        process=Process.sequential,
        verbose=True,
        respect_context_window=True,
        max_rpm=20  # Rate limiting
    )
```

## Performance Optimizations

### Async Execution

Enable async execution for I/O-bound tasks:

```yaml
task_name:
  async_execution: true  # Enable for data fetching tasks
```

### Rate Limiting

Configure rate limits to prevent API throttling:

```python
max_rpm=20  # Maximum 20 requests per minute
```

### Tool Optimization

Use minimal tool sets for specific use cases:

```python
# Minimal tools for risk assessment
tools = [
    QuantitativeAnalysisTool(asset_class=asset_class),
    TickerValidationTool(),
    asset_specific_tool
]
```

## Error Handling

### Graceful Degradation

Crews handle failures gracefully:

```python
try:
    result = crew.crew().kickoff(inputs=inputs)
except Exception as e:
    logger.error(f"Crew execution failed: {e}")
    # Fall back to baseline analysis
    result = baseline_analysis(inputs)
```

### Retry Logic

Automatic retry with exponential backoff:

```python
max_retries = 3
retry_delay = 2  # seconds
```

### Validation

All outputs are validated against Pydantic schemas:

```python
# Automatic validation
result = TenKInsight.model_validate(crew_output)
```

## Best Practices

### Crew Selection

Choose the appropriate crew for your use case:

- **Single asset analysis**: Use asset-specific crews (Stock, ETF, Crypto)
- **Portfolio evaluation**: Use Deep Analysis Crew
- **Comparative analysis**: Use multiple asset-specific crews
- **Report generation**: Use Report Crew for consolidation

### Input Validation

Always validate inputs before crew execution:

```python
# Validate ticker format
if not re.match(r'^[A-Z]{1,5}$', ticker):
    raise ValueError(f"Invalid ticker format: {ticker}")

# Validate asset class
if asset_class not in ['stock', 'etf', 'crypto']:
    raise ValueError(f"Invalid asset class: {asset_class}")
```

### Output Processing

Process crew outputs consistently:

```python
# Check for successful execution
if hasattr(result, 'error'):
    logger.error(f"Crew execution failed: {result.error}")
    return None

# Validate output schema
try:
    validated_result = OutputSchema.model_validate(result)
except ValidationError as e:
    logger.error(f"Output validation failed: {e}")
    return None
```

## Monitoring and Debugging

### Logging

Enable verbose logging for debugging:

```python
crew = Crew(
    agents=self.agents,
    tasks=self.tasks,
    verbose=True  # Enable detailed logging
)
```

### Performance Metrics

Track crew execution metrics:

```python
import time

start_time = time.time()
result = crew.crew().kickoff(inputs=inputs)
execution_time = time.time() - start_time

logger.info(f"Crew execution completed in {execution_time:.2f} seconds")
```

### Memory Usage

Monitor memory usage during execution:

```python
import psutil

process = psutil.Process()
memory_before = process.memory_info().rss / 1024 / 1024  # MB
result = crew.crew().kickoff(inputs=inputs)
memory_after = process.memory_info().rss / 1024 / 1024  # MB

logger.info(f"Memory usage: {memory_after - memory_before:.2f} MB")
```

## Integration Examples

### Flow Integration

Use crews within CrewAI Flows:

```python
from crewai.flow import Flow, start, listen

class AnalysisFlow(Flow):
    @start()
    def analyze_stock(self):
        crew = StockCrew()
        result = crew.crew().kickoff(inputs={"ticker": "AAPL"})
        return {"stock_analysis": result}
    
    @listen("analyze_stock")
    def generate_report(self, stock_data):
        crew = ReportCrew()
        result = crew.crew().kickoff(inputs={
            "analysis_results": [stock_data["stock_analysis"]],
            "report_type": "single_asset"
        })
        return {"report": result}
```

### Batch Processing

Process multiple assets efficiently:

```python
import asyncio

async def analyze_portfolio(tickers):
    crews = [StockCrew() for _ in tickers]
    
    # Execute crews in parallel
    tasks = [
        crew.crew().kickoff(inputs={"ticker": ticker})
        for crew, ticker in zip(crews, tickers)
    ]
    
    results = await asyncio.gather(*tasks)
    return dict(zip(tickers, results))
```

## Troubleshooting

### Common Issues

**Issue**: Crew execution hangs

```python
# Solution: Check task descriptions for reasoning compatibility
# Ensure single-ticker mode is specified for Deep Analysis Crew
```

**Issue**: API rate limits exceeded

```python
# Solution: Reduce max_rpm or add delays
crew = Crew(max_rpm=10)  # Reduce from default 20
```

**Issue**: Memory usage too high

```python
# Solution: Use minimal tool sets
tools = get_minimal_tools(asset_class)
```

**Issue**: Validation errors

```python
# Solution: Check output schema compatibility
result = OutputSchema.model_validate(crew_output)
```

## Related Documentation

- **[Tools Reference](tools.md)** - Available analysis tools
- **[Schemas Reference](schemas.md)** - Output data models
- **[Configuration Reference](configuration.md)** - Configuration options
- **[Flow Architecture](../../explanations/flow_architecture.md)** - Flow integration patterns

---

**Version**: 2.0  
**Last Updated**: 2025-10-26
