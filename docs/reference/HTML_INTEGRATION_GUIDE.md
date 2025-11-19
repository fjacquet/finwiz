# HTML Integration Guide

This guide shows how to integrate automatic HTML generation into existing FinWiz code.

## Quick Start

### 1. Import the HTML Generator

```python
from finwiz.utils.html_generator import (
    save_json_with_html,
    save_portfolio_review,
    save_backtesting_results,
    JSONWriter,
    auto_html
)
```

### 2. Replace JSON Saves

**Before (JSON only):**

```python
import json

def save_portfolio_analysis(data, output_path):
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    return output_path
```

**After (JSON + HTML):**

```python
from finwiz.utils.html_generator import save_portfolio_review

def save_portfolio_analysis(data, output_path):
    json_path, html_path = save_portfolio_review(data, output_path)
    return json_path  # HTML generated automatically
```

## Integration Methods

### Method 1: Direct Replacement (Recommended)

Use the convenience functions for specific report types:

```python
# Backtesting results
json_path, html_path = save_backtesting_results(data, "output/backtesting.json")

# Portfolio review
json_path, html_path = save_portfolio_review(data, "output/portfolio.json")

# A+ discovery
json_path, html_path = save_a_plus_discovery(data, "output/discovery.json")

# Deep analysis
json_path, html_path = save_deep_analysis(data, "output/analysis.json")

# Optimization report
json_path, html_path = save_optimization_report(data, "output/optimization.json")

# Validation report
json_path, html_path = save_validation_report(data, "output/validation.json")
```

### Method 2: Generic Save with Auto-Detection

```python
from finwiz.utils.html_generator import save_json_with_html

# Template type auto-detected from filename
json_path, html_path = save_json_with_html(data, "output/portfolio_review.json")
json_path, html_path = save_json_with_html(data, "output/backtesting_results.json")
```

### Method 3: Context Manager

```python
from finwiz.utils.html_generator import JSONWriter

with JSONWriter("output/portfolio_review.json", "portfolio_review") as writer:
    # Build your data
    data = {"holdings": [], "summary": {}}
    
    # Add more data as needed
    writer.update({"additional_field": "value"})
    
    # Write final data (JSON + HTML generated on exit)
    writer.write(data)
```

### Method 4: Decorator

```python
from finwiz.utils.html_generator import auto_html

@auto_html('portfolio_review')
def generate_portfolio_report(holdings_data):
    # Your existing logic
    report_data = process_holdings(holdings_data)
    
    # Save JSON file
    output_path = "output/portfolio_review.json"
    with open(output_path, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    return output_path  # HTML generated automatically
```

## Crew Integration

### CrewAI Flow Integration

```python
from finwiz.utils.html_generator import save_portfolio_review, save_backtesting_results

class FinwizFlow(Flow[FinwizState]):
    
    @listen("analyze_portfolio")
    def save_portfolio_results(self, analysis_data: dict[str, Any]) -> dict[str, Any]:
        # Process analysis data
        portfolio_data = self._format_portfolio_data(analysis_data)
        
        # Save with automatic HTML generation
        json_path, html_path = save_portfolio_review(
            portfolio_data, 
            f"output/portfolio/portfolio_review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        return {
            "portfolio_saved": True,
            "json_path": str(json_path),
            "html_path": str(html_path) if html_path else None
        }
    
    @listen("run_backtesting")
    def save_backtesting_results(self, backtest_data: dict[str, Any]) -> dict[str, Any]:
        # Format backtesting results
        results_data = self._format_backtesting_data(backtest_data)
        
        # Save with HTML generation
        json_path, html_path = save_backtesting_results(
            results_data,
            "output/backtesting_results_default.json"
        )
        
        return {
            "backtesting_saved": True,
            "results_path": str(json_path),
            "html_path": str(html_path) if html_path else None
        }
```

### Individual Crew Integration

```python
from finwiz.utils.html_generator import save_a_plus_discovery

class StockDiscoveryCrew:
    
    def save_discovery_results(self, discovery_data: dict) -> str:
        """Save discovery results with HTML generation."""
        
        # Format data for template
        formatted_data = {
            "discovery_id": f"StockRun-{datetime.now().strftime('%Y-%m-%d-%H%M')}",
            "generated_at": datetime.now().isoformat(),
            "asset_type": "stock",
            "grade": "A+",
            "discovery_criteria": discovery_data.get("criteria", {}),
            "candidates": discovery_data.get("candidates", [])
        }
        
        # Save with automatic HTML generation
        json_path, html_path = save_a_plus_discovery(
            formatted_data,
            f"output/discovery/a_plus_stocks_{datetime.now().strftime('%Y%m%d')}.json"
        )
        
        if html_path:
            print(f"📊 Discovery report generated: {html_path}")
        
        return str(json_path)
```

## Configuration

### Enable/Disable HTML Generation

```python
from finwiz.utils.html_generator import enable_html_generation, disable_html_generation

# Disable for performance-critical operations
disable_html_generation()
# ... bulk processing ...

# Re-enable for user-facing reports
enable_html_generation()
```

### Environment Variable Control

Add to your `.env` file:

```bash
# Enable/disable HTML generation
FINWIZ_HTML_GENERATION=true

# Custom templates directory (optional)
FINWIZ_TEMPLATES_DIR=/path/to/custom/templates
```

Use in code:

```python
import os
from finwiz.utils.html_generator import html_generator

# Check environment variable
if os.getenv("FINWIZ_HTML_GENERATION", "true").lower() == "false":
    html_generator.disable()
```

## Error Handling

The HTML generation is designed to be non-blocking:

```python
# If HTML generation fails, JSON is still saved
json_path, html_path = save_portfolio_review(data, "output/portfolio.json")

if html_path:
    print(f"✅ HTML generated: {html_path}")
else:
    print("⚠️  HTML generation failed, but JSON saved successfully")
```

## Performance Considerations

### Batch Operations

For bulk processing, disable HTML generation:

```python
from finwiz.utils.html_generator import disable_html_generation, enable_html_generation

# Disable during bulk processing
disable_html_generation()

for holding in large_portfolio:
    # Process many holdings quickly (JSON only)
    save_json_with_html(holding_data, f"output/holdings/{holding.ticker}.json")

# Re-enable for final reports
enable_html_generation()
save_portfolio_review(consolidated_data, "output/portfolio_summary.json")
```

### Async Processing

For async operations, HTML generation is thread-safe:

```python
import asyncio
from finwiz.utils.html_generator import save_portfolio_review

async def process_portfolio_async(portfolio_data):
    # HTML generation works in async context
    json_path, html_path = save_portfolio_review(portfolio_data, "output/async_portfolio.json")
    return json_path, html_path
```

## Migration Checklist

When migrating existing code:

- [ ] **Identify JSON save points** - Find where JSON files are currently saved
- [ ] **Choose integration method** - Direct replacement, decorator, or context manager
- [ ] **Update imports** - Add HTML generator imports
- [ ] **Replace save calls** - Use HTML-enabled save functions
- [ ] **Test output** - Verify both JSON and HTML are generated correctly
- [ ] **Handle errors** - Ensure HTML generation failures don't break existing logic
- [ ] **Update documentation** - Document new HTML output locations

## Examples

See `examples/inline_html_example.py` for complete working examples of all integration methods.

## Troubleshooting

### HTML Not Generated

1. **Check template mapping** - Ensure filename matches expected pattern
2. **Verify data format** - Template expects specific data structure
3. **Check permissions** - Ensure write access to output directory
4. **Enable debug** - Set `FINWIZ_DEBUG=true` for detailed error messages

### Template Errors

1. **Missing fields** - Templates handle missing data gracefully with defaults
2. **Type errors** - Ensure data types match template expectations
3. **Custom templates** - Use custom templates directory if needed

### Performance Issues

1. **Disable for bulk operations** - Use `disable_html_generation()` for large batches
2. **Async processing** - HTML generation is non-blocking but can be disabled if needed
3. **Template caching** - Templates are cached automatically for performance

---

**Version**: 1.0  
**Last Updated**: 2025-10-27  
**Next**: See `src/finwiz/templates/README.md` for template customization
