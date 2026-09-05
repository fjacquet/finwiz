# Troubleshooting Guide

Comprehensive troubleshooting guide for common FinWiz issues and their solutions.

## Prerequisites

- FinWiz installed and configured
- Basic familiarity with FinWiz concepts
- Access to log files and error messages

## Overview

This guide covers common issues you may encounter when using FinWiz, including CrewAI Flow errors, template rendering problems, schema mismatches, and data structure issues.

---

## CrewAI Flow Execution Errors

### Schema Validation Failures

**Problem**: Deep analysis results failing validation with schema mismatch errors

**Symptoms**:

```
Validation failed for output/stock/AAPL_default.json against DeepAnalysisCrewExport
```

**Root Cause**: Python analyzer output doesn't match CrewAI schema structure

**Solution**: Use the correct schema for Python-based analysis

The system now supports both schemas:

- `PythonDeepAnalysisResult` - For Python-based deep analysis
- `DeepAnalysisCrewExport` - For CrewAI crew analysis

The consolidator automatically detects which schema to use based on the `crew_name` field.

**Verification**:

```bash
# Check that all analyses validate
grep "Validation failed" logs/flow_execution.log
# Should return no results
```

---

### Investment Discovery Crew Initialization Failure

**Problem**: Discovery crew fails to initialize with `KeyError: True`

**Symptoms**:

```
KeyError: True
  in CrewAI task variable mapping
```

**Root Cause**: Invalid `output_json: true` in task configuration

**Explanation**:

- `output_json` should be a Pydantic model class name (e.g., `output_pydantic: FeedbackLearningResult`)
- OR omitted entirely for JSON file output
- Setting it to `true` (boolean) causes CrewAI to look for a model named `True`

**Solution**: Remove or fix the `output_json` configuration

```yaml
# WRONG
feedback_learning_task:
  output_json: true  # ❌ Invalid

# CORRECT (Option 1: Use Pydantic model)
feedback_learning_task:
  output_pydantic: FeedbackLearningResult

# CORRECT (Option 2: Omit for JSON file output)
feedback_learning_task:
  output_file: "output/discovery/feedback_learning_report.json"
```

---

### Consolidated Report Field Errors

**Problem**: Consolidator trying to set fields that don't exist in schema

**Symptoms**:

```
"ConsolidatedReportExport" object has no field "backtesting_data"
"ConsolidatedReportExport" object has no field "portfolio_data"
```

**Root Cause**: Schema missing optional fields for additional data

**Solution**: Schema has been updated with optional fields:

```python
class ConsolidatedReportExport(BaseModel):
    # ... existing fields ...
    portfolio_data: Optional[dict[str, Any]] = None
    aplus_opportunities: Optional[dict[str, Any]] = None
    backtesting_data: Optional[dict[str, Any]] = None
```

**Verification**:

```bash
# Check consolidated report generation
cat output/reports/*/consolidated_report.json | jq '.deep_analyses | length'
# Should show total number of holdings
```

---

## Template Rendering Issues

### Handling CrewAI Output Format Mismatches

**Problem**: HTML templates render with empty/default values despite having rich data in JSON

**Symptoms**:

- Discovery date shows as "N/A"
- Total opportunities shows as 0
- Candidate details are missing

**Root Cause**: Data structure mismatch between JSON format and template expectations

CrewAI outputs use nested structure:

```json
{
  "raw_output": "...",
  "json_dict": null,
  "pydantic": {
    "opportunities": [...],      // <-- Actual data here
    "analysis_date": "2025-10-27T00:00:00Z"
  }
}
```

Templates looking for data at root level instead of inside `pydantic` field.

**Solution**: Extract data from the `pydantic` field before use. There is
no `template_renderer.py` or `render_discovery_latest` method in the
codebase — the real unwrapping logic lives in
`src/finwiz/orchestrators/reporting/data_loading.py:78-94`, which
branches on cache format (`{"analysis": {...}}`), CrewAI format
(`{"pydantic": {...}}`), and direct/enriched format:

```python
# src/finwiz/orchestrators/reporting/data_loading.py (actual code, condensed)
if "analysis" in data and isinstance(data["analysis"], dict):
    analysis_data = data["analysis"]  # cache format
elif "pydantic" in data and isinstance(data["pydantic"], dict):
    analysis_data = data["pydantic"]  # CrewAI format
else:
    analysis_data = data  # direct or enriched format
```

**Field Mapping Fixes**:

- `discovery_date` → `analysis_date` (with fallback)
- `discovery_criteria` → `screening_criteria` (with fallback)
- Add `market_context` and `data_sources` fields

**Date Parsing**:

```python
# Parse discovery date if it's a string
discovery_date_str = data.get("analysis_date") or data.get("discovery_date")
if discovery_date_str and isinstance(discovery_date_str, str):
    from dateutil import parser

    discovery_date = parser.parse(discovery_date_str)
```

---

### Template Schema Compatibility

**Problem**: Template crashes when rendering different schema types

**Symptoms**:

```
jinja2.exceptions.UndefinedError: 'PythonDeepAnalysisResult object' has no attribute 'risk_assessment'
```

**Root Cause**: Templates trying to access nested objects that don't exist in Python schemas

**Schema Differences** (corrected — the class/field names below were
wrong in an earlier version of this doc):

`TenKInsight` (`src/finwiz/schemas/stock.py`) has no `risk_assessment`
field at all — its fields are `schema_version`, `ticker`, `filing_url`,
`filed_at`, `section`, `excerpt`, `sec_citation` (and it's
`extra="forbid"`, so an unlisted field would be rejected outright, not
silently absent). The schema that actually carries a `risk_assessment`
field is the crew export schema (e.g. `StockCrewExport`,
`DeepAnalysisCrewExport` in `src/finwiz/schemas/crew_exports.py`):

```python
# Crew export schema (e.g. StockCrewExport, DeepAnalysisCrewExport)
class StockCrewExport(CrewExportBase):
    risk_assessment: RiskAssessmentStandardized  # Nested object
    # RiskAssessmentStandardized.score is 0-5 scale, not 0-10 (see
    # src/finwiz/schemas/common.py:41 — there is no `risk_score` attribute)


# Python Schema (PythonDeepAnalysisResult)
class PythonDeepAnalysisResult(BaseModel):
    risk_score: float | None  # Direct field, 0-1 scale
    # No nested risk_assessment object
```

**Solution**: Template handles both schema types gracefully

{% raw %}

```html
<!-- Handle both CrewAI and Python schemas -->
<div class="metric-card">
    <h4>Risque</h4>
    {% if analysis.risk_assessment is defined and analysis.risk_assessment %}
    <!-- CrewAI schema: nested object, 0-5 scale (RiskAssessmentStandardized.score) -->
    <div class="metric-value risk-{{ 'low' if analysis.risk_assessment.score <= 1.5 else ('medium' if analysis.risk_assessment.score <= 3 else 'high') }}">
        {{ analysis.risk_assessment.score }}/5
    </div>
    {% elif analysis.risk_score is defined and analysis.risk_score is not none %}
    <!-- Python schema: direct field, 0-1 scale, convert to 0-5 to match the CrewAI scale above -->
    <div class="metric-value risk-{{ 'low' if analysis.risk_score <= 0.3 else ('medium' if analysis.risk_score <= 0.6 else 'high') }}">
        {{ "%.1f"|format(analysis.risk_score * 5) }}/5
    </div>
    {% else %}
    <!-- Fallback if neither exists -->
    <div class="metric-value">N/A</div>
    {% endif %}
</div>
```

{% endraw %}

**Key Techniques**:

1. **Conditional checks**: {% raw %}`{% if field is defined %}`{% endraw %}
2. **Fallback logic**: {% raw %}`{% elif alternative_field %}`{% endraw %}
3. **Scale conversion**: `risk_score * 5` (0-1 → 0-5, matching `RiskAssessmentStandardized.score`)
4. **Graceful degradation**: Show "N/A" if data unavailable

---

### Template Attribute vs Dict Access

**Problem**: Template fails with attribute access errors

**Symptoms**:

```
'dict' object has no attribute 'ticker'
```

**Root Cause**: Template using attribute access (`.`) on dict objects

**Solution**: Use dict access (`[]`) or `.get()` method

{% raw %}

```html
<!-- WRONG: Attribute access (fails on dicts) -->
{{ candidate.ticker }}

<!-- CORRECT: Dict access (works on dicts) -->
{{ candidate['ticker'] }}

<!-- BEST: Safe access with default -->
{{ candidate.get('ticker', 'N/A') }}
```

{% endraw %}

**Smart Rationale Generation — NOT IMPLEMENTED**:

An earlier version of this document showed a `_generate_rationale()`
function in a `template_renderer.py` that combined per-asset-class fields
(`competitive_moat`, `tokenomics_summary`, etc.) into a rationale string.
Neither that file nor that function exists anywhere in `src/` or `tests/`
— this was aspirational, not real. Rationale strings for discovery
candidates come from elsewhere in the pipeline (see
`src/finwiz/orchestrators/discovery/extractors/base.py` and
`src/finwiz/orchestrators/portfolio_review/decisions.py:build_rationale`
for the actual rationale-building code, which does not do this
moat/tokenomics field-combining).

---

## Data Structure Issues

### Missing Flow State Fields

**Problem**: Flow execution crashes with missing state fields

**Symptoms**:

```
AttributeError: 'StateWithId' object has no attribute 'errors'
```

**Root Cause**: Flow state Pydantic model missing fields that orchestrator tries to use

**Solution**: Add missing fields to state model

```python
# In flow_state.py
class FinwizState(BaseModel):
    # ... existing fields ...

    # Error tracking
    errors: list[str] = Field(default_factory=list, description="List of error messages from flow execution")
    failed_holdings: list[str] = Field(default_factory=list, description="List of tickers that failed analysis")
    retry_counts: dict[str, int] = Field(default_factory=dict, description="Retry count per ticker")
    timeout_holdings: list[str] = Field(default_factory=list, description="List of tickers that timed out")
```

**Usage in Flow**:

```python
# Now this works without AttributeError
self.state.errors.append(f"Analysis failed for {ticker}: {error}")
```

---

## Testing Issues

### Pre-commit Hook False Positives

**Problem**: Pre-commit hook blocks commits with false positive for `unittest.mock`

**Symptoms**:

```
❌ Check for unittest.mock usage........................Failed
- hook id: check-unittest-mock
- exit code: 1

scripts/fix_all_broken_links.py:
- **Testing**: pytest with pytest-mock (unittest.mock banned)
```

**Root Cause**: Regex pattern too broad, matching documentation strings

**Original Pattern** (too broad):

```bash
grep -r "from unittest.mock\|import unittest.mock" tests/
```

This matched:

- ✅ Actual imports: `from unittest.mock import Mock`
- ❌ Documentation: `"unittest.mock banned"`
- ❌ Comments: `# unittest.mock is not allowed`

**Solution**: Use precise regex for import statements only

```yaml
# In .pre-commit-config.yaml
entry: bash -c 'if grep -E "^[[:space:]]*(from unittest\.mock|import unittest\.mock)" tests/ -r 2>/dev/null; then ...'
```

**Pattern Breakdown**:

- `^[[:space:]]*` - Match start of line with optional whitespace
- `-E` - Use extended regex
- `\.` - Escaped dots for literal matching

**Testing**:

```bash
# Test on actual imports (should fail)
echo "from unittest.mock import Mock" > /tmp/test.py
grep -E "^[[:space:]]*(from unittest\.mock|import unittest\.mock)" /tmp/test.py
# Result: Match found ✅

# Test on documentation (should pass)
echo '- **Testing**: pytest with pytest-mock (unittest.mock banned)' > /tmp/test.py
grep -E "^[[:space:]]*(from unittest\.mock|import unittest\.mock)" /tmp/test.py
# Result: No match ✅
```

---

## Advanced Troubleshooting

## Next Steps

- [Related How-to Guide](setup_environment.md)
- [Reference Documentation](../reference/index.md)
- [Tutorials](../tutorials/index.md)

## See Also

- Related documentation links
- External resources
