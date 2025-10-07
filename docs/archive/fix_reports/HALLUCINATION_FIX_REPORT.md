# FinWiz Hallucination Issue - Root Cause & Fix

## Issue Summary

The HTML report (`output/finwiz_family_financial_plan.html`) contains hallucinated ticker symbols (ABC, LMN, XYZ) with fake company names and fabricated SEC filings, breaking all trust in the system.

## Root Cause Analysis

### 1. **Corrupted JSON Output Files**

The stock/ETF/crypto crew output files are corrupted and contain raw LLM text instead of properly structured JSON:

```bash
# Example from stock_output_20251003_113716.json:
"raw": "Analysis current as of 2025-10-03 (concise, evidence-backed)..."
```

This is NOT valid JSON data - it's the raw text output from the LLM.

### 2. **JSON Parsing Failures**

The error logs show repeated JSON decode errors:

```text
JSONDecodeError: Expecting value: line 31 column 21 (char 86205)
```

The integration manager cannot parse these files because they contain malformed JSON.

### 3. **Data Integration Failure**

When the report crew tries to read upstream data:

- `get_crew_data_with_freshness_check()` fails for stock, ETF, and crypto crews
- The report crew has NO access to verified ticker data
- The consolidated reporter input is empty or contains error messages

### 4. **LLM Hallucination**

Without verified data, the report crew's LLM agents:

- Fabricate ticker symbols: ABC, LMN, XYZ
- Invent company names: "Alpha Beta Corp", "Lumina Networks", "Xylon Holdings"
- Create fake SEC filings with fake URLs and dates
- Generate completely fictional 10-K excerpts

## Evidence

### From the HTML Report

```html
<li>ABC — <strong>Ticker validé</strong> — allocation recommandée : 8 % (80 CHF/mois)</li>
<li>LMN — <strong>Ticker validé</strong> — allocation recommandée : 6 % (60 CHF/mois)</li>
<li>XYZ — <strong>Ticker validé</strong> — allocation recommandée : 4 % (40 CHF/mois)</li>

<strong>ABC — Alpha Beta Corp — Form 10‑K (déposé 2025‑02‑20)</strong><br>
URL : <a href="https://www.sec.gov/ix?doc=/Archives/edgar/data/0001234567/000123456725000012/abc-20241231x10k.htm">
```

### From Error Logs

```text
2025-10-02 08:39:03 - Failed to get data for stock crew: Expecting value: line 31 column 21
2025-10-02 08:39:03 - Failed to get data for etf crew: Expecting value: line 22 column 18
2025-10-02 08:39:03 - Failed to get data for crypto crew: Expecting value: line 110 column 18
```

### From Actual JSON Files

The files contain raw text like:

```text
"raw": "Analysis current as of 2025-10-03...\n\nExecutive summary (top 5 sectors to watch..."
```

Instead of structured data like:

```json
{
  "validated_tickers": ["AAPL", "MSFT", "GOOGL"],
  "recommendations": [...]
}
```

## The Fix

### Immediate Actions Required

1. **Fix JSON Serialization in Integration Manager**
   - The `_save_json_file()` method needs to properly serialize CrewOutput objects
   - Ensure `usage_metrics` and `datetime` objects are converted to JSON-serializable formats
   - The custom `json_serializer` exists but may not be applied correctly

2. **Extract Structured Data from Crew Outputs**
   - Use `crew_output.pydantic.model_dump()` or `crew_output.json_dict` instead of `crew_output.raw`
   - The `raw` field contains unstructured LLM text and should only be used for logging
   - Store validated tickers, recommendations, and analysis in structured fields

3. **Add Validation Before Report Generation**
   - The report crew should validate that upstream data exists and is parseable
   - If data is missing or corrupted, the report crew should FAIL with a clear error message
   - NEVER allow the LLM to hallucinate data when real data is unavailable

4. **Implement Data Contracts**
   - Define strict Pydantic schemas for crew outputs
   - Validate all crew outputs against schemas before saving
   - Reject outputs that don't conform to the schema

### Code Changes Needed

#### 1. Fix `store_crew_output` in `src/finwiz/integration/manager.py`

```python
# BEFORE (current - stores raw text):
output_data = {
    "raw_output": str(crew_output.raw),  # ❌ This is unstructured text!
    "json_dict": crew_output.json_dict,
    "pydantic": crew_output.pydantic.model_dump() if crew_output.pydantic else {},
}

# AFTER (should prioritize structured data):
output_data = {
    "structured_output": crew_output.pydantic.model_dump() if crew_output.pydantic else crew_output.json_dict,
    "raw_output": str(crew_output.raw),  # Keep for debugging only
    "validated_tickers": extract_validated_tickers(crew_output),  # Extract structured data
    "recommendations": extract_recommendations(crew_output),
}
```

#### 2. Fix `_save_json_file` to use the custom serializer

```python
def _save_json_file(self, file_path: Path, data: dict) -> None:
    """Save data to JSON file with proper serialization."""
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=self.json_serializer)
```

#### 3. Add validation in report crew before generation

```python
def prepare_crew_context(self, max_age_hours: int = 24) -> dict[str, Any]:
    integrated_context = self.get_integrated_data_context(max_age_hours)

    # CRITICAL: Validate that we have real data
    if not integrated_context.get("validated_tickers"):
        raise ValueError(
            "Cannot generate report: No validated tickers found in upstream data. "
            "This would result in hallucinated recommendations."
        )

    if integrated_context.get("error") or integrated_context.get("fallback_mode"):
        raise ValueError(
            f"Cannot generate report: Data integration failed. "
            f"Error: {integrated_context.get('error')}"
        )

    return integrated_context
```

#### 4. Update report crew task instructions

Add to `src/finwiz/crews/report_crew/config/tasks.yaml`:

```yaml
comprehensive_investment_report_task:
  description: |
    CRITICAL RULE: You MUST ONLY use ticker symbols from the validated_tickers[] array
    in the integrated data context. DO NOT invent or hallucinate ticker symbols.

    If validated_tickers is empty or missing, you MUST fail the task with an error message.
    DO NOT proceed with report generation if you don't have verified ticker data.

    Verified data sources:
    - inputs.validated_tickers[] - ONLY use tickers from this list
    - inputs.stock_recommendations[] - Use these recommendations
    - inputs.etf_recommendations[] - Use these recommendations

    NEVER use placeholder tickers like ABC, XYZ, LMN, or any ticker not in validated_tickers[].
```

## Prevention Measures

1. **Add Integration Tests**
   - Test that corrupted JSON files cause the report crew to fail (not hallucinate)
   - Test that missing upstream data causes graceful failure
   - Test that only validated tickers appear in reports

2. **Add Monitoring**
   - Alert when JSON parsing fails
   - Alert when report crew generates tickers not in validated_tickers[]
   - Track data freshness and alert on stale data

3. **Add Schema Validation**
   - Validate all crew outputs against Pydantic schemas
   - Reject outputs that don't match expected structure
   - Log validation failures for debugging

4. **Improve Error Messages**
   - When data is missing, provide clear error messages
   - Don't let LLMs "fill in the gaps" with hallucinated data
   - Fail fast and fail loud when data integrity is compromised

## Testing the Fix

After implementing the fixes, verify:

1. ✅ JSON files in `output/stock/`, `output/etf/`, `output/crypto/` are valid JSON
2. ✅ JSON files contain `validated_tickers[]` arrays with real ticker symbols
3. ✅ Report crew can parse the JSON files without errors
4. ✅ Generated HTML report contains ONLY tickers from `validated_tickers[]`
5. ✅ No hallucinated company names or fake SEC filings
6. ✅ All SEC citations reference real filings with verifiable URLs

## Conclusion

The hallucination issue is caused by a data pipeline failure, not an LLM problem. The LLMs are doing what they're designed to do - generate plausible-sounding content when given insufficient context. The fix is to ensure the data pipeline provides verified, structured data and fails gracefully when data is unavailable, rather than allowing hallucination.

**Priority: CRITICAL** - This breaks trust in the entire system and could lead to catastrophic investment decisions based on fake data.
