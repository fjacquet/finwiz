# Data Quality Guide for FinWiz

Comprehensive guide for maintaining data quality in FinWiz financial reports.

## Table of Contents

1. [Core Principles](#core-principles)
2. [Data Validation at Source](#data-validation-at-source)
3. [Handling Missing Data](#handling-missing-data)
4. [Data Availability Tracking](#data-availability-tracking)
5. [Component Reference](#component-reference)
6. [Best Practices](#best-practices)
7. [Common Scenarios](#common-scenarios)

## Core Principles

### 1. Fail Fast

Reject invalid data at the source rather than attempting to fix it downstream.

**Why**: Prevents cascading errors and maintains data integrity throughout the system.

**Example**:

```python
# ✅ Correct - Reject at source
def validate_ticker(ticker: str) -> str | None:
    if not ticker or not ticker.isalpha():
        logger.warning(f"Invalid ticker format: {ticker}")
        return None
    return ticker.upper()

# ❌ Incorrect - Try to fix downstream
def validate_ticker(ticker: str) -> str:
    # Assumes ticker is valid, causes issues later
    return ticker.upper()
```

### 2. Transparency

Always communicate when data is unavailable rather than hiding the issue.

**Why**: Users need to know data limitations to make informed decisions.

**Example**:

```python
# ✅ Correct - Clear communication
if sec_url is None:
    return "No SEC filings available for this ticker"

# ❌ Incorrect - Hide the issue
if sec_url is None:
    return ""  # Silent failure
```

### 3. No Hallucinations

Never generate fake data to fill gaps in real data.

**Why**: Fake data undermines trust and can lead to poor investment decisions.

**Example**:

```python
# ✅ Correct - Return None for missing data
def get_sharpe_ratio(ticker: str) -> float | None:
    ratio = calculate_sharpe(ticker)
    if ratio is None:
        return None
    return ratio

# ❌ Incorrect - Generate fake data
def get_sharpe_ratio(ticker: str) -> str:
    ratio = calculate_sharpe(ticker)
    if ratio is None:
        return "Données non disponibles"  # Fake string instead of None
    return str(ratio)
```

### 4. Completeness

Process all available data, even if some validation checks fail.

**Why**: Partial data is better than no data, as long as limitations are documented.

**Example**:

```python
# ✅ Correct - Process all, mark validation status
for holding in all_holdings:
    result = process_holding(holding)
    result.validation_status = validate(holding)
    results.append(result)

# ❌ Incorrect - Skip failed validations
for holding in all_holdings:
    if validate(holding):
        results.append(process_holding(holding))
    # Silently excludes invalid holdings
```

### 5. Traceability

Log all data decisions and rejections for debugging and auditing.

**Why**: Enables troubleshooting and ensures accountability.

**Example**:

```python
# ✅ Correct - Log decisions
if not is_valid_url(url):
    logger.warning(f"Rejected invalid URL for {ticker}: {url}")
    return None

# ❌ Incorrect - Silent rejection
if not is_valid_url(url):
    return None  # No logging
```

## Data Validation at Source

### SEC Filing URLs

**Problem**: Hardcoded or outdated SEC URLs that return 404 errors.

**Solution**: Use `SECFilingURLGenerator` to generate and verify URLs.

```python
from finwiz.tools.sec_filing_url_generator import SECFilingURLGenerator

generator = SECFilingURLGenerator()

# Generate URL with automatic CIK lookup
url = generator.get_filing_url(ticker="AAPL", filing_type="10-K")

if url is None:
    # No filings available
    return "No SEC filings available"

# Verify URL is accessible
if generator.verify_url(url):
    # URL is valid and returns 200
    return url
else:
    # URL exists but is inaccessible
    fallback_url = generator.get_company_browse_url(cik)
    return fallback_url
```

**Features**:

- Automatic CIK lookup from ticker
- URL format validation
- HTTP status verification
- Fallback to company browse page
- Returns None when no filings exist

### Sentiment Data

**Problem**: News articles with fake URLs (example.com, test.com).

**Solution**: Validate URLs before including articles in analysis.

```python
from finwiz.tools.enhanced_sentiment_tool import StandardizedSentimentTool

tool = StandardizedSentimentTool()

# Tool automatically validates URLs
result = tool._run(ticker="AAPL", asset_class="stock", days_back=7)

# Only real, accessible URLs are included
for article in result.articles:
    assert article.url.startswith("http")
    assert "example.com" not in article.url
    assert "test.com" not in article.url
```

**Validation Rules**:

- URL must start with http:// or https://
- URL must not contain forbidden patterns (example.com, test.com, localhost)
- URL must be accessible (optional HEAD request)
- Articles with invalid URLs are logged and excluded

### Portfolio Holdings

**Problem**: Holdings missing from reports due to validation failures.

**Solution**: Use `PortfolioHoldingsProcessor` to process ALL holdings.

```python
from finwiz.orchestrators.portfolio_holdings_processor import PortfolioHoldingsProcessor

processor = PortfolioHoldingsProcessor()

# Load all holdings from CSV files
holdings = processor.load_all_holdings()
# Returns: {"stocks": [...], "etfs": [...], "crypto": [...]}

# Process ALL holdings, including those that fail validation
processed = processor.process_holdings(holdings)

# Get summary of what was processed
summary = processor.get_processing_summary()
print(f"Processed: {summary.total_processed}/{summary.total_holdings}")
print(f"Excluded: {summary.total_excluded}")
print(f"Reasons: {summary.exclusion_reasons}")
```

**Features**:

- Reads from stock.csv, etf.csv, crypto.csv
- Processes ALL holdings regardless of validation status
- Tracks excluded holdings with reasons
- Provides detailed processing summary
- Logs each holding processed

## Handling Missing Data

### Return None, Not Fake Data

**Always use None for missing data**:

```python
# ✅ Correct - Use None
class BacktestingMetrics(BaseModel):
    annualized_return: float | None
    sharpe_ratio: float | None
    max_drawdown: float | None

# ❌ Incorrect - Use strings
class BacktestingMetrics(BaseModel):
    annualized_return: str  # "Données non disponibles"
    sharpe_ratio: str       # "N/A"
    max_drawdown: str       # "Not available"
```

### Display "Not Available" in Reports

**Format None values for display**:

```python
def format_metric(value: float | None, format_str: str = ".2f") -> str:
    """Format metric for display, showing 'Not calculated' for None."""
    if value is None:
        return "Not calculated"
    return f"{value:{format_str}}"

# Usage
sharpe_ratio = get_sharpe_ratio(ticker)
display_value = format_metric(sharpe_ratio, ".2f")
# Returns: "1.25" or "Not calculated"
```

### A+ Discovery Results

**Handle missing discovery results**:

```python
from finwiz.integration.aplus_discovery_accessor import APlusDiscoveryAccessor

accessor = APlusDiscoveryAccessor()

# Check if results exist
if not accessor.has_discovery_results():
    return "A+ discovery not run - use --discovery flag"

# Load results
results = accessor.load_discovery_results()

if results is None or len(results.opportunities) == 0:
    return "No A+ opportunities found in current analysis"

# Display opportunities
summary = accessor.get_opportunities_summary()
return summary
```

### Backtesting Metrics

**Extract available metrics, mark others as None**:

```python
from finwiz.integration.backtesting_extractor import BacktestingMetricsExtractor

extractor = BacktestingMetricsExtractor()

# Extract all available metrics
metrics = extractor.extract_metrics(validation_result)

# Get dict with None for unavailable metrics
available = extractor.get_available_metrics(metrics)
# Returns: {
#   "annualized_return": 0.15,
#   "sharpe_ratio": 1.2,
#   "max_drawdown": None,  # Not calculated
#   "win_rate": None       # Not calculated
# }

# Format for display
display = extractor.format_for_display(metrics)
# Returns formatted string with "Not calculated" for None values
```

## Data Availability Tracking

### Track All Data Sources

**Use `DataAvailabilityTracker` to track every data source**:

```python
from finwiz.integration.data_availability_tracker import DataAvailabilityTracker

tracker = DataAvailabilityTracker()

# Track sentiment data
if sentiment_data:
    tracker.track_data_source("sentiment", "available", age_hours=2)
else:
    tracker.track_data_source("sentiment", "unavailable", age_hours=0)

# Track SEC filings
if sec_url:
    tracker.track_data_source("sec_filings", "available", age_hours=24)
else:
    tracker.track_data_source("sec_filings", "unavailable", age_hours=0)

# Track portfolio data
tracker.track_data_source("portfolio", "available", age_hours=1)

# Track discovery results
if discovery_results:
    tracker.track_data_source("discovery", "available", age_hours=12)
else:
    tracker.track_data_source("discovery", "not_run", age_hours=0)

# Track backtesting
if backtesting_metrics:
    tracker.track_data_source("backtesting", "available", age_hours=168)
else:
    tracker.track_data_source("backtesting", "unavailable", age_hours=0)
```

### Generate Availability Summary

**Include summary in reports**:

```python
# Get availability summary
summary = tracker.get_availability_summary()

print(f"Data Sources: {summary.available_sources}/{summary.total_sources} available")
print(f"Stale Sources: {summary.stale_sources}")

# Get freshness warnings
warnings = tracker.get_freshness_warnings()
for warning in warnings:
    print(f"⚠️ {warning}")

# Example output:
# Data Sources: 4/5 available
# Stale Sources: 1
# ⚠️ Backtesting data is 8 days old (stale threshold: 7 days)
```

### Data Freshness Thresholds

**Default thresholds**:

- **Stale**: > 7 days old
- **Very Stale**: > 30 days old

**Custom thresholds**:

```python
tracker = DataAvailabilityTracker(stale_threshold_hours=168)  # 7 days

# Track with custom age
tracker.track_data_source("sentiment", "available", age_hours=48)

# Check if stale
warnings = tracker.get_freshness_warnings()
# No warning if age_hours < stale_threshold_hours
```

## Component Reference

### SECFilingURLGenerator

**Purpose**: Generate valid, working SEC filing URLs.

**Location**: `src/finwiz/tools/sec_filing_url_generator.py`

**Methods**:

- `get_filing_url(ticker, filing_type)`: Get filing URL or None
- `get_company_browse_url(cik)`: Get company browse page URL
- `verify_url(url)`: Verify URL returns 200 status

**Example**:

```python
generator = SECFilingURLGenerator()

url = generator.get_filing_url("AAPL", "10-K")
if url and generator.verify_url(url):
    print(f"Valid URL: {url}")
else:
    print("No valid filing URL available")
```

### PortfolioHoldingsProcessor

**Purpose**: Process all portfolio holdings from CSV files.

**Location**: `src/finwiz/orchestrators/portfolio_holdings_processor.py`

**Methods**:

- `load_all_holdings()`: Load from stock.csv, etf.csv, crypto.csv
- `process_holdings(holdings)`: Process ALL holdings
- `get_processing_summary()`: Get summary of processing

**Example**:

```python
processor = PortfolioHoldingsProcessor()

holdings = processor.load_all_holdings()
processed = processor.process_holdings(holdings)
summary = processor.get_processing_summary()

print(f"Processed {summary.total_processed} holdings")
print(f"Excluded {summary.total_excluded} holdings")
```

### APlusDiscoveryAccessor

**Purpose**: Access A+ discovery results reliably.

**Location**: `src/finwiz/integration/aplus_discovery_accessor.py`

**Methods**:

- `has_discovery_results()`: Check if results exist
- `load_discovery_results()`: Load results or None
- `get_opportunities_summary()`: Get human-readable summary

**Example**:

```python
accessor = APlusDiscoveryAccessor()

if accessor.has_discovery_results():
    results = accessor.load_discovery_results()
    summary = accessor.get_opportunities_summary()
    print(summary)
else:
    print("Discovery not run")
```

### DataAvailabilityTracker

**Purpose**: Track and report data availability and freshness.

**Location**: `src/finwiz/integration/data_availability_tracker.py`

**Methods**:

- `track_data_source(source, status, age_hours)`: Track source
- `get_availability_summary()`: Get summary
- `get_freshness_warnings()`: Get warnings for stale data

**Example**:

```python
tracker = DataAvailabilityTracker()

tracker.track_data_source("sentiment", "available", age_hours=2)
tracker.track_data_source("sec_filings", "unavailable", age_hours=0)

summary = tracker.get_availability_summary()
warnings = tracker.get_freshness_warnings()
```

## Best Practices

### 1. Validate Early

Validate data as soon as it enters the system:

```python
# ✅ Correct - Validate at entry point
def fetch_stock_data(ticker: str) -> StockData | None:
    # Validate ticker first
    if not is_valid_ticker(ticker):
        logger.warning(f"Invalid ticker: {ticker}")
        return None
    
    # Fetch data
    data = api.get_stock_data(ticker)
    
    # Validate response
    if not is_valid_response(data):
        logger.warning(f"Invalid response for {ticker}")
        return None
    
    return data

# ❌ Incorrect - Validate late
def fetch_stock_data(ticker: str) -> StockData:
    data = api.get_stock_data(ticker)
    # Assumes data is valid, causes issues later
    return data
```

### 2. Log All Rejections

Log every time data is rejected:

```python
# ✅ Correct - Log rejections
if not is_valid_url(url):
    logger.warning(
        f"Rejected invalid URL",
        extra={"ticker": ticker, "url": url, "reason": "invalid_format"}
    )
    return None

# ❌ Incorrect - Silent rejection
if not is_valid_url(url):
    return None
```

### 3. Provide Context

Include context in error messages:

```python
# ✅ Correct - Provide context
raise ValueError(
    f"Invalid ticker format: '{ticker}'. "
    f"Expected 1-5 uppercase letters, got '{ticker}'"
)

# ❌ Incorrect - Generic message
raise ValueError("Invalid ticker")
```

### 4. Use Type Hints

Use type hints to indicate optional data:

```python
# ✅ Correct - Clear that data may be None
def get_sharpe_ratio(ticker: str) -> float | None:
    ...

# ❌ Incorrect - Unclear if data can be None
def get_sharpe_ratio(ticker: str) -> float:
    ...
```

### 5. Document Limitations

Document data limitations in docstrings:

```python
def get_backtesting_metrics(ticker: str) -> BacktestingMetrics | None:
    """
    Get backtesting metrics for ticker.
    
    Returns None if:
    - Backtesting has not been run
    - Insufficient historical data
    - Calculation errors occurred
    
    Note: Individual metrics may be None if not calculable.
    """
    ...
```

## Common Scenarios

### Scenario 1: Missing SEC Filings

**Problem**: Ticker has no SEC filings (e.g., foreign stock, crypto).

**Solution**:

```python
generator = SECFilingURLGenerator()

url = generator.get_filing_url(ticker="BTC-USD", filing_type="10-K")

if url is None:
    # Expected for crypto
    return "No SEC filings available (cryptocurrency)"
```

### Scenario 2: Stale Backtesting Data

**Problem**: Backtesting data is 30 days old.

**Solution**:

```python
tracker = DataAvailabilityTracker()

tracker.track_data_source("backtesting", "available", age_hours=720)  # 30 days

warnings = tracker.get_freshness_warnings()
# Returns: "Backtesting data is 30 days old (stale threshold: 7 days)"

# Include warning in report
if warnings:
    report += f"\n⚠️ Data Freshness Warnings:\n"
    for warning in warnings:
        report += f"- {warning}\n"
```

### Scenario 3: Discovery Not Run

**Problem**: User didn't run discovery crew.

**Solution**:

```python
accessor = APlusDiscoveryAccessor()

if not accessor.has_discovery_results():
    return {
        "status": "not_run",
        "message": "A+ discovery not run - use --discovery flag to enable",
        "opportunities": []
    }
```

### Scenario 4: Incomplete Portfolio

**Problem**: Some holdings excluded from report.

**Solution**:

```python
processor = PortfolioHoldingsProcessor()

holdings = processor.load_all_holdings()
processed = processor.process_holdings(holdings)
summary = processor.get_processing_summary()

if summary.total_excluded > 0:
    logger.warning(
        f"Excluded {summary.total_excluded} holdings",
        extra={"reasons": summary.exclusion_reasons}
    )
    
    # Include in report
    report += f"\n⚠️ {summary.total_excluded} holdings excluded:\n"
    for reason, count in summary.exclusion_reasons.items():
        report += f"- {reason}: {count}\n"
```

### Scenario 5: Mixed Data Availability

**Problem**: Some data sources available, others not.

**Solution**:

```python
tracker = DataAvailabilityTracker()

# Track all sources
tracker.track_data_source("sentiment", "available", age_hours=2)
tracker.track_data_source("sec_filings", "unavailable", age_hours=0)
tracker.track_data_source("portfolio", "available", age_hours=1)
tracker.track_data_source("discovery", "not_run", age_hours=0)
tracker.track_data_source("backtesting", "available", age_hours=168)

# Generate summary
summary = tracker.get_availability_summary()

# Include in report footer
report += f"\n## Data Availability\n"
report += f"- Available: {summary.available_sources}/{summary.total_sources}\n"
report += f"- Unavailable: {summary.unavailable_sources}\n"
report += f"- Stale: {summary.stale_sources}\n"

# Add warnings
warnings = tracker.get_freshness_warnings()
if warnings:
    report += f"\n### Freshness Warnings\n"
    for warning in warnings:
        report += f"- ⚠️ {warning}\n"
```

## Testing Data Quality

### Unit Tests

Test each component independently:

```python
def test_should_return_none_when_no_filings_available(mocker):
    """Test SEC URL generator returns None for missing filings."""
    # Arrange
    generator = SECFilingURLGenerator()
    mocker.patch.object(generator, '_get_cik', return_value=None)
    
    # Act
    url = generator.get_filing_url("INVALID", "10-K")
    
    # Assert
    assert url is None

def test_should_process_all_holdings_including_invalid(mocker):
    """Test processor includes all holdings."""
    # Arrange
    processor = PortfolioHoldingsProcessor()
    holdings = [
        {"ticker": "AAPL", "valid": True},
        {"ticker": "INVALID", "valid": False}
    ]
    
    # Act
    processed = processor.process_holdings(holdings)
    
    # Assert
    assert len(processed) == 2  # Both included
```

### Integration Tests

Test data quality in full reports:

```python
def test_should_not_hallucinate_urls_in_report():
    """Test report contains no fake URLs."""
    # Arrange
    report = generate_report(ticker="AAPL")
    
    # Assert
    assert "example.com" not in report
    assert "test.com" not in report
    assert "localhost" not in report

def test_should_include_all_portfolio_holdings():
    """Test report includes all holdings from CSV."""
    # Arrange
    csv_holdings = load_csv_holdings()
    report = generate_portfolio_report()
    
    # Assert
    for holding in csv_holdings:
        assert holding.ticker in report
```

## Troubleshooting

### Issue: URLs returning 404

**Cause**: Hardcoded or outdated SEC URLs.

**Solution**: Use `SECFilingURLGenerator` with verification.

### Issue: Holdings missing from report

**Cause**: Silent exclusion of invalid holdings.

**Solution**: Use `PortfolioHoldingsProcessor` to process all holdings.

### Issue: "Données non disponibles" in metrics

**Cause**: Using strings instead of None for missing data.

**Solution**: Use `float | None` and format for display.

### Issue: No A+ opportunities shown

**Cause**: Discovery not run or results not loaded.

**Solution**: Use `APlusDiscoveryAccessor` to check and load results.

### Issue: Stale data not flagged

**Cause**: No freshness tracking.

**Solution**: Use `DataAvailabilityTracker` to track and warn.

## See Also

- [API Reference](API_REFERENCE.md) - Component documentation
- [Developer Guide](DEVELOPER_GUIDE.md) - Development standards
- [Architecture Guide](ARCHITECTURE.md) - System design
- [Report Data Quality Fixes Spec](.kiro/specs/report-data-quality-fixes/) - Implementation details

---

**Version**: 1.0  
**Last Updated**: 2025-01-07
