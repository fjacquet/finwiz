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

Complete reference documentation for FinWiz's CrewAI crew(s), including configuration, inputs, outputs, and usage examples.

## Overview

FinWiz uses one CrewAI crew, `deep_analysis`, for qualitative financial
analysis. Six other crews (`stock_crew`, `etf_crew`, `crypto_crew`,
`investment_discovery_crew`, `portfolio_rebalancing_crew`, `report_crew`)
were deleted on 2026-09-07 because nothing invoked them — see root
`CLAUDE.md`'s "Crew Pattern" section. Everything below this point documented
those six crews and has been removed; only the surviving crew is documented
now.

## Available Crews

### Deep Analysis Crew

Unified crew for comprehensive analysis of any asset class with detailed grading and scoring.

**Location**: `src/finwiz/crews/deep_analysis/deep_analysis.py`

**Purpose**: Perform deep, comprehensive analysis for portfolio evaluation

**Inputs**:

```python
{
    "ticker": "AAPL",  # Required: Asset ticker
    "asset_class": "stock",  # Required: "stock", "etf", or "crypto"
}
```

**Example Usage** (verified: the import succeeds and the instance exposes
both `.kickoff()` and `.crew()`, matching the crew's own docstring):

```python
from finwiz.crews.deep_analysis.deep_analysis import DeepAnalysisCrew

crew = DeepAnalysisCrew()
result = crew.kickoff(inputs={"ticker": "AAPL", "asset_class": "stock"})
```

In production this crew is never called directly this way — it runs through
`analysis/stages/qualify.py`, wrapped by
`infrastructure/resilience/crew_execution.py`'s `execute_crew_with_timeout()`
for timeout handling, retries, and cost tracking. Its qualitative output is
combined with Python-computed quantitative scoring in
`synthesize_enriched_analysis()` (see root `CLAUDE.md`'s Execution Flow
diagram, Phase 3).

**Agents** (1 — `deep_analysis/config/agents.yaml`):

- **asset_analyst**: Qualitative-only agent ("Financial Analyst (Qualitative)").
  There is no separate reporter or grading agent — Python's
  `synthesize_enriched_analysis()` handles consolidation for $0.
  Quantitative scoring and grading happen in Python (`DeepAnalysisScorer`),
  not in this crew.

**Dynamic Tool Routing**:

- **Stock**: SEC analysis, fundamental metrics
- **ETF**: Fund analysis, expense evaluation
- **Crypto**: Blockchain analysis, market metrics

## Crew Configuration

### Agent Configuration

Agents are configured in YAML (`deep_analysis/config/agents.yaml`):

```yaml
asset_analyst:
  role: Financial Analyst (Qualitative)
  goal: Provide qualitative insights in French for {ticker}. Output JSON only.
  backstory: Expert financier qualitative.
```

### Task Configuration

Tasks are defined in YAML configuration (`deep_analysis/config/tasks.yaml`):

```yaml
deep_qualitative_analysis_task:
  description: >
    Qualitative analysis for {ticker} ({asset_class}). ...
  agent: asset_analyst
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
        max_rpm=20,  # Rate limiting
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
max_rpm = 20  # Maximum 20 requests per minute
```

### Tool Optimization

Use minimal tool sets for specific use cases:

```python
# Minimal tools for risk assessment
tools = [QuantitativeAnalysisTool(asset_class=asset_class), TickerExistenceValidationTool(), asset_specific_tool]
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
if not re.match(r"^[A-Z]{1,5}$", ticker):
    raise ValueError(f"Invalid ticker format: {ticker}")

# Validate asset class
if asset_class not in ["stock", "etf", "crypto"]:
    raise ValueError(f"Invalid asset class: {asset_class}")
```

### Output Processing

Process crew outputs consistently:

```python
# Check for successful execution
if hasattr(result, "error"):
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
    verbose=True,  # Enable detailed logging
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
        result = crew.crew().kickoff(inputs={"analysis_results": [stock_data["stock_analysis"]], "report_type": "single_asset"})
        return {"report": result}
```

### Batch Processing

Process multiple assets efficiently:

```python
import asyncio


async def analyze_portfolio(tickers):
    crews = [StockCrew() for _ in tickers]

    # Execute crews in parallel
    tasks = [crew.crew().kickoff(inputs={"ticker": ticker}) for crew, ticker in zip(crews, tickers)]

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
- **[Flow Architecture](../../explanations/ARCHITECTURE.md)** - Flow integration patterns

---

**Version**: 2.0
**Last Updated**: 2025-10-26
