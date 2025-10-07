# Enhanced Data Extraction System

## Overview

The Enhanced Data Extraction System provides specialized extractors that pull rich analytical data from upstream crew outputs for comprehensive reporting. This system enables the Report crew to access backtesting performance metrics, market context indicators, discovery methodology details, and aggregated performance data.

## Architecture

The system consists of four main extractor classes:

1. **BacktestingDataExtractor** - Extracts backtesting performance metrics from validation results
2. **MarketContextExtractor** - Extracts market regime and context indicators
3. **DiscoveryMethodologyExtractor** - Extracts screening criteria and validation statistics
4. **PerformanceMetricsAggregator** - Aggregates performance metrics across asset types and regimes

All extractors are integrated into the `CrewDataAccessor` for unified access.

## BacktestingDataExtractor

### Purpose

Extracts and structures backtesting performance metrics from `ValidationResult` objects in discovery crew outputs.

### Key Features

- Extracts core metrics: annualized return, Sharpe ratio, max drawdown, win rate
- Provides regime-specific performance analysis (bull/bear/sideways markets)
- Calculates risk-adjusted metrics (Sharpe, Sortino, Calmar ratios)
- Generates performance summaries across all A+ candidates

### Usage

```python
from finwiz.integration.data_accessor import CrewDataAccessor
from finwiz.integration.backtesting_extractor import BacktestingDataExtractor

# Initialize accessor
accessor = CrewDataAccessor()

# Get backtesting extractor
extractor = BacktestingDataExtractor(accessor)

# Extract metrics for a specific candidate
metrics = extractor.extract_backtesting_metrics("AAPL")
print(f"Annualized Return: {metrics.annualized_return:.2%}")
print(f"Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
print(f"Max Drawdown: {metrics.max_drawdown:.2%}")
print(f"Win Rate: {metrics.win_rate:.2%}")

# Extract regime-specific performance
regime_perf = extractor.extract_regime_performance("AAPL")
for regime, perf in regime_perf.items():
    print(f"{regime.capitalize()} Market:")
    print(f"  Return: {perf.annualized_return:.2%}")
    print(f"  Sharpe: {perf.sharpe_ratio:.2f}")
    print(f"  Consistency: {perf.consistency_score:.2f}")

# Get overall summary
summary = extractor.get_performance_summary()
print(f"Total Candidates: {summary.total_candidates_tested}")
print(f"Best Performer: {summary.best_performer}")
print(f"Average Sharpe: {summary.average_metrics.sharpe_ratio:.2f}")
```

### Methods

#### `extract_backtesting_metrics(symbol: str) -> Optional[BacktestingMetrics]`

Extracts core backtesting metrics for a specific symbol.

**Parameters:**
- `symbol` (str): The ticker symbol to extract metrics for

**Returns:**
- `BacktestingMetrics` object with performance data, or `None` if not available

**Example:**
```python
metrics = extractor.extract_backtesting_metrics("MSFT")
if metrics:
    print(f"Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
    print(f"Backtest Period: {metrics.backtest_period_years} years")
```

#### `extract_regime_performance(symbol: str) -> Dict[str, RegimePerformance]`

Extracts performance metrics for each market regime.

**Parameters:**
- `symbol` (str): The ticker symbol to extract regime performance for

**Returns:**
- Dictionary mapping regime types to `RegimePerformance` objects

**Example:**
```python
regime_perf = extractor.extract_regime_performance("GOOGL")
bull_perf = regime_perf.get("bull")
if bull_perf:
    print(f"Bull Market Return: {bull_perf.annualized_return:.2%}")
    print(f"Bull Market Sharpe: {bull_perf.sharpe_ratio:.2f}")
```

#### `extract_risk_adjusted_metrics(symbol: str) -> Optional[RiskAdjustedMetrics]`

Extracts risk-adjusted performance metrics.

**Parameters:**
- `symbol` (str): The ticker symbol to extract metrics for

**Returns:**
- `RiskAdjustedMetrics` object with Sharpe, Sortino, and Calmar ratios

**Example:**
```python
risk_metrics = extractor.extract_risk_adjusted_metrics("AMZN")
if risk_metrics:
    print(f"Sharpe: {risk_metrics.sharpe_ratio:.2f}")
    print(f"Sortino: {risk_metrics.sortino_ratio:.2f}")
    print(f"Calmar: {risk_metrics.calmar_ratio:.2f}")
```

#### `get_performance_summary() -> Optional[BacktestingSummary]`

Generates a summary of backtesting results across all A+ candidates.

**Returns:**
- `BacktestingSummary` object with aggregated metrics

**Example:**
```python
summary = extractor.get_performance_summary()
if summary:
    print(f"Candidates Tested: {summary.total_candidates_tested}")
    print(f"Average Return: {summary.average_metrics.annualized_return:.2%}")
    print(f"Best: {summary.best_performer}, Worst: {summary.worst_performer}")
```

## MarketContextExtractor

### Purpose

Extracts market regime and context indicators from `APlusDiscoveryResult` objects.

### Key Features

- Extracts market regime type (bull/bear/sideways/volatile)
- Provides VIX indicators with percentile calculations
- Extracts macroeconomic indicators (inflation, interest rates)
- Generates market context summaries with allocation implications

### Usage

```python
from finwiz.integration.market_context_extractor import MarketContextExtractor

# Initialize extractor
extractor = MarketContextExtractor(accessor)

# Extract market regime
regime = extractor.extract_market_regime()
if regime:
    print(f"Regime Type: {regime.regime_type}")
    print(f"VIX Level: {regime.vix_level:.2f}")
    print(f"Inflation Rate: {regime.inflation_rate:.2%}")
    print(f"Interest Rate Trend: {regime.interest_rate_trend}")
    print(f"Market Stress: {regime.market_stress_level}")

# Extract VIX indicators
vix = extractor.extract_vix_indicators()
if vix:
    print(f"Current VIX: {vix.current_vix:.2f}")
    print(f"VIX Percentile: {vix.vix_percentile:.1f}%")
    print(f"Volatility Regime: {vix.volatility_regime}")

# Extract macro indicators
macro = extractor.extract_macro_indicators()
if macro:
    print(f"Inflation: {macro.inflation_rate:.2%}")
    print(f"Interest Rate: {macro.interest_rate:.2%}")
    print(f"Rate Trend: {macro.interest_rate_trend}")

# Get comprehensive summary
summary = extractor.get_market_context_summary()
if summary:
    print(f"Risk Environment: {summary.risk_environment}")
    print("Allocation Implications:")
    for implication in summary.allocation_implications:
        print(f"  - {implication}")
```

### Methods

#### `extract_market_regime() -> Optional[MarketRegime]`

Extracts current market regime assessment.

**Returns:**
- `MarketRegime` object with regime type and indicators

#### `extract_vix_indicators() -> Optional[VIXIndicators]`

Extracts VIX volatility indicators.

**Returns:**
- `VIXIndicators` object with VIX levels and percentiles

#### `extract_macro_indicators() -> Optional[MacroIndicators]`

Extracts macroeconomic indicators.

**Returns:**
- `MacroIndicators` object with inflation and interest rate data

#### `get_market_context_summary() -> Optional[MarketContextSummary]`

Generates comprehensive market context summary.

**Returns:**
- `MarketContextSummary` with regime, VIX, macro data, and allocation implications

## DiscoveryMethodologyExtractor

### Purpose

Extracts discovery methodology details including screening criteria, validation statistics, and score breakdowns.

### Key Features

- Extracts A+ screening criteria and thresholds
- Provides validation statistics (screened vs. found vs. validated)
- Extracts fundamental and technical score breakdowns
- Generates methodology summaries for reporting

### Usage

```python
from finwiz.integration.discovery_methodology_extractor import DiscoveryMethodologyExtractor

# Initialize extractor
extractor = DiscoveryMethodologyExtractor(accessor)

# Extract screening criteria
criteria = extractor.extract_screening_criteria()
if criteria:
    print(f"ETF Max Expense Ratio: {criteria.etf_max_expense_ratio:.2%}")
    print(f"Stock Min ROE: {criteria.stock_min_roe:.2%}")
    print(f"Crypto Min Market Cap: ${criteria.crypto_min_market_cap:,.0f}")

# Extract validation statistics
stats = extractor.extract_validation_statistics()
if stats:
    print(f"Total Screened: {stats.total_screened}")
    print(f"Candidates Found: {stats.candidates_found}")
    print(f"Passed Validation: {stats.passed_validation}")
    print(f"Validation Rate: {stats.validation_rate:.2%}")

# Extract score breakdowns
scores = extractor.extract_fundamental_technical_scores()
for symbol, breakdown in scores.items():
    print(f"{symbol}:")
    print(f"  Fundamental: {breakdown.fundamental_score:.2f}")
    print(f"  Technical: {breakdown.technical_score:.2f}")
    print(f"  Composite: {breakdown.composite_score:.2f}")
    print(f"  Grade: {breakdown.grade}")

# Get methodology summary
summary = extractor.get_methodology_summary()
if summary:
    print(f"Validation Rate: {summary.validation_statistics.validation_rate:.2%}")
    print("Methodology Notes:")
    for note in summary.methodology_notes:
        print(f"  - {note}")
```

### Methods

#### `extract_screening_criteria() -> Optional[APlusCriteria]`

Extracts A+ screening criteria and thresholds.

**Returns:**
- `APlusCriteria` object with ETF, stock, and crypto criteria

#### `extract_validation_statistics() -> Optional[ValidationStatistics]`

Extracts validation statistics from discovery process.

**Returns:**
- `ValidationStatistics` object with screening and validation metrics

#### `extract_fundamental_technical_scores() -> Dict[str, ScoreBreakdown]`

Extracts score breakdowns for each A+ candidate.

**Returns:**
- Dictionary mapping symbols to `ScoreBreakdown` objects

#### `get_methodology_summary() -> Optional[MethodologySummary]`

Generates comprehensive methodology summary.

**Returns:**
- `MethodologySummary` with criteria, statistics, scores, and notes

## PerformanceMetricsAggregator

### Purpose

Aggregates performance metrics across asset types and market regimes for portfolio-level analysis.

### Key Features

- Aggregates metrics by asset type (ETF/stock/crypto)
- Aggregates metrics by market regime (bull/bear/sideways)
- Calculates portfolio impact metrics
- Generates comprehensive performance reports

### Usage

```python
from finwiz.integration.performance_metrics_aggregator import PerformanceMetricsAggregator

# Initialize aggregator
aggregator = PerformanceMetricsAggregator(backtesting_extractor)

# Aggregate by asset type
by_asset = aggregator.aggregate_by_asset_type()
for asset_type, metrics in by_asset.items():
    print(f"{asset_type.upper()}:")
    print(f"  Count: {metrics.count}")
    print(f"  Avg Return: {metrics.average_return:.2%}")
    print(f"  Avg Sharpe: {metrics.average_sharpe:.2f}")
    print(f"  Best: {metrics.best_performer}")

# Aggregate by regime
by_regime = aggregator.aggregate_by_regime()
for regime, metrics in by_regime.items():
    print(f"{regime.capitalize()} Market:")
    print(f"  Avg Return: {metrics.average_return:.2%}")
    print(f"  Avg Sharpe: {metrics.average_sharpe:.2f}")

# Calculate portfolio impact
impact = aggregator.calculate_portfolio_impact()
print(f"Expected Grade Improvement: {impact.expected_grade_improvement:.1f}%")
print(f"Expected Return Improvement: {impact.expected_return_improvement:.2%}")
print(f"Risk Impact: {impact.risk_impact}")
print(f"Diversification Impact: {impact.diversification_impact}")

# Generate comprehensive report
report = aggregator.generate_performance_report()
print(f"Top Opportunities: {', '.join(report.top_opportunities)}")
print(f"Report Generated: {report.report_timestamp}")
```

### Methods

#### `aggregate_by_asset_type() -> Dict[str, PerformanceMetrics]`

Aggregates performance metrics by asset type.

**Returns:**
- Dictionary mapping asset types to `PerformanceMetrics` objects

#### `aggregate_by_regime() -> Dict[str, PerformanceMetrics]`

Aggregates performance metrics by market regime.

**Returns:**
- Dictionary mapping regime types to `PerformanceMetrics` objects

#### `calculate_portfolio_impact() -> PortfolioImpactMetrics`

Calculates portfolio-level impact from A+ opportunities.

**Returns:**
- `PortfolioImpactMetrics` object with expected improvements

#### `generate_performance_report() -> PerformanceReport`

Generates comprehensive performance report.

**Returns:**
- `PerformanceReport` with aggregated metrics and top opportunities

## Integration with CrewDataAccessor

All extractors are integrated into `CrewDataAccessor` for unified access:

```python
from finwiz.integration.data_accessor import CrewDataAccessor

# Initialize accessor
accessor = CrewDataAccessor()

# Access extractors directly
backtesting_metrics = accessor.get_backtesting_metrics()
market_context = accessor.get_market_context()
methodology = accessor.get_discovery_methodology()
performance_report = accessor.get_performance_report()

# Or get consolidated reporter input with all enhanced data
consolidated = accessor.get_consolidated_reporter_input()
print(f"Backtesting Summary: {consolidated.backtesting_summary}")
print(f"Market Context: {consolidated.market_context_summary}")
print(f"Methodology: {consolidated.methodology_summary}")
print(f"Performance Report: {consolidated.performance_report}")
```

## Error Handling

All extractors implement graceful degradation:

```python
# Extractors return None when data is unavailable
metrics = extractor.extract_backtesting_metrics("UNKNOWN")
if metrics is None:
    print("Backtesting data not available for this symbol")

# Summaries return None when no discovery data exists
summary = extractor.get_performance_summary()
if summary is None:
    print("No discovery crew output available")

# Use conservative assumptions when data is missing
context = extractor.get_market_context_summary()
if context is None:
    print("Using conservative market assumptions")
```

## Best Practices

1. **Check for None**: Always check if extractor methods return `None` before accessing data
2. **Use Accessor Methods**: Access extractors through `CrewDataAccessor` for consistency
3. **Handle Missing Data**: Implement fallbacks when enhanced data is unavailable
4. **Cache Results**: Extractor results are cached by `CrewDataAccessor` for performance
5. **Log Warnings**: Log when enhanced data is missing to aid debugging

## See Also

- [Crew Data Integration Design](design.md)
- [Requirements Document](requirements.md)
- [Report Crew Enhanced Data Usage Examples](REPORT_CREW_ENHANCED_EXAMPLES.md)
