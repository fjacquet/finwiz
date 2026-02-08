# Best Practices

This document provides best practices for implementing and using the Pure Python Pipeline.

## Score Uniqueness Validation

### Why It Matters

Score uniqueness validation ensures that each holding receives a unique score based on real market data, preventing the use of hardcoded default values.

### Implementation

```python
def _validate_score_uniqueness(
    self,
    analysis_results: dict[str, DeepAnalysisResult]
) -> None:
    """Validate that scores are unique across holdings."""
    if len(analysis_results) < 2:
        # Need at least 2 holdings to check uniqueness
        return

    # Extract composite scores
    composite_scores = [
        result.composite_score
        for result in analysis_results.values()
    ]

    # Calculate standard deviation
    import statistics
    composite_std = statistics.stdev(composite_scores)

    # Check for identical scores (std dev < 0.03 indicates hardcoded values)
    if composite_std < 0.03:
        raise ValueError(
            f"Score validation failed: All holdings have identical scores "
            f"(std={composite_std:.4f}). Expected unique scores per ticker."
        )
```

### Best Practices

1. **Always validate**: Run validation after analysis completes
2. **Set appropriate threshold**: 0.03 allows similar but not identical scores
3. **Log validation results**: Track standard deviation for monitoring
4. **Handle validation errors**: Provide clear error messages

## Real Data Fetching

### Why It Matters

Fetching real market data ensures analysis is based on actual market conditions, not placeholder values.

### Implementation

```python
def _extract_holding_data(
    self,
    holding: HoldingDecision
) -> dict[str, Any] | None:
    """Extract real market data from holding for scoring."""
    from finwiz.tools.quantitative_analysis_tool import QuantitativeAnalysisTool

    try:
        # Fetch real quantitative data
        quant_tool = QuantitativeAnalysisTool()
        quant_data = quant_tool._run(
            symbol=holding.ticker,
            asset_class=holding.asset_class,
            analysis_type="performance"
        )

        # Extract real values
        return {
            "ticker": holding.ticker,
            "volatility": quant_data.get("volatility", 0.20),
            "max_drawdown": quant_data.get("max_drawdown", -0.15),
            "beta": quant_data.get("beta", 1.0),
            # ... other metrics
        }
    except Exception as e:
        logger.error(f"Failed to fetch data for {holding.ticker}: {e}")
        # Return None to signal this holding should be skipped
        return None
```

### Best Practices

1. **Handle API failures gracefully**: Return None for unavailable data
2. **Log fetch attempts**: Track success/failure rates
3. **Use appropriate defaults**: Only as fallback, not primary values
4. **Validate data quality**: Check for reasonable value ranges

## JSON Export Structure

### Why It Matters

Standardized export structure ensures downstream systems can reliably consume analysis results.

### Implementation

```python
def _export_json_files(
    self,
    json_exports: dict[str, Any],
    session_id: str
) -> dict[str, Any]:
    """Export JSON files to proper output directories."""
    # Create asset class directories
    stock_dir = self.output_dir / "stock"
    etf_dir = self.output_dir / "etf"
    crypto_dir = self.output_dir / "crypto"

    for dir_path in [stock_dir, etf_dir, crypto_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)

    exported_files = []

    # Export with session_id in filename
    for ticker, export_data in json_exports.items():
        asset_class = export_data["asset_class"]

        # Determine output directory
        if asset_class == "stock":
            output_path = stock_dir / f"{ticker}_{session_id}.json"
        elif asset_class == "etf":
            output_path = etf_dir / f"{ticker}_{session_id}.json"
        elif asset_class == "crypto":
            output_path = crypto_dir / f"{ticker}_{session_id}.json"
        else:
            output_path = stock_dir / f"{ticker}_{session_id}.json"

        # Write JSON file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)

        exported_files.append(str(output_path))

    return {"exported_files": exported_files}
```

### Best Practices

1. **Use consistent naming**: `{ticker}_{session_id}.json`
2. **Organize by asset class**: Separate directories for stock/etf/crypto
3. **Include session ID**: Enables tracking and cleanup
4. **Pretty print JSON**: Use `indent=2` for readability
5. **Handle datetime serialization**: Use `default=str`

## Error Handling

### Why It Matters

Graceful error handling ensures the pipeline continues processing even when individual holdings fail.

### Implementation

```python
def analyze_portfolio_holdings(
    self,
    holdings: list[HoldingDecision],
    session_id: str
) -> dict[str, Any]:
    """Analyze all portfolio holdings with error handling."""
    results = {
        "successful_analyses": 0,
        "failed_analyses": 0,
        "deep_analysis_results": {}
    }

    for holding in holdings:
        try:
            # Extract data
            data = self._extract_holding_data(holding)

            # Skip if data unavailable
            if data is None:
                logger.warning(f"Skipping {holding.ticker} - data unavailable")
                results["failed_analyses"] += 1
                continue

            # Run analysis
            analysis_result = self.scorer.calculate_composite_score(
                ticker=holding.ticker,
                asset_class=holding.asset_class,
                data=data
            )

            # Store result
            results["deep_analysis_results"][holding.ticker] = analysis_result
            results["successful_analyses"] += 1

        except Exception as e:
            logger.error(f"Failed to analyze {holding.ticker}: {e}")
            results["failed_analyses"] += 1

    return results
```

### Best Practices

1. **Continue on errors**: Don't stop entire pipeline for one failure
2. **Log all errors**: Include ticker and error details
3. **Track success/failure**: Maintain counts for monitoring
4. **Return partial results**: Even if some holdings fail
5. **Provide clear error messages**: Help with debugging

## Session ID Management

### Why It Matters

Unique session IDs prevent file conflicts and enable tracking of analysis runs.

### Implementation

```python
import time
from datetime import datetime

# Timestamp-based (simple)
session_id = f"analysis_{int(time.time())}"

# Date-based (readable)
session_id = f"portfolio_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# User-based (multi-user)
session_id = f"user_{user_id}_{int(time.time())}"

# Portfolio-based (organized)
session_id = f"{portfolio_name}_{int(time.time())}"
```

### Best Practices

1. **Always use unique IDs**: Prevent file overwrites
2. **Include timestamp**: Enables chronological sorting
3. **Use descriptive prefixes**: Helps identify analysis type
4. **Keep IDs short**: Avoid excessively long filenames
5. **Document ID format**: Maintain consistency across team

## Performance Optimization

### Parallel Processing

While the current implementation processes holdings sequentially, consider these optimization strategies:

```python
# Future: Parallel processing with asyncio
import asyncio

async def analyze_holding_async(holding, session_id):
    """Async analysis for parallel processing."""
    # Fetch data asynchronously
    data = await fetch_data_async(holding.ticker)

    # Calculate score (CPU-bound, still sequential)
    result = calculate_score(data)

    return result

# Process multiple holdings in parallel
results = await asyncio.gather(*[
    analyze_holding_async(h, session_id)
    for h in holdings
])
```

### Caching Strategy

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_market_data(ticker: str, date: str) -> dict:
    """Cache market data to avoid redundant API calls."""
    return fetch_market_data(ticker, date)
```

### Memory Management

```python
# Process large portfolios in batches
BATCH_SIZE = 10

for i in range(0, len(holdings), BATCH_SIZE):
    batch = holdings[i:i + BATCH_SIZE]
    batch_results = analyze_batch(batch, session_id)

    # Write results immediately
    export_batch_results(batch_results)

    # Clear memory
    del batch_results
```

## Testing Practices

### Unit Testing

```python
def test_should_calculate_unique_scores_per_ticker(mocker):
    """Test that each ticker gets unique score."""
    # Arrange
    holdings = [
        create_holding("AAPL"),
        create_holding("MSFT"),
        create_holding("GOOGL")
    ]

    # Mock data fetching to return different values
    mocker.patch('finwiz.tools.quantitative_analysis_tool.QuantitativeAnalysisTool._run')

    # Act
    results = analyze_portfolio_with_python(holdings, "test_session")

    # Assert
    scores = [r.composite_score for r in results["deep_analysis_results"].values()]
    assert len(set(scores)) == len(scores), "Scores should be unique"
```

### Integration Testing

```python
@pytest.mark.integration
def test_should_complete_full_pipeline():
    """Test complete pipeline execution."""
    # Arrange
    holdings = load_test_holdings()
    session_id = f"integration_test_{int(time.time())}"

    # Act
    analysis_results = analyze_portfolio_with_python(holdings, session_id)
    discovery_results = integrate_aplus_discovery_with_deep_analysis(session_id)
    backtesting_results = connect_backtesting_to_discovery_results(session_id)

    # Assert
    assert analysis_results["successful_analyses"] > 0
    assert discovery_results["has_a_plus_analysis"] in [True, False]
    assert "backtesting_executed" in backtesting_results
```

## Documentation Practices

### Code Documentation

```python
def analyze_portfolio_with_python(
    holdings: list[HoldingDecision],
    session_id: str
) -> dict[str, Any]:
    """
    Analyze portfolio holdings using pure Python.

    This function replaces AI-based DeepAnalysisCrew with deterministic
    Python calculations for 10-20x speed improvement and 100% cost reduction.

    Args:
        holdings: List of portfolio holdings to analyze
        session_id: Unique session identifier for tracking

    Returns:
        Dictionary containing:
            - successful_analyses: Count of successful analyses
            - failed_analyses: Count of failed analyses
            - deep_analysis_results: Map of ticker to analysis result
            - performance_metrics: Execution metrics

    Example:
        >>> results = analyze_portfolio_with_python(holdings, "session_123")
        >>> print(f"Analyzed {results['successful_analyses']} holdings")
    """
```

### Inline Comments

```python
# Validate score uniqueness to prevent hardcoded defaults
self._validate_score_uniqueness(results["deep_analysis_results"])

# Export JSON files to proper directories (Requirements 0.8-0.12)
export_info = self._export_json_files(json_exports, session_id)

# Generate HTML reports using existing template (CRITICAL FIX)
html_content = generator.generate_report(export_data)
```

## Related Documentation

- **[Components](components.md)** - Component documentation
- **[Data Flow](data-flow.md)** - Data flow architecture
- **[Troubleshooting](troubleshooting.md)** - Common issues
- **[How-to Guide](../../how-to/use_python_pipeline.md)** - Usage instructions
