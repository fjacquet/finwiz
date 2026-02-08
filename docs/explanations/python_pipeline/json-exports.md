# JSON Export Structures

This document specifies the JSON export structures used throughout the Pure Python Pipeline.

## Individual Analysis Export

### Location

`output/{asset_class}/{ticker}_{session_id}.json`

### Structure

```json
{
  "crew_name": "PythonDeepAnalyzer",
  "execution_id": "python-AAPL-1730000000",
  "ticker": "AAPL",
  "asset_class": "stock",
  "analysis_timestamp": "2025-10-29T14:30:00Z",
  "composite_score": 0.850,
  "grade": "A",
  "recommendation": "BUY",
  "confidence": 0.85,
  "rationale": "Strong fundamentals with excellent technical indicators",
  "fundamental_score": 0.900,
  "technical_score": 0.800,
  "risk_score": 0.750,
  "risk_details": {
    "volatility": 0.20,
    "max_drawdown": -0.15,
    "beta": 1.05
  },
  "performance_metrics": {
    "execution_time_seconds": 0.1,
    "llm_calls": 0,
    "cost_usd": 0.0
  }
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `crew_name` | string | Always "PythonDeepAnalyzer" |
| `execution_id` | string | Unique execution identifier |
| `ticker` | string | Stock/ETF/Crypto ticker symbol |
| `asset_class` | string | "stock", "etf", or "crypto" |
| `analysis_timestamp` | string | ISO 8601 timestamp |
| `composite_score` | float | Overall score (0.0-1.0) |
| `grade` | string | Letter grade (A+, A, B, C, D, F) |
| `recommendation` | string | BUY, HOLD, or SELL |
| `confidence` | float | Confidence level (0.0-1.0) |
| `rationale` | string | Analysis rationale |
| `fundamental_score` | float | Fundamental analysis score |
| `technical_score` | float | Technical analysis score |
| `risk_score` | float | Risk assessment score |
| `risk_details` | object | Detailed risk metrics |
| `performance_metrics` | object | Execution metrics |

## Consolidated Export

### Location

`output/deep_analysis_consolidated_{session_id}.json`

### Structure

```json
{
  "session_id": "analysis_session_123",
  "analysis_timestamp": "2025-10-29T14:30:00Z",
  "total_analyses": 5,
  "exported_files": [
    "output/stock/AAPL_analysis_session_123.json",
    "output/stock/MSFT_analysis_session_123.json",
    "output/etf/SPY_analysis_session_123.json"
  ],
  "analyses": {
    "AAPL": {
      "ticker": "AAPL",
      "asset_class": "stock",
      "composite_score": 0.850,
      "grade": "A",
      "recommendation": "BUY"
    },
    "MSFT": {
      "ticker": "MSFT",
      "asset_class": "stock",
      "composite_score": 0.820,
      "grade": "A",
      "recommendation": "BUY"
    }
  }
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | string | Session identifier |
| `analysis_timestamp` | string | ISO 8601 timestamp |
| `total_analyses` | integer | Total number of analyses |
| `exported_files` | array | List of exported file paths |
| `analyses` | object | Map of ticker to analysis data |

## Discovery Results

### Location

`output/aplus_discovery_{session_id}.json`

### Structure

```json
{
  "has_a_plus_analysis": true,
  "total_opportunities_found": 3,
  "aplus_holdings": [
    {
      "ticker": "NVDA",
      "grade": "A+",
      "composite_score": 0.920,
      "asset_class": "stock",
      "recommendation": "BUY",
      "analysis_file": "output/stock/NVDA_analysis_session_123.json"
    },
    {
      "ticker": "TSLA",
      "grade": "A",
      "composite_score": 0.880,
      "asset_class": "stock",
      "recommendation": "BUY",
      "analysis_file": "output/stock/TSLA_analysis_session_123.json"
    }
  ],
  "total_analyzed": 5,
  "session_id": "analysis_session_123",
  "integration_timestamp": "2025-10-29T14:35:00Z"
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `has_a_plus_analysis` | boolean | Whether A+ opportunities exist |
| `total_opportunities_found` | integer | Count of A+ opportunities |
| `aplus_holdings` | array | List of A+ holding details |
| `total_analyzed` | integer | Total holdings analyzed |
| `session_id` | string | Session identifier |
| `integration_timestamp` | string | ISO 8601 timestamp |

### A+ Holding Structure

| Field | Type | Description |
|-------|------|-------------|
| `ticker` | string | Ticker symbol |
| `grade` | string | "A+" or "A" |
| `composite_score` | float | Overall score (0.0-1.0) |
| `asset_class` | string | Asset class type |
| `recommendation` | string | BUY, HOLD, or SELL |
| `analysis_file` | string | Path to analysis JSON |

## Backtesting Results

### Location

`output/backtesting_results_{session_id}.json`

### Structure

```json
{
  "backtesting_executed": true,
  "candidates_count": 3,
  "candidates": [
    {
      "ticker": "NVDA",
      "grade": "A+",
      "composite_score": 0.920,
      "asset_class": "stock"
    }
  ],
  "results": [
    {
      "ticker": "NVDA",
      "grade": "A+",
      "annual_return": 0.17,
      "sharpe_ratio": 1.50,
      "max_drawdown": -0.15,
      "win_rate": 0.65,
      "backtest_period": "5 years",
      "status": "completed"
    }
  ],
  "execution_time_seconds": 2.5,
  "session_id": "analysis_session_123",
  "timestamp": "2025-10-29T14:36:00Z"
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `backtesting_executed` | boolean | Whether backtesting ran |
| `candidates_count` | integer | Number of candidates tested |
| `candidates` | array | List of candidate details |
| `results` | array | List of backtesting results |
| `execution_time_seconds` | float | Total execution time |
| `session_id` | string | Session identifier |
| `timestamp` | string | ISO 8601 timestamp |

### Backtesting Result Structure

| Field | Type | Description |
|-------|------|-------------|
| `ticker` | string | Ticker symbol |
| `grade` | string | Letter grade |
| `annual_return` | float | Annualized return (0.17 = 17%) |
| `sharpe_ratio` | float | Risk-adjusted return metric |
| `max_drawdown` | float | Maximum decline (-0.15 = -15%) |
| `win_rate` | float | Winning trades percentage |
| `backtest_period` | string | Time period tested |
| `status` | string | "completed" or "failed" |

## File Naming Conventions

### Individual Analysis Files

Pattern: `{ticker}_{session_id}.json`

Examples:

- `AAPL_analysis_session_123.json`
- `SPY_analysis_session_123.json`
- `BTC_analysis_session_123.json`

### Consolidated Files

Pattern: `{type}_consolidated_{session_id}.json`

Examples:

- `deep_analysis_consolidated_analysis_session_123.json`

### Discovery Files

Pattern: `aplus_discovery_{session_id}.json`

Examples:

- `aplus_discovery_analysis_session_123.json`

### Backtesting Files

Pattern: `backtesting_results_{session_id}.json`

Examples:

- `backtesting_results_analysis_session_123.json`

## Directory Structure

```
output/
├── stock/
│   ├── AAPL_{session_id}.json
│   ├── AAPL_{session_id}.html
│   ├── MSFT_{session_id}.json
│   ├── MSFT_{session_id}.html
│   └── ...
├── etf/
│   ├── SPY_{session_id}.json
│   ├── SPY_{session_id}.html
│   └── ...
├── crypto/
│   ├── BTC_{session_id}.json
│   ├── BTC_{session_id}.html
│   └── ...
├── deep_analysis_consolidated_{session_id}.json
├── aplus_discovery_{session_id}.json
├── backtesting_results_{session_id}.json
└── finwiz_family_financial_plan.html
```

## JSON Schema Validation

### Individual Analysis Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": [
    "crew_name",
    "ticker",
    "asset_class",
    "composite_score",
    "grade",
    "recommendation"
  ],
  "properties": {
    "crew_name": {"type": "string"},
    "ticker": {"type": "string"},
    "asset_class": {"enum": ["stock", "etf", "crypto"]},
    "composite_score": {"type": "number", "minimum": 0, "maximum": 1},
    "grade": {"enum": ["A+", "A", "B", "C", "D", "F"]},
    "recommendation": {"enum": ["BUY", "HOLD", "SELL"]}
  }
}
```

## Best Practices

### File Writing

1. **Use UTF-8 encoding**: `encoding="utf-8"`
2. **Pretty print JSON**: `indent=2`
3. **Ensure ASCII compatibility**: `ensure_ascii=False`
4. **Handle datetime serialization**: Use `default=str`

```python
import json

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False, default=str)
```

### File Reading

1. **Handle missing files gracefully**
2. **Validate JSON structure**
3. **Log parsing errors**
4. **Continue processing on errors**

```python
import json
from pathlib import Path

try:
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}")
        return None

    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    # Validate structure
    assert "ticker" in data
    assert "composite_score" in data

    return data
except Exception as e:
    logger.error(f"Failed to read {file_path}: {e}")
    return None
```

## Related Documentation

- **[Data Flow](data-flow.md)** - Complete data flow architecture
- **[Components](components.md)** - Component documentation
- **[API Reference](../../reference/integration/python_pipeline_integration.md)** - API documentation
