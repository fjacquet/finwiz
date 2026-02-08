# Data Quality Verification Script

## Overview

The `verify_data_quality.sh` script verifies that FinWiz crew outputs are properly consumed and not replaced with fallback data. It checks for common data quality issues that indicate the data consumption gap.

## Usage

```bash
# Run verification
./scripts/verify_data_quality.sh

# Check exit code
echo $?
# 0 = All checks passed
# 1 = Quality checks failed
```

## What It Checks

### 1. Crew Outputs Exist

Verifies that crew output files exist in the expected directories:

- `output/stock/stock_output_*.json` - Stock crew analysis
- `output/etf/etf_output_*.json` - ETF crew analysis
- `output/crypto/crypto_output_*.json` - Crypto crew analysis
- `output/portfolio/portfolio_review.json` - Portfolio review

### 2. Portfolio Review Data Quality

Checks the portfolio review for data quality issues:

- **Fallback Grade D Pattern**: Detects holdings with Grade D and composite_score 0.6 (fallback data)
- **Validation Rapide Messages**: Identifies "Validation rapide" messages indicating fallback analysis
- **Grade Distribution**: Shows distribution of grades across holdings

**Expected**: Holdings should have varied grades (A+, A, B, C, D, F) based on actual analysis, not all Grade D.

### 3. Report Quality

Checks the HTML report for data quality issues:

- **Placeholder URLs**: Counts `example.com` URLs (should be 0)
- **NOT PROVIDED Messages**: Counts "NOT PROVIDED" text (should be 0)
- **Missing Alternatives**: Counts "aucune alternative fournie" messages

**Expected**: Report should have real URLs and complete data, not placeholders.

### 4. Data Quality Metrics

Reads the data quality metrics file (if available) and displays:

- Quality score (0-1)
- Quality grade (A+, A, B, C, D, F)
- Fallback grades count
- Placeholder URLs count
- Missing data count
- Successful/failed merges count

## Quality Score Calculation

The script calculates an overall quality score:

```
Quality Score = 1.0 - (penalties)

Penalties:
- Fallback grades: -0.1 per occurrence
- Placeholder URLs: -0.05 per occurrence
- Missing data: -0.05 per occurrence
```

**Thresholds**:

- **0.90+**: Excellent (Grade A+/A)
- **0.80-0.89**: Good (Grade B)
- **0.70-0.79**: Acceptable (Grade C)
- **0.60-0.69**: Poor (Grade D)
- **<0.60**: Failing (Grade F)

## Exit Codes

- **0**: All checks passed (with or without warnings)
- **1**: Quality checks failed (critical issues detected)

## Example Output

### Successful Run

```
==========================================
FinWiz Data Quality Verification
==========================================

1. Checking Crew Outputs
----------------------------------------
✅ PASS: Stock crew output has 6 file(s)
✅ PASS: ETF crew output has 6 file(s)
✅ PASS: Crypto crew output has 6 file(s)
✅ PASS: Portfolio review exists: output/portfolio/portfolio_review.json

2. Checking Portfolio Review Data Quality
----------------------------------------
ℹ️  INFO: Portfolio has 5 holdings
✅ PASS: No fallback Grade D patterns detected

Grade Distribution:
  A+: 2
  A: 1
  B: 1
  C: 1

3. Checking Report Quality
----------------------------------------
✅ PASS: Report found: output/finwiz_family_financial_plan.html
✅ PASS: No example.com placeholder URLs found
✅ PASS: No 'NOT PROVIDED' messages found
✅ PASS: No 'aucune alternative fournie' messages found

4. Checking Data Quality Metrics
----------------------------------------
✅ PASS: Data quality metrics found: .finwiz/metrics/data_quality_metrics_20251018_120000.json

Quality Metrics:
  Score: 0.95
  Grade: A+
  Fallback Grades: 0
  Placeholder URLs: 0
  Missing Data: 0
  Successful Merges: 5
  Failed Merges: 0

==========================================
Data Quality Summary
==========================================

Quality Score: 1.0

Test Results:
  Total Checks: 12
  Passed: 12
  Failed: 0
  Warnings: 0

✅ ALL CHECKS PASSED

Data quality is excellent. All crew outputs are being properly consumed.
```

### Failed Run

```
==========================================
FinWiz Data Quality Verification
==========================================

1. Checking Crew Outputs
----------------------------------------
✅ PASS: Stock crew output has 6 file(s)
✅ PASS: ETF crew output has 6 file(s)
✅ PASS: Crypto crew output has 6 file(s)
✅ PASS: Portfolio review exists: output/portfolio/portfolio_review.json

2. Checking Portfolio Review Data Quality
----------------------------------------
ℹ️  INFO: Portfolio has 5 holdings
❌ FAIL: ALL holdings have fallback Grade D (actual analysis not used)
⚠️  WARN: 5 holdings have 'Validation rapide' messages (fallback data)

Grade Distribution:
  D: 5

3. Checking Report Quality
----------------------------------------
✅ PASS: Report found: output/finwiz_family_financial_plan.html
❌ FAIL: Found 3 example.com placeholder URLs
❌ FAIL: Found 3 'NOT PROVIDED' messages

4. Checking Data Quality Metrics
----------------------------------------
⚠️  WARN: Data quality metrics file not found (may not have been exported)

==========================================
Data Quality Summary
==========================================

Quality Score: 0.35

Test Results:
  Total Checks: 12
  Passed: 5
  Failed: 3
  Warnings: 2

❌ QUALITY CHECKS FAILED

Data quality issues detected. Crew outputs may not be properly consumed.

Common issues:
  - Fallback Grade D: Deep analysis not merged into portfolio
  - Placeholder URLs: Real URLs not retrieved from tools
  - NOT PROVIDED: Data availability not properly reported

Review the failed checks above and investigate data flow.
```

## Integration with CI/CD

Add to your CI/CD pipeline:

```bash
# Run FinWiz
uv run python src/finwiz/main.py

# Verify data quality
./scripts/verify_data_quality.sh

# Exit code 1 will fail the build if quality checks fail
```

## Troubleshooting

### All Holdings Have Grade D

**Issue**: Portfolio review shows all holdings with Grade D and score 0.6.

**Cause**: Deep analysis results are not being merged into portfolio holdings.

**Fix**: Check `DeepAnalysisDataMerger` in `src/finwiz/utils/deep_analysis_merger.py`.

### Placeholder URLs (example.com)

**Issue**: Report contains `example.com` URLs instead of real URLs.

**Cause**: URL generation is failing or returning None.

**Fix**: Check URL generation in tools and ensure URLs are validated before use.

### NOT PROVIDED Messages

**Issue**: Report shows "NOT PROVIDED" for data that should exist.

**Cause**: Data availability tracking is not properly reporting available data.

**Fix**: Check `DataAvailabilityTracker` and ensure it's tracking all data sources.

### No Data Quality Metrics File

**Issue**: Script warns that metrics file not found.

**Cause**: `DataQualityMetrics.export_to_file()` may not be called.

**Fix**: Ensure flow orchestrator exports metrics at the end of execution.

## Requirements Addressed

This script addresses the following requirements from the regression diagnosis spec:

- **12.6**: Track data quality metrics
- **12.7**: Calculate overall quality score
- **12.8**: Log metrics at end of flow execution
- **12.9**: Export metrics to file for monitoring
- **12.10**: Provide verification of data quality

## Related Files

- `src/finwiz/utils/data_quality_metrics.py` - Data quality metrics tracker
- `src/finwiz/utils/deep_analysis_merger.py` - Deep analysis data merger
- `src/finwiz/flows/flow_orchestrator.py` - Flow orchestrator with metrics integration
- `.finwiz/metrics/` - Directory for exported metrics files

## See Also

- [Data Quality Metrics Integration](../docs/DATA_QUALITY_METRICS_INTEGRATION.md)
- [Task 12 Summary](../TASK_12_DATA_QUALITY_METRICS_SUMMARY.md)
- [Regression Diagnosis Design](../.kiro/specs/regression-diagnosis-and-fix/design.md)
