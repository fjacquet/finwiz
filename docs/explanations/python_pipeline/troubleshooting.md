# Troubleshooting Guide

This document provides solutions to common issues encountered when using the Pure Python Pipeline.

## Common Issues

### Issue: All Holdings Have Identical Scores

**Symptom:**

```
ValueError: Score validation failed: All holdings have identical scores (std=0.0000)
```

**Cause:**

The `QuantitativeAnalysisTool` is returning default values instead of real market data for all tickers.

**Diagnosis:**

1. Check if API keys are configured:

   ```bash
   echo $ALPHA_VANTAGE_API_KEY
   echo $TWELVE_DATA_API_KEY
   ```

2. Verify ticker symbols are valid:

   ```python
   from finwiz.tools.ticker_validation_tool import TickerValidationTool

   validator = TickerValidationTool()
   result = validator._run(ticker="AAPL")
   print(result)
   ```

3. Check network connectivity:

   ```bash
   curl -I https://www.alphavantage.co
   ```

**Solutions:**

1. **Configure API keys**:

   ```bash
   # Add to .env file
   ALPHA_VANTAGE_API_KEY=your_key_here
   TWELVE_DATA_API_KEY=your_key_here
   ```

2. **Verify ticker format**:

   ```python
   # Correct format
   ticker = "AAPL"  # Not "Apple" or "aapl"
   ```

3. **Check QuantitativeAnalysisTool logs**:

   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)

   # Run analysis and check logs
   results = analyze_portfolio_with_python(holdings, session_id)
   ```

4. **Test data fetching directly**:

   ```python
   from finwiz.tools.quantitative_analysis_tool import QuantitativeAnalysisTool

   tool = QuantitativeAnalysisTool()
   data = tool._run(symbol="AAPL", asset_class="stock", analysis_type="performance")
   print(data)
   ```

### Issue: No A+ Opportunities Found

**Symptom:**

```python
discovery_results["has_a_plus_analysis"] == False
discovery_results["total_opportunities_found"] == 0
```

**Possible Causes:**

1. Deep analysis not completed successfully
2. No holdings achieved A+ or A grade
3. JSON files not in expected directories
4. Session ID mismatch between analysis and discovery

**Diagnosis:**

1. Check deep analysis results:

   ```python
   print(f"Successful: {analysis_results['successful_analyses']}")
   print(f"Failed: {analysis_results['failed_analyses']}")
   ```

2. Check grades in analysis results:

   ```python
   for ticker, result in analysis_results["deep_analysis_results"].items():
       print(f"{ticker}: Grade {result.grade}, Score {result.composite_score:.3f}")
   ```

3. Verify output directory structure:

   ```bash
   ls -la output/stock/
   ls -la output/etf/
   ls -la output/crypto/
   ```

4. Check session ID consistency:

   ```python
   print(f"Analysis session: {session_id}")
   print(f"Discovery session: {session_id}")  # Should match
   ```

**Solutions:**

1. **Verify deep analysis completed**:

   ```python
   if analysis_results["successful_analyses"] == 0:
       print("❌ Deep analysis failed - check logs")
   ```

2. **Check analysis grades**:

   ```python
   # Look for A+ or A grades
   aplus_count = sum(
       1 for r in analysis_results["deep_analysis_results"].values()
       if r.grade in ["A+", "A"]
   )
   print(f"Found {aplus_count} A+/A grade holdings")
   ```

3. **Verify directory structure**:

   ```python
   from pathlib import Path

   output_dir = Path("output")
   for asset_class in ["stock", "etf", "crypto"]:
       dir_path = output_dir / asset_class
       if not dir_path.exists():
           print(f"❌ Missing directory: {dir_path}")
           dir_path.mkdir(parents=True, exist_ok=True)
   ```

4. **Use consistent session ID**:

   ```python
   # Generate once, use everywhere
   session_id = f"analysis_{int(time.time())}"

   analysis_results = analyze_portfolio_with_python(holdings, session_id)
   discovery_results = integrate_aplus_discovery_with_deep_analysis(session_id)
   ```

### Issue: Backtesting Not Executing

**Symptom:**

```python
backtesting_results["backtesting_executed"] == False
backtesting_results["reason"] == "No A+ candidates available"
```

**Possible Causes:**

1. A+ discovery found no opportunities
2. Discovery integration failed
3. Candidate list is empty

**Diagnosis:**

1. Check discovery results:

   ```python
   print(f"Has A+ analysis: {discovery_results['has_a_plus_analysis']}")
   print(f"Opportunities: {discovery_results['total_opportunities_found']}")
   ```

2. Check candidate list:

   ```python
   if discovery_results["has_a_plus_analysis"]:
       for holding in discovery_results["aplus_holdings"]:
           print(f"Candidate: {holding['ticker']} (Grade {holding['grade']})")
   ```

3. Verify discovery JSON exists:

   ```bash
   ls -la output/aplus_discovery_*.json
   ```

**Solutions:**

1. **Run A+ discovery first**:

   ```python
   # Ensure discovery runs before backtesting
   discovery_results = integrate_aplus_discovery_with_deep_analysis(session_id)

   if discovery_results["has_a_plus_analysis"]:
       backtesting_results = connect_backtesting_to_discovery_results(session_id)
   else:
       print("ℹ️ No A+ opportunities - skipping backtesting")
   ```

2. **Check discovery results**:

   ```python
   if not discovery_results["has_a_plus_analysis"]:
       print("No A+ opportunities found")
       print(f"Total analyzed: {discovery_results['total_analyzed']}")
   ```

3. **Verify discovery JSON**:

   ```python
   from pathlib import Path
   import json

   discovery_file = Path(f"output/aplus_discovery_{session_id}.json")
   if discovery_file.exists():
       with open(discovery_file) as f:
           data = json.load(f)
           print(f"Candidates: {len(data.get('aplus_holdings', []))}")
   ```

### Issue: JSON Export Files Not Found

**Symptom:**

```
FileNotFoundError: [Errno 2] No such file or directory: 'output/stock/AAPL_session_123.json'
```

**Possible Causes:**

1. Deep analysis failed to export files
2. Incorrect output directory path
3. File permissions issue
4. Session ID mismatch

**Diagnosis:**

1. Check if files were created:

   ```bash
   find output -name "*.json" -type f
   ```

2. Check file permissions:

   ```bash
   ls -la output/
   ls -la output/stock/
   ```

3. Check export logs:

   ```python
   # Look for export messages in logs
   # "📄 Exported AAPL analysis to output/stock/AAPL_session_123.json"
   ```

**Solutions:**

1. **Verify export completed**:

   ```python
   if "export_info" in analysis_results:
       print(f"Exported files: {analysis_results['export_info']['exported_files']}")
   ```

2. **Check directory permissions**:

   ```bash
   chmod 755 output/
   chmod 755 output/stock/
   chmod 755 output/etf/
   chmod 755 output/crypto/
   ```

3. **Create directories if missing**:

   ```python
   from pathlib import Path

   for dir_name in ["stock", "etf", "crypto"]:
       dir_path = Path("output") / dir_name
       dir_path.mkdir(parents=True, exist_ok=True)
   ```

### Issue: Report Generation Fails

**Symptom:**

```
Exception: Failed to generate report: ...
```

**Possible Causes:**

1. Missing template file
2. Invalid data structure
3. Jinja2 template error
4. File write permissions

**Diagnosis:**

1. Check template exists:

   ```bash
   ls -la src/finwiz/templates/
   ```

2. Validate input data:

   ```python
   print(f"Portfolio review: {portfolio_review}")
   print(f"Analysis results: {analysis_results}")
   ```

3. Check template rendering:

   ```python
   from finwiz.reporting.python_report_generator import PythonReportGenerator

   generator = PythonReportGenerator()
   # Check for template errors
   ```

**Solutions:**

1. **Verify template exists**:

   ```python
   from pathlib import Path

   template_path = Path("src/finwiz/templates/report.html.j2")
   if not template_path.exists():
       print(f"❌ Template not found: {template_path}")
   ```

2. **Validate data structure**:

   ```python
   from finwiz.schemas.portfolio_review import PortfolioReview

   # Ensure portfolio_review is valid
   assert isinstance(portfolio_review, PortfolioReview)
   assert len(portfolio_review.holdings) > 0
   ```

3. **Check output permissions**:

   ```bash
   chmod 755 output/
   touch output/test.html
   rm output/test.html
   ```

## Performance Issues

### Issue: Slow Analysis Execution

**Symptom:**

Analysis takes longer than expected (> 2 seconds per holding).

**Possible Causes:**

1. Network latency for API calls
2. API rate limiting
3. Large portfolio size
4. Inefficient data fetching

**Solutions:**

1. **Enable caching**:

   ```python
   # Cache market data to avoid redundant API calls
   from functools import lru_cache

   @lru_cache(maxsize=1000)
   def get_cached_data(ticker, date):
       return fetch_market_data(ticker, date)
   ```

2. **Batch processing**:

   ```python
   # Process holdings in batches
   BATCH_SIZE = 10
   for i in range(0, len(holdings), BATCH_SIZE):
       batch = holdings[i:i + BATCH_SIZE]
       process_batch(batch)
   ```

3. **Monitor API calls**:

   ```python
   import time

   start = time.time()
   data = fetch_data(ticker)
   elapsed = time.time() - start

   if elapsed > 1.0:
       logger.warning(f"Slow API call for {ticker}: {elapsed:.2f}s")
   ```

### Issue: High Memory Usage

**Symptom:**

Memory usage increases significantly during analysis.

**Solutions:**

1. **Process in batches**:

   ```python
   # Clear memory after each batch
   for batch in batches:
       results = process_batch(batch)
       export_results(results)
       del results  # Free memory
   ```

2. **Use generators**:

   ```python
   def analyze_holdings_generator(holdings):
       for holding in holdings:
           yield analyze_holding(holding)

   # Process one at a time
   for result in analyze_holdings_generator(holdings):
       export_result(result)
   ```

3. **Monitor memory**:

   ```python
   import psutil

   process = psutil.Process()
   memory_mb = process.memory_info().rss / 1024 / 1024
   print(f"Memory usage: {memory_mb:.1f} MB")
   ```

## Debugging Tips

### Enable Debug Logging

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Run analysis with debug logging
results = analyze_portfolio_with_python(holdings, session_id)
```

### Inspect Intermediate Results

```python
# Check analysis results
for ticker, result in analysis_results["deep_analysis_results"].items():
    print(f"{ticker}:")
    print(f"  Grade: {result.grade}")
    print(f"  Score: {result.composite_score:.3f}")
    print(f"  Fundamental: {result.fundamental_score:.3f}")
    print(f"  Technical: {result.technical_score:.3f}")
    print(f"  Risk: {result.risk_score:.3f}")
```

### Validate JSON Exports

```python
import json
from pathlib import Path

# Read and validate JSON export
export_file = Path(f"output/stock/AAPL_{session_id}.json")
with open(export_file) as f:
    data = json.load(f)

# Validate structure
assert "ticker" in data
assert "composite_score" in data
assert "grade" in data
print("✅ JSON export valid")
```

## Getting Help

If you continue to experience issues:

1. **Check logs**: Review application logs for error messages
2. **Verify configuration**: Ensure all environment variables are set
3. **Test components individually**: Isolate the failing component
4. **Review documentation**: Check component-specific documentation
5. **Report issues**: Create a GitHub issue with:
   - Error message
   - Steps to reproduce
   - Environment details
   - Log output

## Related Documentation

- **[Components](components.md)** - Component documentation
- **[Best Practices](best-practices.md)** - Implementation guidelines
- **[How-to Guide](../../how-to/use_python_pipeline.md)** - Usage instructions
- **[API Reference](../../reference/integration/python_pipeline_integration.md)** - API documentation
