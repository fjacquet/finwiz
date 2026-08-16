# Pipeline Components

This document provides detailed information about each component of the Pure Python Pipeline.

## Portfolio Deep Analyzer {#portfolio-deep-analyzer}

### Overview

The Portfolio Deep Analyzer (`portfolio_deep_analyzer.py`) replaces AI-based DeepAnalysisCrew with fast, deterministic Python calculations.

### Key Features

- **Pure Python Scoring**: Uses `DeepAnalysisScorer` for deterministic calculations
- **Real Market Data**: Fetches actual data via `QuantitativeAnalysisTool`
- **JSON Export Generation**: Creates standardized exports for downstream systems
- **HTML Report Generation**: individual holding reports
- **Score Uniqueness Validation**: Prevents hardcoded defaults

### Performance Characteristics

- **Execution Time**: < 1 second per holding
- **LLM Calls**: 0
- **Cost**: $0.00
- **Memory Usage**: < 50 MB for typical portfolios

### Usage Example

```python
from finwiz.scoring.portfolio_deep_analyzer import analyze_portfolio_with_python

results = analyze_portfolio_with_python(
    holdings=portfolio_holdings,
    session_id="analysis_session_123"
)

# Access results
print(f"Successful: {results['successful_analyses']}")
print(f"Failed: {results['failed_analyses']}")
print(f"Time: {results['performance_metrics']['total_execution_time_seconds']:.2f}s")
```

### Output Structure

The analyzer generates:

1. **Individual JSON exports**: `output/{asset_class}/{ticker}_{session_id}.json`
2. **Individual HTML reports**: `output/{asset_class}/{ticker}_{session_id}.html`
3. **Consolidated export**: `output/deep_analysis_consolidated_{session_id}.json`

[View JSON export structure →](json-exports.md#individual-analysis-export)

## A+ Discovery Integrator {#aplus-discovery-integrator}

### Overview

The A+ Discovery Integrator (`aplus_discovery_integrator.py`) identifies A+ opportunities from deep analysis results by reading JSON exports.

### Key Features

- **Directory Scanning**: Scans `output/stock/`, `output/etf/`, `output/crypto/`
- **Grade Filtering**: Identifies A+ and A grade holdings
- **Cross-Asset Consolidation**: Consolidates opportunities across asset classes
- **Duplicate Removal**: Ensures unique ticker list

### Data Flow

```
output/stock/*.json  ─┐
output/etf/*.json    ─┼─> A+ Discovery Integration ─> Opportunities List
output/crypto/*.json ─┘
```

### Usage Example

```python
from finwiz.orchestrators.discovery.aplus_discovery_integrator import integrate_aplus_discovery_with_deep_analysis

discovery_results = integrate_aplus_discovery_with_deep_analysis(
    session_id="analysis_session_123"
)

if discovery_results["has_a_plus_analysis"]:
    print(f"Found {discovery_results['total_opportunities_found']} opportunities")
    for holding in discovery_results["aplus_holdings"]:
        print(f"  {holding['ticker']}: Grade {holding['grade']}")
```

### Output Structure

Returns an in-memory dict (it writes no file — the only reference to `output/aplus_discovery_*.json` in the repo is a *read* in `backtesting_pipeline_connector.py:50`) containing:

- `has_a_plus_analysis`: Boolean indicating if opportunities exist
- `total_opportunities_found`: Count of A+ opportunities
- `aplus_holdings`: List of opportunity details
- `total_analyzed`: Total holdings analyzed
- `integration_timestamp`: ISO timestamp

[View discovery results structure →](json-exports.md#discovery-results)

## Backtesting Pipeline Connector {#backtesting-pipeline-connector}

### Overview

The Backtesting Pipeline Connector (`backtesting_pipeline_connector.py`) automatically executes backtesting when A+ candidates are available.

> **This connector runs no backtest and computes no metric.** Every number it
> emits is a hardcoded placeholder, each tagged `# Simulated` in the source
> under the comment *"Simulate backtesting execution / In a real
> implementation, this would: 1. Load historical price data …"*
> (`integration/backtesting_pipeline_connector.py:129-145`):
>
> | Field | Value actually emitted |
> |---|---|
> | `annual_return` | `0.12` + `0.05` if grade is A+, else `+0.02` |
> | `sharpe_ratio` | `1.2` + `0.3` if grade is A+, else `+0.1` |
> | `max_drawdown` | `-0.15`, always |
> | `win_rate` | `0.65`, always |
> | `backtest_period` | `"5 years"`, always |
> | `status` | `"completed"` |
>
> It is not wired into the flow — nothing in `src/` or `tests/` calls it — so
> these values do not reach the report today. Treat the module as a stub, not
> as a data source.

### Key Features

- **Automatic Candidate Detection**: Reads A+ candidates from discovery results
- **Simulated results**: emits fixed placeholders per candidate (see above)
- **JSON Export**: Saves results for report integration

### Usage Example

```python
from finwiz.integration.backtesting_pipeline_connector import connect_backtesting_to_discovery_results

backtesting_results = connect_backtesting_to_discovery_results(
    session_id="analysis_session_123"
)

if backtesting_results["backtesting_executed"]:
    print(f"Backtested {backtesting_results['candidates_count']} candidates")
    for result in backtesting_results["results"]:
        print(f"  {result['ticker']}: {result['annual_return']:.1%} return")
```

### Output Structure

Generates `output/backtesting_results_{session_id}.json` containing:

- `candidates`: List of candidate details
- `results`: List of simulated results
- `execution_time_seconds`
- `session_id`
- `timestamp`

`backtesting_executed` and `candidates_count` are on the function's **return
value** only — they are not written to the JSON artifact.

[View backtesting results structure →](json-exports.md#backtesting-results)

## Python Report Generator {#python-report-generator}

### Overview

The Python Report Generator (`python_report_generator.py`) generates comprehensive HTML reports without any AI calls.

### Key Features

- **f-string generation**: the document is assembled in Python — this module imports no template engine and loads no template file. Sections come from `finwiz.reporting.sections/`, CSS from `assets/report_styles.css`.
- **Portfolio Statistics**: Calculates comprehensive statistics
- **Holdings Analysis**: Detailed analysis with grades and scores
- **Deep Analysis Integration**: Incorporates deep analysis results
- **Performance Metrics**: Displays execution metrics
- **Responsive Design**: Light/dark mode CSS styling

### Report Sections

1. **Executive Summary**
   - Portfolio grade and score
   - Total holdings and opportunities
   - Key statistics

2. **Portfolio Overview**
   - Asset class distribution
   - Grade distribution
   - Recommendation breakdown

3. **Holdings Analysis**
   - Detailed holding information
   - Grades and scores
   - Recommendations and rationale

4. **Strategic Recommendations**
   - Priority actions
   - Optimization suggestions
   - Python pipeline benefits

5. **Deep Analysis Results**
   - Analysis success metrics
   - Detailed scores
   - Component breakdowns

6. **Performance Metrics**
   - Execution time
   - Cost savings
   - Efficiency metrics

### Usage Example

```python
from finwiz.reporting.python_report_generator import generate_python_report

report_path = generate_python_report(
    portfolio_review=portfolio_review,
    deep_analysis_results=analysis_results,
    session_id="analysis_session_123"
)

print(f"Report generated: {report_path}")
```

### Output

Generates `output/finwiz_family_financial_plan.html` with:

- Professional HTML structure
- Responsive CSS styling
- Complete portfolio analysis
- Deep analysis integration
- Performance metrics

## Component Integration

### Sequential Execution

Components execute in sequence:

```
1. Portfolio Deep Analyzer
   ↓ (generates JSON exports)
2. A+ Discovery Integrator
   ↓ (identifies opportunities)
3. Backtesting Pipeline Connector
   ↓ (validates candidates)
4. Python Report Generator
   ↓ (consolidates results)
Final HTML Report
```

### Data Dependencies

- **A+ Discovery** depends on Deep Analysis JSON exports
- **Backtesting** depends on A+ Discovery results
- **Report Generator** depends on all previous components

### Error Handling

Each component implements graceful error handling:

- **Deep Analyzer**: Continues with remaining holdings if one fails
- **A+ Discovery**: Returns empty results if no exports found
- **Backtesting**: Skips execution if no candidates available
- **Report Generator**: Generates report even with partial data

## Performance Optimization

### Parallel Processing

- Deep Analyzer processes holdings sequentially (data fetching is I/O bound)
- HTML generation uses template caching

### Memory Management

- Streaming JSON parsing for large files
- Incremental report generation
- Automatic cleanup of temporary data

### Caching Strategy

- Market data cached per session
- Template compilation cached
- Analysis results cached in JSON

## Related Documentation

- **[Data Flow](data-flow.md)** - Complete data flow architecture
- **[JSON Exports](json-exports.md)** - Export structure specifications
- **[API Reference](../../reference/integration/python_pipeline_integration.md)** - Complete API documentation
- **[How-to Guide](../../how-to/use_python_pipeline.md)** - Usage instructions
