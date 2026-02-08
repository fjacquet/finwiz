# Quick Start: Data Quality Verification

## Run Verification

```bash
./scripts/verify_data_quality.sh
```

## Interpret Results

### ✅ Success (Exit Code 0)

```
✅ ALL CHECKS PASSED
Data quality is excellent. All crew outputs are being properly consumed.
```

**Action**: None needed. System is working correctly.

### ⚠️ Warnings (Exit Code 0)

```
⚠️ CHECKS PASSED WITH WARNINGS
Data quality is acceptable but has some issues. Review warnings above.
```

**Action**: Review warnings. System is functional but could be improved.

### ❌ Failure (Exit Code 1)

```
❌ QUALITY CHECKS FAILED
Data quality issues detected. Crew outputs may not be properly consumed.
```

**Action**: Investigate failed checks. Data consumption gap detected.

## Common Issues

### Issue: ALL holdings have fallback Grade D

**Symptom**:

```
❌ FAIL: ALL holdings have fallback Grade D (actual analysis not used)
```

**Cause**: Deep analysis results not merged into portfolio holdings.

**Fix**: Check `DeepAnalysisDataMerger` in `src/finwiz/utils/deep_analysis_merger.py`

### Issue: Placeholder URLs (example.com)

**Symptom**:

```
❌ FAIL: Found 3 example.com placeholder URLs
```

**Cause**: URL generation failing or returning None.

**Fix**: Check URL generation in tools and `URLValidator`

### Issue: NOT PROVIDED messages

**Symptom**:

```
❌ FAIL: Found 3 'NOT PROVIDED' messages
```

**Cause**: Data availability tracking not reporting available data.

**Fix**: Check `DataAvailabilityTracker` and ensure it tracks all sources

## Quality Score Guide

| Score | Grade | Status |
|-------|-------|--------|
| 0.95+ | A+ | Excellent |
| 0.90-0.94 | A | Very Good |
| 0.80-0.89 | B | Good |
| 0.70-0.79 | C | Acceptable |
| 0.60-0.69 | D | Poor |
| <0.60 | F | Failing |

## Quick Commands

```bash
# Run verification
./scripts/verify_data_quality.sh

# Run and save output
./scripts/verify_data_quality.sh > quality_report.txt 2>&1

# Check exit code
./scripts/verify_data_quality.sh && echo "PASSED" || echo "FAILED"

# Run in CI/CD
uv run python src/finwiz/main.py && ./scripts/verify_data_quality.sh
```

## See Full Documentation

For detailed information, see:

- `scripts/README_VERIFY_DATA_QUALITY.md` - Complete documentation
- `TASK_19_VERIFICATION_SCRIPT_SUMMARY.md` - Implementation summary
