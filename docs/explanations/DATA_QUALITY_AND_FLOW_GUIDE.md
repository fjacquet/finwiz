# Data Flow and Quality Assurance Guide

## Overview

This document provides comprehensive guidance on FinWiz's data flow architecture, quality requirements, error handling, and troubleshooting. It addresses the critical data consumption gap that was fixed in the regression-diagnosis-and-fix specification.

**Last Updated**: 2025-01-18
**Related Spec**: `.kiro/specs/regression-diagnosis-and-fix/`

---

## Table of Contents

1. [Data Quality Requirements](#data-quality-requirements)
2. [Data Flow Architecture](#data-flow-architecture)
3. [Fail-Fast Error Handling](#fail-fast-error-handling)
4. [Data Quality Verification](#data-quality-verification)
5. [Debugging Data Consumption Issues](#debugging-data-consumption-issues)
6. [Troubleshooting Guide](#troubleshooting-guide)

---

## Data Quality Requirements

### Core Principles

FinWiz enforces strict data quality standards to ensure report accuracy and reliability:

1. **No Hallucinations**: Never generate fake data, URLs, or metrics to fill gaps
2. **Fail Fast**: Reject invalid data at the source rather than attempting to fix it downstream
3. **Transparency**: Always communicate when data is unavailable instead of using placeholders
4. **Completeness**: Process all available data, even if some validation checks fail
5. **Traceability**: Every data point must be traceable to its source with valid URLs

### Data Quality Metrics

The system tracks comprehensive quality metrics:

```python
from finwiz.validation.quality_metrics import DataQualityMetrics

metrics = DataQualityMetrics()

# Track various quality indicators
metrics.record_fallback_grade("AAPL")  # When fallback data is used
metrics.record_placeholder_url("example.com")  # When placeholder URLs detected
metrics.record_missing_data("alternatives")  # When expected data is missing
metrics.record_successful_merge("AAPL")  # When data merge succeeds

# Calculate overall quality score (0-1)
quality_score = metrics.get_quality_score()
print(f"Data Quality Score: {quality_score:.2%}")

# Export metrics for monitoring
metrics.export_to_file("data_quality_report.json")
```

### Quality Thresholds

- **Minimum Quality Score**: 90% (0.90)
- **Maximum Fallback Grades**: 0 (when deep analysis exists)
- **Maximum Placeholder URLs**: 0
- **Maximum Missing Data**: 0 (when data should exist)

### Validation at All Boundaries

All data transfers use strict Pydantic v2 models:

```python
from pydantic import BaseModel, Field

class HoldingDecision(BaseModel):
    """Strict validation for holding decisions."""
    ticker: str = Field(..., pattern=r'^[A-Z]{1,5}$')
    grade: str = Field(..., pattern=r'^(A\+|A|B|C|D|F)$')
    composite_score: float = Field(..., ge=0.0, le=1.0)

    model_config = {
        "extra": "forbid",  # Reject unknown fields
        "str_strip_whitespace": True
    }
```

---

## Data Flow Architecture

### Complete Data Flow

The system follows a strict data flow from generation to report:

```
┌─────────────────────────────────────────────────────────────────┐
│                    1. DATA GENERATION                            │
│  Crews generate rich analysis with proper grades and scores     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    2. DATA STORAGE                               │
│  Crew outputs stored in output/{crew_name}/ directories         │
│  - stock_output_*.json                                           │
│  - etf_output_*.json                                             │
│  - crypto_output_*.json                                          │
│  - portfolio_review.json                                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    3. DATA RETRIEVAL                             │
│  DataConsolidationValidator ensures data can be retrieved       │
│  - Validates crew data exists                                    │
│  - Checks data structure integrity                               │
│  - Fails fast if data missing or corrupted                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    4. DATA CONSOLIDATION                         │
│  ReportConsolidator merges crew exports into one report          │
│  - Loads deep analysis exports                                   │
│  - Validates export structure                                    │
│  - Tracks per-crew execution status                              │
│  - Records validation errors in the report                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    5. REPORT GENERATION                          │
│  ReportDataValidator ensures complete inputs                    │
│  - Validates all required fields present                         │
│  - Detects "NOT PROVIDED" placeholders                           │
│  - Checks for fallback Grade D patterns                          │
│  - Refuses to generate report if data incomplete                 │
└─────────────────────────────────────────────────────────────────┘
```

### Data Generation Phase

**Crews**: Stock, ETF, Crypto, Discovery
**Output**: Rich analysis with proper grades, risk assessments, and recommendations

```python
# Example: Stock crew generates detailed analysis
{
    "ticker": "AAPL",
    "grade": "A+",
    "composite_score": 0.95,
    "risk": {
        "score": 2.5,
        "factors": ["Market volatility", "Sector competition"]
    },
    "rationale_bullets": [
        "Strong fundamentals with 25% revenue growth",
        "Excellent profit margins above 25%",
        "Low debt-to-equity ratio of 0.15"
    ],
    "citations": [
        {
            "source": "SEC 10-K Filing",
            "url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000320193",
            "date": "2024-10-31"
        }
    ]
}
```

### Data Storage Phase

**Location**: `output/{crew_name}/`
**Format**: JSON files with timestamps
**Validation**: Pydantic models ensure data integrity

```bash
output/
├── stock/
│   ├── stock_output_20250118_081944.json
│   └── stock_output_20250118_143022.json
├── etf/
│   └── etf_output_20250118_081955.json
├── crypto/
│   └── crypto_output_20250118_082010.json
└── portfolio/
    └── portfolio_review.json
```

### Data Retrieval Phase

**Component**: `DataConsolidationValidator`
**Purpose**: Ensure crew data can be retrieved before processing

```python
from finwiz.validation.consolidation import DataConsolidationValidator

validator = DataConsolidationValidator()

try:
    # Validate all expected crew data exists
    crew_data = validator.validate_crew_data_retrieval(['stock', 'etf', 'crypto'])

    # Data successfully retrieved
    for crew_name, data in crew_data.items():
        print(f"✅ {crew_name}: {len(data)} records")

except DataRetrievalError as e:
    # Fail fast - data missing or corrupted
    logger.error(f"❌ Data retrieval failed: {e}")
    raise
```

### Report Generation Phase

**Component**: `ReportDataValidator`
**Purpose**: Ensure report crew receives complete, validated data

```python
from finwiz.validation.report_data import ReportDataValidator

validator = ReportDataValidator()

try:
    # Validate report inputs
    validator.validate_report_inputs(crew_inputs)
    validator.validate_portfolio_review_data(crew_inputs['portfolio_review'])

    # Generate report with validated data
    report = generate_report(crew_inputs)

except ReportValidationError as e:
    # Fail fast - refuse to generate report with bad data
    logger.error(f"❌ Report validation failed: {e}")
    raise
```

---

## Fail-Fast Error Handling

### Philosophy

**Better to fail loudly and stop execution than to silently degrade and produce misleading reports.**

Users must be able to trust that if they receive a report, it contains accurate data.

### Fail-Fast Components

#### 1. Data Retrieval Validation

```python
# Fails if crew data missing or corrupted
validator.validate_crew_data_retrieval(['stock', 'etf', 'crypto'])
# Raises: DataRetrievalError with detailed diagnostics
```

#### 2. Data Merge Validation

```python
# Fails if deep analysis missing or contains fallback data
merger.merge_deep_analysis_into_holdings(holdings, deep_analysis)
# Raises: DataMergeError with specific ticker and reason
```

#### 3. Report Input Validation

```python
# Fails if required fields missing or contain placeholders
validator.validate_report_inputs(crew_inputs)
# Raises: ReportValidationError with field-level details
```

### Error Messages

All error messages include:

1. **What failed**: Specific operation that failed
2. **Why it failed**: Root cause with details
3. **What was expected**: Expected data structure or values
4. **What was found**: Actual data that caused failure
5. **Remediation**: Steps to fix the issue

**Example Error Message**:

```
DataMergeError: Failed to merge 2 holdings: ['AAPL', 'GOOGL']

Expected: Deep analysis results for all holdings
Found: Deep analysis missing for AAPL, GOOGL
Available tickers: ['MSFT', 'AMZN', 'TSLA']

Remediation:
1. Check if deep analysis crews ran successfully
2. Verify output files exist in output/stock/
3. Check logs for crew execution errors
4. Re-run deep analysis for missing tickers
```

### Graceful Degradation (Optional)

The system MAY continue with graceful degradation ONLY when:

1. **Explicitly configured**: Feature flag enables degradation mode
2. **Clearly marked**: Degraded sections marked with warnings in report
3. **User notified**: Clear communication about degraded data quality

```python
# Enable graceful degradation (not recommended for production)
os.environ["ALLOW_GRACEFUL_DEGRADATION"] = "true"

# Report will include warnings
"""
⚠️ WARNING: This section uses fallback data due to missing deep analysis.
Data quality may be reduced. Re-run with --deep-analysis for full accuracy.
"""
```

---

## Data Quality Verification

### Manual Verification Steps

#### 1. Verify Crew Outputs Exist

```bash
# Check for crew output files
ls -la output/stock/stock_output_*.json
ls -la output/etf/etf_output_*.json
ls -la output/crypto/crypto_output_*.json

# Should see timestamped files
# stock_output_20250118_081944.json
# etf_output_20250118_081955.json
# crypto_output_20250118_082010.json
```

#### 2. Verify Portfolio Review Has Actual Grades

```bash
# Check portfolio review grades
cat output/portfolio/portfolio_review.json | jq '.portfolio_review.holdings[] | {ticker, grade, composite_score}'

# Expected: Grades should be A+, A, B, C, etc. NOT all "D"
# Expected: Scores should vary, NOT all 0.6
```

**Good Output**:

```json
{
  "ticker": "AAPL",
  "grade": "A+",
  "composite_score": 0.95
}
{
  "ticker": "GOOGL",
  "grade": "A",
  "composite_score": 0.88
}
```

**Bad Output** (indicates data consumption issue):

```json
{
  "ticker": "AAPL",
  "grade": "D",
  "composite_score": 0.6
}
{
  "ticker": "GOOGL",
  "grade": "D",
  "composite_score": 0.6
}
```

#### 3. Verify Report Has Real URLs

```bash
# Check for placeholder URLs
grep -c "example.com" output/finwiz_family_financial_plan.html

# Expected: 0 (no placeholder URLs)
```

#### 4. Verify Report Has No "NOT PROVIDED" Messages

```bash
# Check for missing data messages
grep -c "NOT PROVIDED" output/finwiz_family_financial_plan.html

# Expected: 0 (no missing data messages)
```

#### 5. Calculate Data Quality Score

```python
from finwiz.validation.quality_metrics import DataQualityMetrics

# Load metrics from last run
metrics = DataQualityMetrics.load_from_file("data_quality_report.json")

# Get quality score
score = metrics.get_quality_score()
print(f"Data Quality Score: {score:.2%}")

# Expected: ≥ 90%
```

### Continuous Monitoring

Set up continuous monitoring to track data quality over time:

```python
# In your CI/CD pipeline
def test_data_quality_threshold():
    """Ensure data quality meets minimum threshold."""
    metrics = DataQualityMetrics.load_from_file("data_quality_report.json")
    score = metrics.get_quality_score()

    assert score >= 0.90, f"Data quality score {score:.2%} below threshold 90%"
```

---

## Debugging Data Consumption Issues

### Common Symptoms

1. **All holdings show Grade D**: Deep analysis not being consumed
2. **All scores are 0.6**: Fallback data being used
3. **"NOT PROVIDED" in report**: Data availability not tracked
4. **example.com URLs**: URL generation failing
5. **Empty alternatives lists**: Alternative finding not working

### Diagnostic Logging

The system includes comprehensive diagnostic logging to trace data flow:

```python
# Enable diagnostic logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Run analysis
uv run python src/finwiz/main.py

# Check logs for diagnostic output
tail -f logs/finwiz.log
```

### Diagnostic Log Output

```
================================================================================
DEEP ANALYSIS MERGE - DIAGNOSTIC LOGGING
================================================================================
Deep analysis results available: ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA']
  AAPL: Grade A+, Score 0.95, Has deep analysis: True
  GOOGL: Grade A, Score 0.88, Has deep analysis: True
  MSFT: Grade B, Score 0.75, Has deep analysis: True
  AMZN: Grade A, Score 0.85, Has deep analysis: True
  TSLA: Grade C, Score 0.65, Has deep analysis: True

Portfolio holdings BEFORE merge:
  AAPL: Grade D, Score 0.60
  GOOGL: Grade D, Score 0.60
  MSFT: Grade D, Score 0.60
  AMZN: Grade D, Score 0.60
  TSLA: Grade D, Score 0.60

✅ Merged AAPL: Grade A+, Score 0.95
✅ Merged GOOGL: Grade A, Score 0.88
✅ Merged MSFT: Grade B, Score 0.75
✅ Merged AMZN: Grade A, Score 0.85
✅ Merged TSLA: Grade C, Score 0.65

Portfolio holdings AFTER merge:
  AAPL: Grade A+, Score 0.95
  GOOGL: Grade A, Score 0.88
  MSFT: Grade B, Score 0.75
  AMZN: Grade A, Score 0.85
  TSLA: Grade C, Score 0.65

Deep analysis merge complete: 5/5 holdings successfully merged with actual analysis data
================================================================================
```

### Step-by-Step Debugging

#### Step 1: Verify Crew Execution

```bash
# Check if crews ran successfully
grep "crew_complete" logs/finwiz.log

# Expected output:
# {"crew": "StockCrew", "event": "crew_complete", "duration": 45.2}
# {"crew": "ETFCrew", "event": "crew_complete", "duration": 38.5}
# {"crew": "CryptoCrew", "event": "crew_complete", "duration": 42.1}
```

#### Step 2: Verify Data Storage

```bash
# Check if output files were created
ls -lt output/stock/ | head -5
ls -lt output/etf/ | head -5
ls -lt output/crypto/ | head -5

# Verify file contents
cat output/stock/stock_output_*.json | jq '.ticker, .grade, .composite_score'
```

#### Step 3: Verify Data Retrieval

```bash
# Check retrieval logs
grep "DataConsolidationValidator" logs/finwiz.log

# Expected output:
# ✅ Successfully retrieved data for stock
# ✅ Successfully retrieved data for etf
# ✅ Successfully retrieved data for crypto
```

#### Step 4: Verify Data Consolidation

```bash
# Check consolidation logs
grep "Deep analysis consolidation" logs/finwiz.log

# Expected output:
# Deep analysis consolidation: success (5 exports)
```

#### Step 5: Verify Report Generation

```bash
# Check report validation logs
grep "ReportDataValidator" logs/finwiz.log

# Expected output:
# ✅ Report inputs validation passed
# ✅ Portfolio review validation passed: 5 holdings with actual analysis data
```

### Common Issues and Fixes

#### Issue 1: Deep Analysis Not Running

**Symptom**: No deep analysis output files

**Diagnosis**:

```bash
# Check if a per-asset-class analysis crew was skipped
grep "disabled via feature flag" logs/finwiz.log

# Check for crew execution errors
grep "crew_error" logs/finwiz.log
```

**Fix**:

```bash
# Enable stock/etf/crypto analysis explicitly (all default to true)
export FF_STOCK_ANALYSIS=true
export FF_ETF_ANALYSIS=true
export FF_CRYPTO_ANALYSIS=true

# Re-run analysis
uv run python src/finwiz/main.py
```

#### Issue 2: Data Merge Failing

**Symptom**: Holdings still show Grade D after merge

**Diagnosis**:

```bash
# Check merge logs for errors
grep "DataMergeError" logs/finwiz.log

# Check if deep analysis results match holdings
cat output/portfolio/portfolio_review.json | jq '.portfolio_review.holdings[].ticker'
cat output/stock/stock_output_*.json | jq '.ticker'
```

**Fix**:

```python
# Verify ticker matching
holdings_tickers = set(['AAPL', 'GOOGL', 'MSFT'])
analysis_tickers = set(['AAPL', 'GOOGL', 'MSFT'])

missing = holdings_tickers - analysis_tickers
print(f"Missing analysis for: {missing}")

# Re-run deep analysis for missing tickers
```

#### Issue 3: Report Validation Failing

**Symptom**: Report generation fails with validation error

**Diagnosis**:

```bash
# Check validation error details
grep "ReportValidationError" logs/finwiz.log

# Check for missing fields
cat output/portfolio/portfolio_review.json | jq 'keys'
```

**Fix**:

```python
# Ensure all required fields are present
required_fields = [
    "portfolio_review",
    "aplus_opportunities",
    "investment_discovery_structured",
    "validated_tickers_list",
    "discovery_status",
    "backtesting_status",
    "data_availability_summary",
    "data_availability_summary_formatted"
]

# Check which fields are missing
for field in required_fields:
    if field not in crew_inputs:
        print(f"Missing field: {field}")
```

---

## Troubleshooting Guide

### Problem: All Holdings Show Grade D

**Cause**: Deep analysis results not being merged into portfolio

**Solution**:

1. Check if deep analysis ran:

   ```bash
   ls -la output/stock/stock_output_*.json
   ```

2. Check consolidation logs:

   ```bash
   grep "Deep analysis consolidation" logs/finwiz.log
   ```

3. Verify ticker matching:

   ```bash
   # Holdings tickers
   cat output/portfolio/portfolio_review.json | jq '.portfolio_review.holdings[].ticker'

   # Analysis tickers
   cat output/stock/stock_output_*.json | jq '.ticker'
   ```

4. Re-run with diagnostic logging:

   ```bash
   export LOG_LEVEL=DEBUG
   uv run python src/finwiz/main.py
   ```

### Problem: Report Has example.com URLs

**Cause**: URL generation failing, falling back to placeholders

**Solution**:

1. Check URL generation logs:

   ```bash
   grep "SECFilingURLGenerator" logs/finwiz.log
   ```

2. Verify API keys:

   ```bash
   echo $SEC_API_KEY
   echo $ALPHA_VANTAGE_API_KEY
   ```

3. Test URL generation manually:

   ```python
   from finwiz.tools.sec_filing_url_generator import SECFilingURLGenerator

   generator = SECFilingURLGenerator()
   url = generator.get_filing_url("AAPL", "10-K")
   print(f"Generated URL: {url}")
   ```

4. Check URL validator:

   ```python
   from finwiz.validation.url import URLValidator

   validator = URLValidator()
   is_valid = validator.validate_url("https://www.sec.gov/...")
   print(f"URL valid: {is_valid}")
   ```

### Problem: Report Shows "NOT PROVIDED"

**Cause**: Data availability not being tracked or reported

**Solution**:

1. Check data availability tracking:

   ```bash
   grep "DataAvailabilityTracker" logs/finwiz.log
   ```

2. Verify data sources:

   ```python
   from finwiz.integration.data_availability_tracker import DataAvailabilityTracker

   tracker = DataAvailabilityTracker()
   summary = tracker.get_availability_summary()
   print(summary)
   ```

3. Check report inputs:

   ```bash
   cat output/portfolio/portfolio_review.json | jq '.data_availability_summary'
   ```

### Problem: Empty Alternatives Lists

**Cause**: Alternative finding not working or not being passed to report

**Solution**:

1. Check alternative finder logs:

   ```bash
   grep "AlternativeFinder" logs/finwiz.log
   ```

2. Verify alternatives in portfolio:

   ```bash
   cat output/portfolio/portfolio_review.json | jq '.portfolio_review.holdings[].alternatives'
   ```

3. Test alternative finder manually:

   ```python
   from finwiz.tools.alternative_finder_tool import AlternativeFinder

   finder = AlternativeFinder()
   alternatives = finder.find_alternatives(holding)
   print(f"Found {len(alternatives)} alternatives")
   ```

### Problem: Data Quality Score Below 90%

**Cause**: Multiple data quality issues

**Solution**:

1. Load quality metrics:

   ```python
   from finwiz.validation.quality_metrics import DataQualityMetrics

   metrics = DataQualityMetrics.load_from_file("data_quality_report.json")
   print(metrics.get_summary())
   ```

2. Identify specific issues:

   ```python
   if metrics.fallback_grades_count > 0:
       print(f"⚠️ {metrics.fallback_grades_count} fallback grades detected")

   if metrics.placeholder_urls_count > 0:
       print(f"⚠️ {metrics.placeholder_urls_count} placeholder URLs detected")

   if metrics.missing_data_count > 0:
       print(f"⚠️ {metrics.missing_data_count} missing data points detected")
   ```

3. Fix each issue individually using the solutions above

### Problem: Crew Execution Hangs

**Cause**: Infinite reasoning loops or API timeouts

**Solution**:

1. Check for reasoning loops:

   ```bash
   grep "reasoning_attempt" logs/finwiz.log | tail -20
   ```

2. Set reasoning limits:

   ```python
   # In crew configuration
   agent = Agent(
       reasoning=True,
       max_reasoning_attempts=3  # Prevent infinite loops
   )
   ```

3. Set API timeouts:

   ```python
   import httpx

   async with httpx.AsyncClient(timeout=30.0) as client:
       response = await client.get(url)
   ```

### Problem: Validation Errors

**Cause**: Data doesn't match Pydantic schema

**Solution**:

1. Check validation error details:

   ```bash
   grep "ValidationError" logs/finwiz.log
   ```

2. Verify data structure:

   ```python
   from pydantic import ValidationError
   from finwiz.schemas.portfolio_review import HoldingDecision

   try:
       holding = HoldingDecision(**data)
   except ValidationError as e:
       print(e.json())
   ```

3. Fix data to match schema:

   ```python
   # Ensure all required fields present
   # Ensure field types match
   # Ensure values within valid ranges
   ```

---

## Best Practices

### 1. Always Enable Diagnostic Logging

```bash
export LOG_LEVEL=DEBUG
uv run python src/finwiz/main.py
```

### 2. Verify Data Quality After Each Run

Follow the [Manual Verification Steps](#manual-verification-steps) above after each run.

### 3. Monitor Quality Metrics Over Time

```python
# Track quality trends
metrics_history = []
for run in runs:
    metrics = DataQualityMetrics.load_from_file(f"run_{run}_metrics.json")
    metrics_history.append({
        "run": run,
        "score": metrics.get_quality_score(),
        "fallback_grades": metrics.fallback_grades_count,
        "placeholder_urls": metrics.placeholder_urls_count
    })

# Plot trends
import matplotlib.pyplot as plt
plt.plot([m["score"] for m in metrics_history])
plt.axhline(y=0.90, color='r', linestyle='--', label='Threshold')
plt.title("Data Quality Score Over Time")
plt.show()
```

### 4. Use Fail-Fast in Production

```python
# Never allow graceful degradation in production
os.environ["ALLOW_GRACEFUL_DEGRADATION"] = "false"
```

### 5. Implement Continuous Monitoring

```python
# In CI/CD pipeline
def test_data_quality():
    """Ensure data quality meets standards."""
    metrics = DataQualityMetrics.load_from_file("data_quality_report.json")

    assert metrics.get_quality_score() >= 0.90
    assert metrics.fallback_grades_count == 0
    assert metrics.placeholder_urls_count == 0
    assert metrics.missing_data_count == 0
```

---

## Related Documentation

- **[Data Quality and Flow Guide](DATA_QUALITY_AND_FLOW_GUIDE.md)**: Comprehensive data quality standards
- **[API Reference](../reference/API_REFERENCE.md)**: Data quality component API documentation
- **[Developer Guide](../development/DEVELOPER_GUIDE.md)**: Development standards and patterns
- **[Architecture Guide](ARCHITECTURE.md)**: System architecture overview

---

## Support

For issues or questions:

1. Check this troubleshooting guide
2. Review diagnostic logs
3. Run verification script
4. Check related documentation
5. Open an issue with:
   - Symptom description
   - Diagnostic log output
   - Data quality metrics
   - Steps to reproduce

---

**Version**: 1.0
**Last Updated**: 2025-01-18
**Maintainer**: FinWiz Development Team
