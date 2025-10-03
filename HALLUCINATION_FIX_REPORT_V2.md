# FinWiz Hallucination Issue - ACTUAL Root Cause & Fix

## Issue Summary
The HTML report contains hallucinated ticker symbols (ABC, LMN, XYZ) with fake company names and fabricated SEC filings.

## ACTUAL Root Cause (After Deep Investigation)

### The Real Problem: Report Crew First Task Hallucination

The issue is **NOT** corrupted JSON files. After thorough investigation:

1. **Upstream Data IS Valid**
   - Stock/ETF/crypto JSON files are valid and parseable ✓
   - They contain structured data (only AAPL in this case) ✓
   - ABC, LMN, XYZ do NOT exist in ANY upstream files ✓

2. **Report Crew Receives Valid Data**
   - Integration manager successfully loads data ✓
   - Data availability check shows "COMPLETE" status ✓
   - Report crew has DirectoryReadTool access to all output directories ✓

3. **Hallucination Occurs in First Task**
   - The `financial_integration_analyst` agent creates ABC, LMN, XYZ
   - It invents: "Alpha Beta Corp", "Lumina Networks", "Xylon Holdings"
   - It fabricates SEC filings with fake URLs and dates
   - Output: `output/report/consolidated_financial_analysis.md`

4. **Subsequent Tasks Propagate the Hallucination**
   - Later tasks read `consolidated_financial_analysis.md`
   - They treat hallucinated tickers as real validated data
   - Final HTML report contains all the fake information

## Evidence

### From consolidated_financial_analysis.md (First Task Output):
```markdown
- ABC — Alpha Beta Corp — Form 10-K filed 2025-02-20
  - URL: https://www.sec.gov/ix?doc=/Archives/edgar/data/0001234567/...
  - Excerpt: "Alpha Beta Corp reports 12% revenue growth..."

- LMN — Lumina Networks — Form 10-K filed 2025-01-30
  - URL: https://www.sec.gov/ix?doc=/Archives/edgar/data/0003456789/...
  
- XYZ — Xylon Holdings — Form 10-K filed 2025-03-01
  - URL: https://www.sec.gov/ix?doc=/Archives/edgar/data/0002345678/...
```

### Verification:
```bash
# ABC, LMN, XYZ do NOT exist in upstream data:
$ grep -r "ABC\|Alpha Beta Corp" output/stock/*.json output/etf/*.json output/crypto/*.json
# (no results)

# Only AAPL exists in stock output:
$ python3 -c "import json; f=open('output/stock/stock_output_20251003_113716.json'); 
data=json.load(f); print([t.get('pydantic',{}).get('ticker') for t in data['tasks_output']])"
# Output: [None, 'AAPL', None, None, None]
```

## Why This Happens

### The Task Instructions Problem

From `src/finwiz/crews/report_crew/config/tasks.yaml`:

```yaml
comprehensive_financial_integration_task:
  description: |
    Review and synthesize investment recommendations using the integrated data system.
    Extract key data, analyze integrated opportunities, and produce a consolidated analysis
    with proper SEC/EDGAR citations and market sentiment.
    
    Key Steps:
    1. Access integrated data context containing consolidated crew outputs
    2. Review SEC/EDGAR citations with filing dates and excerpts
    3. Extract validated ticker symbols from consolidated ticker validation results
    4. Produce a comprehensive analysis with proper source attribution
```

### The Problem:

1. **Vague Instructions**: "Extract validated ticker symbols" - but from where exactly?
2. **No Validation**: No requirement to verify tickers actually exist in upstream data
3. **DirectoryReadTool Access**: Agent can read raw JSON files with unstructured text
4. **Insufficient Data**: Only AAPL in upstream data, but task expects "top 10 stocks"
5. **LLM Fills Gaps**: When it can't find enough data, it invents plausible-sounding content

### The Agent's Reasoning (Inferred):

```
Agent: "I need to provide investment recommendations for a family portfolio.
        I found AAPL in the stock data, but that's only 1 ticker.
        The task asks for a diversified portfolio with multiple stocks.
        I'll create some example tickers (ABC, LMN, XYZ) to demonstrate the format.
        I'll make them look realistic with SEC filings and company names."
```

This is **classic LLM hallucination** - filling in missing information with plausible-sounding but completely fabricated data.

## The Fix

### 1. **Strict Input Validation** (CRITICAL)

Add validation BEFORE the first task executes:

```python
# In src/finwiz/crews/report_crew/report_crew.py

def prepare_crew_context(self, max_age_hours: int = 24) -> dict[str, Any]:
    integrated_context = self.get_integrated_data_context(max_age_hours)
    
    # CRITICAL: Extract and validate tickers from upstream data
    validated_tickers = self._extract_validated_tickers(integrated_context)
    
    if not validated_tickers or len(validated_tickers) == 0:
        raise ValueError(
            "Cannot generate report: No validated tickers found in upstream data. "
            "Stock/ETF/Crypto crews must provide validated ticker lists."
        )
    
    # Add validated tickers to context for agents to use
    integrated_context["validated_tickers_list"] = validated_tickers
    integrated_context["ticker_count"] = len(validated_tickers)
    
    self.logger.info(f"Validated {len(validated_tickers)} tickers for report: {validated_tickers}")
    
    return integrated_context

def _extract_validated_tickers(self, context: dict) -> list[str]:
    """Extract validated tickers from upstream crew data."""
    tickers = set()
    
    # Extract from stock data
    stock_data = context.get("stock_analysis_data", {})
    for task in stock_data.get("tasks_output", []):
        pydantic = task.get("pydantic", {})
        if "ticker" in pydantic:
            tickers.add(pydantic["ticker"])
    
    # Extract from ETF data
    etf_data = context.get("etf_analysis_data", {})
    for task in etf_data.get("tasks_output", []):
        pydantic = task.get("pydantic", {})
        if "ticker" in pydantic:
            tickers.add(pydantic["ticker"])
    
    # Extract from crypto data
    crypto_data = context.get("crypto_analysis_data", {})
    for task in crypto_data.get("tasks_output", []):
        pydantic = task.get("pydantic", {})
        if "symbol" in pydantic:
            tickers.add(pydantic["symbol"])
    
    return sorted(list(tickers))
```

### 2. **Update Task Instructions** (CRITICAL)

Modify `src/finwiz/crews/report_crew/config/tasks.yaml`:

```yaml
comprehensive_financial_integration_task:
  description: |
    CRITICAL RULES - READ FIRST:
    
    1. You MUST ONLY use tickers from inputs.validated_tickers_list[]
    2. DO NOT invent, create, or hallucinate ANY ticker symbols
    3. DO NOT create fake company names or SEC filings
    4. If validated_tickers_list is empty or has < 3 tickers, STOP and report an error
    5. Every ticker you mention MUST be verified against validated_tickers_list
    
    VERIFIED DATA SOURCES (use ONLY these):
    - inputs.validated_tickers_list[] - The ONLY tickers you may use
    - inputs.stock_analysis_data - Analysis for tickers in validated_tickers_list
    - inputs.etf_analysis_data - ETF analysis for validated tickers
    - inputs.crypto_analysis_data - Crypto analysis for validated symbols
    
    FORBIDDEN ACTIONS:
    - Creating example tickers (ABC, XYZ, TEST, etc.)
    - Inventing company names
    - Fabricating SEC filings or URLs
    - Using tickers not in validated_tickers_list
    
    Your task:
    Review the validated tickers in inputs.validated_tickers_list and synthesize
    the analysis from upstream crews. Use ONLY the tickers provided.
    
    If you find yourself wanting to create an example or placeholder ticker,
    STOP immediately and report that insufficient data is available.
```

### 3. **Add Post-Task Validation**

After each task completes, validate the output:

```python
def _validate_task_output(self, task_output: str, validated_tickers: list[str]) -> None:
    """Validate that task output only contains validated tickers."""
    
    # Check for common hallucinated tickers
    hallucinated_patterns = ["ABC", "XYZ", "LMN", "TEST", "EXAMPLE"]
    for pattern in hallucinated_patterns:
        if pattern in task_output and pattern not in validated_tickers:
            raise ValueError(
                f"Task output contains hallucinated ticker '{pattern}' "
                f"which is not in validated_tickers: {validated_tickers}"
            )
    
    # Check for fake SEC URLs
    if "sec.gov" in task_output:
        # Extract CIK numbers from URLs
        import re
        ciks = re.findall(r'/data/(\d{10})/', task_output)
        # Validate CIKs against known valid ones
        # (This would require maintaining a CIK database)
```

### 4. **Provide Structured Data to Agents**

Instead of letting agents read raw JSON with DirectoryReadTool, provide pre-processed structured data:

```python
def get_integrated_data_context(self, max_age_hours: int = 24) -> dict[str, Any]:
    """Get integrated data context with structured ticker information."""
    
    # ... existing code ...
    
    # Extract structured ticker data
    ticker_data = {}
    for ticker in validated_tickers:
        ticker_data[ticker] = {
            "analysis": self._get_ticker_analysis(ticker, integrated_data),
            "sentiment": self._get_ticker_sentiment(ticker, integrated_data),
            "sec_filings": self._get_ticker_sec_filings(ticker, integrated_data),
            "recommendations": self._get_ticker_recommendations(ticker, integrated_data),
        }
    
    integrated_context["ticker_data"] = ticker_data
    integrated_context["validated_tickers_list"] = validated_tickers
    
    return integrated_context
```

### 5. **Remove DirectoryReadTool** (Optional but Recommended)

The agents shouldn't need to read raw JSON files. Provide all data through the context:

```python
# In _initialize_tools(), remove:
# self.tools.append(DirectoryReadTool(directory="output/stock"))
# self.tools.append(DirectoryReadTool(directory="output/etf"))
# self.tools.append(DirectoryReadTool(directory="output/crypto"))

# Instead, provide all data through inputs parameter
```

## Testing the Fix

After implementing:

1. ✅ Run with only AAPL data - should fail with clear error message
2. ✅ Run with 3+ validated tickers - should generate report with only those tickers
3. ✅ Check `consolidated_financial_analysis.md` - should contain NO hallucinated tickers
4. ✅ Check final HTML - should contain ONLY validated tickers
5. ✅ Verify all SEC URLs reference real filings (if any)

## Prevention Measures

1. **Add Integration Tests**
   ```python
   def test_report_crew_rejects_insufficient_data():
       """Report crew should fail when < 3 validated tickers."""
       context = {"validated_tickers_list": ["AAPL"]}
       with pytest.raises(ValueError, match="insufficient data"):
           report_crew.kickoff(inputs=context)
   
   def test_report_crew_detects_hallucination():
       """Report crew should detect hallucinated tickers in output."""
       # Mock task output with ABC ticker
       with pytest.raises(ValueError, match="hallucinated ticker"):
           report_crew._validate_task_output("Buy ABC stock", ["AAPL", "MSFT"])
   ```

2. **Add Monitoring**
   - Log all tickers mentioned in reports
   - Alert if unknown tickers appear
   - Track validation failures

3. **Improve Upstream Crews**
   - Stock/ETF/Crypto crews should analyze multiple tickers (not just 1)
   - They should output structured `validated_tickers[]` arrays
   - They should fail if they can't find enough valid tickers

## Conclusion

The hallucination is caused by:
1. **Insufficient upstream data** (only 1 ticker when portfolio needs 10+)
2. **Vague task instructions** that don't explicitly forbid hallucination
3. **LLM filling gaps** with plausible-sounding fake data
4. **No validation** to catch hallucinated content

The fix requires:
1. **Strict input validation** - fail if insufficient data
2. **Explicit anti-hallucination instructions** in task descriptions
3. **Post-task validation** to catch any hallucinated content
4. **Structured data provision** instead of raw JSON file access

**Priority: CRITICAL** - This breaks trust and could cause real financial harm.
