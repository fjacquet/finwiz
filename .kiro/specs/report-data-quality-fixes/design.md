# Design Document: Report Data Quality Fixes

## Overview

This design addresses the root causes of data quality issues in financial report generation by fixing data at the source. Instead of post-processing validation, we ensure that only valid, real data enters the system.

## Architecture

### High-Level Design

```
Data Sources → Validation Layer → Integration Layer → Report Generation
     ↓              ↓                    ↓                  ↓
  Real APIs    Reject Invalid      Consolidate         Display Real
  SEC EDGAR    Filter Fake         Complete Data       Or "Unavailable"
  News APIs    Verify URLs         Track Freshness     Clear Status
```

### Key Principles

1. **Fail Fast**: Reject invalid data at the source
2. **Transparency**: Clearly communicate when data is unavailable
3. **No Hallucinations**: Never generate fake data to fill gaps
4. **Completeness**: Process all available data
5. **Traceability**: Log all data decisions

## Components and Interfaces

### Component 1: Sentiment Data Validator

**Purpose**: Ensure sentiment analysis uses only real news sources

**Interface**:
```python
class SentimentDataValidator:
    def validate_article(self, article: dict) -> ValidationResult:
        """Validate a single news article."""
        
    def filter_valid_articles(self, articles: list[dict]) -> list[dict]:
        """Filter list to only valid articles."""
        
    def is_valid_url(self, url: str) -> bool:
        """Check if URL is real and accessible."""
```

**Implementation**:
- Check URL format and protocol
- Reject forbidden patterns (example.com, test.com)
- Verify URL is accessible (optional HEAD request)
- Log rejected articles with reasons

### Component 2: SEC Filing URL Generator

**Purpose**: Generate valid, working SEC filing URLs

**Interface**:
```python
class SECFilingURLGenerator:
    def get_filing_url(self, ticker: str, filing_type: str = "10-K") -> str | None:
        """Get valid SEC filing URL for ticker."""
        
    def get_company_browse_url(self, cik: str) -> str:
        """Get SEC company browse page URL."""
        
    def verify_url(self, url: str) -> bool:
        """Verify URL returns 200 status."""
```

**Implementation**:
- Use SEC EDGAR API to get CIK
- Generate browse URL: `https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type={filing_type}`
- Optionally verify URL accessibility
- Return None if no filings available

### Component 3: Portfolio Holdings Processor

**Purpose**: Ensure all holdings from CSV files are processed

**Interface**:
```python
class PortfolioHoldingsProcessor:
    def load_all_holdings(self) -> dict[str, list[Holding]]:
        """Load all holdings from CSV files."""
        
    def process_holdings(self, holdings: list[Holding]) -> list[HoldingAnalysis]:
        """Process all holdings, including failed validations."""
        
    def get_processing_summary(self) -> ProcessingSummary:
        """Get summary of what was processed."""
```

**Implementation**:
- Read stock.csv, etf.csv, crypto.csv
- Process each holding regardless of validation status
- Track successes and failures
- Include all in report with status indicators

### Component 4: A+ Discovery Data Accessor

**Purpose**: Reliably access A+ discovery results

**Interface**:
```python
class APlusDiscoveryAccessor:
    def has_discovery_results(self) -> bool:
        """Check if discovery results exist."""
        
    def load_discovery_results(self) -> APlusDiscoveryResult | None:
        """Load discovery results if available."""
        
    def get_opportunities_summary(self) -> str:
        """Get human-readable summary of opportunities."""
```

**Implementation**:
- Check for output/discovery/ files
- Load and parse discovery results
- Return None if not available
- Provide clear messaging for report

### Component 5: Backtesting Metrics Extractor

**Purpose**: Extract complete backtesting metrics or mark as unavailable

**Interface**:
```python
class BacktestingMetricsExtractor:
    def extract_metrics(self, validation_result: dict) -> BacktestingMetrics | None:
        """Extract all backtesting metrics."""
        
    def get_available_metrics(self, metrics: BacktestingMetrics) -> dict[str, Any]:
        """Get dict of available metrics (None for unavailable)."""
        
    def format_for_display(self, metrics: BacktestingMetrics | None) -> str:
        """Format metrics for report display."""
```

**Implementation**:
- Extract all standard metrics
- Use None for unavailable metrics (not "Données non disponibles")
- Calculate derived metrics if possible
- Provide clear display formatting

### Component 6: Data Availability Tracker

**Purpose**: Track and report data availability and freshness

**Interface**:
```python
class DataAvailabilityTracker:
    def track_data_source(self, source: str, status: str, age_hours: int):
        """Track availability of a data source."""
        
    def get_availability_summary(self) -> DataAvailabilitySummary:
        """Get summary of all data sources."""
        
    def get_freshness_warnings(self) -> list[str]:
        """Get list of freshness warnings."""
```

**Implementation**:
- Track each data source used
- Record success/failure and timestamp
- Calculate data age
- Generate warnings for stale data

## Data Models

### ValidationResult
```python
class ValidationResult(BaseModel):
    is_valid: bool
    reason: str | None
    details: dict[str, Any]
```

### BacktestingMetrics
```python
class BacktestingMetrics(BaseModel):
    annualized_return: float | None
    sharpe_ratio: float | None
    sortino_ratio: float | None
    calmar_ratio: float | None
    max_drawdown: float | None
    win_rate: float | None
    total_trades: int | None
```

### DataAvailabilitySummary
```python
class DataAvailabilitySummary(BaseModel):
    total_sources: int
    available_sources: int
    unavailable_sources: int
    stale_sources: int
    freshness_warnings: list[str]
    source_details: dict[str, SourceStatus]
```

## Error Handling

### Principle: Fail Gracefully

1. **Invalid Data**: Reject and log, don't use
2. **Missing Data**: Return None, don't generate fake data
3. **Failed API Calls**: Log error, continue with available data
4. **Validation Failures**: Include in report with warning

### Error Scenarios

| Scenario | Handling |
|----------|----------|
| Invalid URL | Reject article, log reason |
| SEC filing not found | Return None, show "Not available" |
| Holding validation fails | Include with warning status |
| Discovery not run | Show "Discovery not run" message |
| Backtesting incomplete | Show available metrics, mark others as null |
| Data source timeout | Log error, continue with other sources |

## Testing Strategy

### Unit Tests

- Test each validator independently
- Test URL generation with various inputs
- Test data extraction with complete and incomplete data
- Test error handling for each failure scenario

### Integration Tests

- Test full data flow from source to report
- Test with missing data sources
- Test with invalid data
- Test with stale data

### Contract Tests

- Verify data models match expectations
- Test API response handling
- Verify report generation with various data states

## Implementation Notes

### Phase 1: Data Validation at Source
- Implement validators for each data source
- Add rejection logic for invalid data
- Add logging for all rejections

### Phase 2: Data Availability Tracking
- Implement availability tracker
- Add freshness checking
- Generate availability summaries

### Phase 3: Report Integration
- Update report generation to use validated data
- Add "unavailable" messaging
- Include data availability summary

### Phase 4: Testing and Verification
- Comprehensive testing
- Verify no hallucinations
- Verify complete data processing
