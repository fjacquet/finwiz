# Python Pipeline Integration Reference

## Overview

This reference documents the integration modules that connect the Pure Python Pipeline components together.

## Module: `aplus_discovery_integrator.py`

### Function: `integrate_aplus_discovery_with_deep_analysis`

Integrates A+ discovery with deep analysis results by reading JSON exports.

**Signature:**

```python
def integrate_aplus_discovery_with_deep_analysis(session_id: str) -> dict[str, Any]
```

**Parameters:**

- `session_id` (str): Session identifier for finding analysis files

**Returns:**

- `dict[str, Any]`: Discovery integration results containing:
  - `has_a_plus_analysis` (bool): Whether A+ analysis exists
  - `total_opportunities_found` (int): Number of A+ opportunities
  - `aplus_holdings` (list): List of A+ holding details
  - `total_analyzed` (int): Total holdings analyzed
  - `session_id` (str): Session identifier
  - `integration_timestamp` (str): ISO timestamp

**Example:**

```python
from finwiz.integration.aplus_discovery_integrator import integrate_aplus_discovery_with_deep_analysis

discovery_results = integrate_aplus_discovery_with_deep_analysis(
    session_id="analysis_session_123"
)

if discovery_results["has_a_plus_analysis"]:
    print(f"Found {discovery_results['total_opportunities_found']} A+ opportunities")
    for holding in discovery_results["aplus_holdings"]:
        print(f"  - {holding['ticker']}: Grade {holding['grade']}")
```

**Data Sources:**

- Scans `output/stock/*.json` for stock analysis files
- Scans `output/etf/*.json` for ETF analysis files
- Scans `output/crypto/*.json` for crypto analysis files
- Reads `output/deep_analysis_consolidated_{session_id}.json` if available

**Filtering Logic:**

- Only includes holdings with grade "A+" or "A"
- Excludes holdings with grades "B", "C", "D", "F"
- Removes duplicate tickers

**Error Handling:**

- Returns empty results if directories don't exist
- Logs warnings for unreadable files
- Continues processing even if individual files fail

## Module: `backtesting_pipeline_connector.py`

### Function: `connect_backtesting_to_discovery_results`

Connects backtesting pipeline to discovery results and executes backtesting for A+ candidates.

**Signature:**

```python
def connect_backtesting_to_discovery_results(session_id: str) -> dict[str, Any]
```

**Parameters:**

- `session_id` (str): Session identifier for finding discovery files

**Returns:**

- `dict[str, Any]`: Backtesting execution results containing:
  - `backtesting_executed` (bool): Whether backtesting was executed
  - `candidates_count` (int): Number of candidates tested
  - `candidates` (list): List of candidate details
  - `results` (list): List of backtesting results
  - `execution_time_seconds` (float): Total execution time
  - `results_file` (str): Path to results JSON file
  - `session_id` (str): Session identifier

**Example:**

```python
from finwiz.integration.backtesting_pipeline_connector import connect_backtesting_to_discovery_results

backtesting_results = connect_backtesting_to_discovery_results(
    session_id="analysis_session_123"
)

if backtesting_results["backtesting_executed"]:
    print(f"Backtested {backtesting_results['candidates_count']} candidates")
    for result in backtesting_results["results"]:
        print(f"  {result['ticker']}: {result['annual_return']:.1%} return, "
              f"Sharpe {result['sharpe_ratio']:.2f}")
```

**Data Sources:**

- Calls `integrate_aplus_discovery_with_deep_analysis()` to get candidates
- Falls back to reading discovery JSON files if integration fails
- Removes duplicate candidates

**Backtesting Metrics:**

- `annual_return` (float): Annualized return
- `sharpe_ratio` (float): Risk-adjusted return metric
- `max_drawdown` (float): Maximum peak-to-trough decline
- `win_rate` (float): Percentage of winning trades
- `backtest_period` (str): Time period tested
- `status` (str): Execution status

**Output Files:**

- Saves results to `output/backtesting_results_{session_id}.json`
- Includes candidates, results, and execution metadata

**Error Handling:**

- Returns `backtesting_executed: false` if no candidates found
- Logs errors and continues processing
- Includes error details in return value

## Module: `aplus_extractor.py`

### Class: `APlusDataExtractor`

Extracts and processes A+ opportunity data from discovery crew outputs.

**Constructor:**

```python
def __init__(self, output_dir: Path = Path("output")) -> None
```

**Parameters:**

- `output_dir` (Path): Base output directory containing crew outputs

**Methods:**

#### `extract_aplus_opportunities`

Extracts A+ opportunities from all discovery crew files.

**Signature:**

```python
def extract_aplus_opportunities(self) -> APlusOpportunityCollection | None
```

**Returns:**

- `APlusOpportunityCollection`: Collection of A+ opportunities, or None if extraction fails

**Example:**

```python
from finwiz.integration.aplus_extractor import APlusDataExtractor

extractor = APlusDataExtractor()
collection = extractor.extract_aplus_opportunities()

if collection:
    print(f"Stock opportunities: {len(collection.stock_opportunities)}")
    print(f"ETF opportunities: {len(collection.etf_opportunities)}")
    print(f"Crypto opportunities: {len(collection.crypto_opportunities)}")
    print(f"Confidence score: {collection.confidence_score:.2f}")
```

**Data Sources:**

- Reads `output/discovery/a_plus_stocks.json`
- Reads `output/discovery/a_plus_etfs.json`
- Reads `output/discovery/a_plus_crypto.json`
- Reads `output/discovery/discovery_latest.json` for market context

**Extraction Process:**

1. Loads JSON files from discovery directory
2. Cleans JSON content (fixes Python-style numeric literals)
3. Extracts opportunities with grades "A+" or "A"
4. Calculates composite scores from fundamentals
5. Generates discovery summary
6. Calculates confidence score
7. Extracts allocation recommendations and replacement notes
8. Extracts market context and backtesting metrics

#### `validate_aplus_opportunities`

Validates A+ opportunities collection for completeness and quality.

**Signature:**

```python
def validate_aplus_opportunities(
    self,
    collection: APlusOpportunityCollection
) -> tuple[bool, list[str]]
```

**Parameters:**

- `collection` (APlusOpportunityCollection): Collection to validate

**Returns:**

- `tuple[bool, list[str]]`: (is_valid, list_of_validation_errors)

**Validation Checks:**

- At least one opportunity found
- Confidence score ≥ 0.5
- Discovery summary ≥ 50 characters
- Allocation recommendations provided
- No duplicate symbols

**Example:**

```python
extractor = APlusDataExtractor()
collection = extractor.extract_aplus_opportunities()

if collection:
    is_valid, errors = extractor.validate_aplus_opportunities(collection)
    if is_valid:
        print("✅ Validation passed")
    else:
        print("❌ Validation failed:")
        for error in errors:
            print(f"  - {error}")
```

## Integration Patterns

### Pattern 1: Complete Pipeline Execution

Execute all pipeline components in sequence:

```python
from finwiz.scoring.portfolio_deep_analyzer import analyze_portfolio_with_python
from finwiz.integration.aplus_discovery_integrator import integrate_aplus_discovery_with_deep_analysis
from finwiz.integration.backtesting_pipeline_connector import connect_backtesting_to_discovery_results
from finwiz.reporting.python_report_generator import generate_python_report

# Step 1: Deep Analysis
analysis_results = analyze_portfolio_with_python(
    holdings=portfolio_holdings,
    session_id=session_id
)

# Step 2: A+ Discovery
discovery_results = integrate_aplus_discovery_with_deep_analysis(
    session_id=session_id
)

# Step 3: Backtesting
backtesting_results = connect_backtesting_to_discovery_results(
    session_id=session_id
)

# Step 4: Report Generation
report_path = generate_python_report(
    portfolio_review=portfolio_review,
    deep_analysis_results=analysis_results,
    session_id=session_id
)
```

### Pattern 2: Conditional Execution

Execute components conditionally based on results:

```python
# Always run deep analysis
analysis_results = analyze_portfolio_with_python(
    holdings=portfolio_holdings,
    session_id=session_id
)

# Only run discovery if analysis succeeded
if analysis_results["successful_analyses"] > 0:
    discovery_results = integrate_aplus_discovery_with_deep_analysis(
        session_id=session_id
    )
    
    # Only run backtesting if A+ opportunities found
    if discovery_results["has_a_plus_analysis"]:
        backtesting_results = connect_backtesting_to_discovery_results(
            session_id=session_id
        )
```

### Pattern 3: Error Handling

Implement comprehensive error handling:

```python
try:
    # Deep Analysis
    analysis_results = analyze_portfolio_with_python(
        holdings=portfolio_holdings,
        session_id=session_id
    )
except Exception as e:
    logger.error(f"Deep analysis failed: {e}")
    analysis_results = {"successful_analyses": 0}

try:
    # A+ Discovery
    discovery_results = integrate_aplus_discovery_with_deep_analysis(
        session_id=session_id
    )
except Exception as e:
    logger.error(f"A+ discovery failed: {e}")
    discovery_results = {"has_a_plus_analysis": False}

try:
    # Backtesting
    if discovery_results.get("has_a_plus_analysis"):
        backtesting_results = connect_backtesting_to_discovery_results(
            session_id=session_id
        )
except Exception as e:
    logger.error(f"Backtesting failed: {e}")
    backtesting_results = {"backtesting_executed": False}

# Always generate report (even with partial data)
report_path = generate_python_report(
    portfolio_review=portfolio_review,
    deep_analysis_results=analysis_results,
    session_id=session_id
)
```

## File Structure

### Input Files

```
output/
├── stock/
│   ├── AAPL_{session_id}.json
│   ├── MSFT_{session_id}.json
│   └── ...
├── etf/
│   ├── SPY_{session_id}.json
│   └── ...
├── crypto/
│   ├── BTC_{session_id}.json
│   └── ...
└── deep_analysis_consolidated_{session_id}.json
```

### Output Files

```
output/
├── aplus_discovery_{session_id}.json
├── backtesting_results_{session_id}.json
└── finwiz_family_financial_plan.html
```

## Performance Characteristics

### Execution Times

| Component | Typical Time | Notes |
|-----------|--------------|-------|
| A+ Discovery Integration | <1 second | File I/O only |
| Backtesting Pipeline | 2-5 seconds | Depends on candidate count |
| A+ Data Extraction | <1 second | JSON parsing |

### Memory Usage

| Component | Typical Memory | Notes |
|-----------|----------------|-------|
| A+ Discovery Integration | <10 MB | Minimal memory footprint |
| Backtesting Pipeline | <50 MB | Depends on candidate count |
| A+ Data Extraction | <20 MB | JSON data in memory |

## Error Codes

### A+ Discovery Integration

- `has_a_plus_analysis: false` - No A+ opportunities found
- `total_opportunities_found: 0` - Analysis completed but no A+ grades
- `error` key present - Exception occurred during integration

### Backtesting Pipeline

- `backtesting_executed: false` - Backtesting not executed
- `reason: "No A+ candidates available"` - No candidates to test
- `error` key present - Exception occurred during execution

## Troubleshooting

### Issue: No A+ Opportunities Found

**Symptoms:**

- `has_a_plus_analysis: false`
- `total_opportunities_found: 0`

**Possible Causes:**

1. Deep analysis not completed
2. No holdings achieved A+ or A grade
3. JSON files not in expected directories
4. Session ID mismatch

**Solutions:**

1. Verify deep analysis completed successfully
2. Check analysis results for grades
3. Verify output directory structure
4. Ensure consistent session_id usage

### Issue: Backtesting Not Executing

**Symptoms:**

- `backtesting_executed: false`
- `reason: "No A+ candidates available"`

**Possible Causes:**

1. A+ discovery found no opportunities
2. Discovery integration failed
3. Candidate list empty

**Solutions:**

1. Run A+ discovery integration first
2. Check discovery results for candidates
3. Verify discovery JSON files exist

## Related Documentation

- [Python Pipeline Architecture](../../explanations/python_pipeline_architecture.md)
- [How-to Guide](../../how-to/use_python_pipeline.md)
