# Crew Data Integration - Quick Start Guide

## Overview

Quick reference for using the Crew Data Integration system to access enhanced data in reports.

## Basic Usage

### 1. Initialize Data Accessor

```python
from finwiz.integration.data_accessor import CrewDataAccessor

# Create accessor instance
accessor = CrewDataAccessor()
```

### 2. Access Enhanced Data

```python
# Get backtesting metrics
backtesting = accessor.get_backtesting_metrics()
if backtesting:
    print(f"Average Sharpe: {backtesting.average_metrics.sharpe_ratio:.2f}")

# Get market context
context = accessor.get_market_context()
if context:
    print(f"Market Regime: {context.market_regime.regime_type}")
    print(f"VIX Level: {context.vix_indicators.current_vix:.2f}")

# Get discovery methodology
methodology = accessor.get_discovery_methodology()
if methodology:
    print(f"Validation Rate: {methodology.validation_statistics.validation_rate:.2%}")

# Get performance report
performance = accessor.get_performance_report()
if performance:
    print(f"Top Opportunities: {', '.join(performance.top_opportunities)}")
```

### 3. Get Consolidated Data

```python
# Get all data in one call
consolidated = accessor.get_consolidated_reporter_input()

# Access all components
print(f"Stock Data: {consolidated.stock_data}")
print(f"ETF Data: {consolidated.etf_data}")
print(f"Crypto Data: {consolidated.crypto_data}")
print(f"Discovery Data: {consolidated.discovery_data}")
print(f"Backtesting: {consolidated.backtesting_summary}")
print(f"Market Context: {consolidated.market_context_summary}")
print(f"Methodology: {consolidated.methodology_summary}")
print(f"Performance: {consolidated.performance_report}")
```

## Common Patterns

### Check Data Availability

```python
# Always check for None
data = accessor.get_backtesting_metrics()
if data is None:
    print("Backtesting data not available")
    # Use fallback or skip section
else:
    # Process data
    process_backtesting(data)
```

### Generate Report Section

```python
def generate_section(accessor: CrewDataAccessor) -> str:
    """Generate report section with enhanced data."""
    
    # Get data
    data = accessor.get_backtesting_metrics()
    
    # Handle missing data
    if data is None:
        return "<p><em>Data not available</em></p>"
    
    # Generate HTML
    html = f"""
    <section>
        <h2>Performance Metrics</h2>
        <p>Sharpe Ratio: {data.average_metrics.sharpe_ratio:.2f}</p>
        <p>Max Drawdown: {data.average_metrics.max_drawdown:.2%}</p>
    </section>
    """
    
    return html
```

### Error Handling

```python
try:
    # Access data
    data = accessor.get_backtesting_metrics()
    
    # Process data
    if data:
        result = process_data(data)
    else:
        result = use_fallback()
        
except Exception as e:
    logger.error(f"Error accessing data: {e}")
    result = use_fallback()
```

## Extractor Methods

### BacktestingDataExtractor

```python
# Get specific symbol metrics
metrics = extractor.extract_backtesting_metrics("AAPL")

# Get regime performance
regime_perf = extractor.extract_regime_performance("AAPL")

# Get risk-adjusted metrics
risk_metrics = extractor.extract_risk_adjusted_metrics("AAPL")

# Get overall summary
summary = extractor.get_performance_summary()
```

### MarketContextExtractor

```python
# Get market regime
regime = extractor.extract_market_regime()

# Get VIX indicators
vix = extractor.extract_vix_indicators()

# Get macro indicators
macro = extractor.extract_macro_indicators()

# Get complete summary
summary = extractor.get_market_context_summary()
```

### DiscoveryMethodologyExtractor

```python
# Get screening criteria
criteria = extractor.extract_screening_criteria()

# Get validation statistics
stats = extractor.extract_validation_statistics()

# Get score breakdowns
scores = extractor.extract_fundamental_technical_scores()

# Get complete summary
summary = extractor.get_methodology_summary()
```

### PerformanceMetricsAggregator

```python
# Aggregate by asset type
by_asset = aggregator.aggregate_by_asset_type()

# Aggregate by regime
by_regime = aggregator.aggregate_by_regime()

# Calculate portfolio impact
impact = aggregator.calculate_portfolio_impact()

# Generate complete report
report = aggregator.generate_performance_report()
```

## HTML Report Generation

### Basic Section

```python
def generate_basic_section(data) -> str:
    """Generate basic HTML section."""
    return f"""
    <section>
        <h2>📊 Title</h2>
        <table>
            <tr>
                <th>Metric</th>
                <th>Value</th>
            </tr>
            <tr>
                <td>Return</td>
                <td>{data.return_value:.2%}</td>
            </tr>
        </table>
    </section>
    """
```

### With Styling

```python
def generate_styled_section(data) -> str:
    """Generate styled HTML section."""
    return f"""
    <section>
        <h2>📊 Performance</h2>
        <table class="metrics-table">
            <tr>
                <th>Metric</th>
                <th>Value</th>
            </tr>
            <tr>
                <td>Return</td>
                <td class="positive">{data.return_value:.2%}</td>
            </tr>
            <tr>
                <td>Drawdown</td>
                <td class="negative">{data.max_drawdown:.2%}</td>
            </tr>
        </table>
    </section>
    """
```

## Best Practices

1. **Always check for None** - Enhanced data may not be available
2. **Provide fallbacks** - Show meaningful content when data is missing
3. **Log warnings** - Help debugging when data is unavailable
4. **Use type hints** - Improve code clarity and IDE support
5. **Handle errors gracefully** - Don't let missing data break reports
6. **Cache results** - Accessor caches data automatically
7. **Document assumptions** - Note when using conservative defaults

## Common Issues

### Issue: Data Returns None

**Cause:** Discovery crew hasn't run or output is missing

**Solution:**
```python
if data is None:
    logger.warning("Discovery data not available")
    # Use fallback or skip section
```

### Issue: Incomplete Data

**Cause:** Partial crew execution or validation failures

**Solution:**
```python
# Check individual fields
if data and data.backtesting_summary:
    # Use backtesting data
else:
    # Skip backtesting section
```

### Issue: Stale Data

**Cause:** Data older than 24 hours

**Solution:**
```python
# Check freshness
freshness = accessor.check_data_freshness()
if not freshness.is_fresh:
    logger.warning(f"Data is {freshness.age_hours:.1f} hours old")
    # Recommend refresh or proceed with warning
```

## Complete Example

```python
from finwiz.integration.data_accessor import CrewDataAccessor
from datetime import datetime

def generate_complete_report() -> str:
    """Generate complete investment report."""
    
    # Initialize accessor
    accessor = CrewDataAccessor()
    
    # Get all data
    consolidated = accessor.get_consolidated_reporter_input()
    
    # Build report
    html = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Rapport FinWiz</title>
    </head>
    <body>
        <h1>📊 Rapport d'Investissement</h1>
        <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d')}</p>
    """
    
    # Add backtesting section
    if consolidated.backtesting_summary:
        html += generate_backtesting_section(consolidated.backtesting_summary)
    
    # Add market context section
    if consolidated.market_context_summary:
        html += generate_context_section(consolidated.market_context_summary)
    
    # Add methodology section
    if consolidated.methodology_summary:
        html += generate_methodology_section(consolidated.methodology_summary)
    
    # Add performance section
    if consolidated.performance_report:
        html += generate_performance_section(consolidated.performance_report)
    
    html += """
    </body>
    </html>
    """
    
    return html

# Generate and save report
report_html = generate_complete_report()
with open("report.html", "w", encoding="utf-8") as f:
    f.write(report_html)
```

## See Also

- [Enhanced Data Extraction Documentation](ENHANCED_DATA_EXTRACTION.md) - Complete extractor reference
- [Report Crew Enhanced Examples](REPORT_CREW_ENHANCED_EXAMPLES.md) - Detailed usage examples
- [Design Document](../.kiro/specs/crew-data-integration/design.md) - System architecture
- [Requirements Document](../.kiro/specs/crew-data-integration/requirements.md) - Feature requirements
