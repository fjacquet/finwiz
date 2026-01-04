# Reporting Module

This directory contains report generation logic using Python templates (Jinja2). Following AI Minimalism principles, all report rendering is done with Python - NOT AI agents.

## Directory Structure

```
reporting/
├── __init__.py                          # Module exports + CREW_GENERATORS registry
├── base_report_generator.py             # Abstract base class for generators
├── stock_report_generator.py            # Stock crew reports
├── etf_report_generator.py              # ETF crew reports
├── crypto_report_generator.py           # Crypto crew reports
├── discovery_report_generator.py        # A+ discovery reports
├── rebalancing_report_generator.py      # Rebalancing recommendations
├── deep_analysis_report_generator.py    # Per-holding analysis reports
├── enriched_analysis_report_generator.py # Enriched analysis reports
├── individual_report_generator.py       # Individual holding report generation
├── python_report_generator.py           # Main Python report generator
├── portfolio_review_html.py             # Portfolio review HTML tables & sections
├── report_css_styles.py                 # CSS styles for HTML reports
└── report_section_generators.py         # HTML section generation functions
```

## Major Entry Points

| File | Class/Function | Purpose |
|------|----------------|---------|
| `__init__.py` | `CREW_GENERATORS` | Registry mapping crew names to generators |
| `__init__.py` | `get_generator_for_crew()` | Get generator instance for a crew |
| `base_report_generator.py` | `BaseReportGenerator` | Abstract base class with common logic |
| `stock_report_generator.py` | `StockReportGenerator` | Stock analysis HTML reports |
| `etf_report_generator.py` | `ETFReportGenerator` | ETF analysis HTML reports |
| `crypto_report_generator.py` | `CryptoReportGenerator` | Crypto analysis HTML reports |
| `discovery_report_generator.py` | `DiscoveryReportGenerator` | A+ discovery HTML reports |
| `rebalancing_report_generator.py` | `RebalancingReportGenerator` | Rebalancing HTML reports |
| `deep_analysis_report_generator.py` | `DeepAnalysisReportGenerator` | Per-holding detailed reports |
| `individual_report_generator.py` | `generate_individual_report_html()` | Individual holding HTML report |
| `python_report_generator.py` | `PythonReportGenerator` | Main report generation engine |
| `report_css_styles.py` | `get_report_css()` | CSS styles for HTML reports |
| `report_section_generators.py` | `generate_executive_summary()` | Executive summary HTML |
| `report_section_generators.py` | `generate_holdings_analysis()` | Holdings analysis HTML |
| `report_section_generators.py` | `generate_recommendations()` | Recommendations section HTML |
| `portfolio_review_html.py` | `generate_holdings_table()` | Holdings table with grades |
| `portfolio_review_html.py` | `generate_trades_table()` | Trade recommendations table |
| `portfolio_review_html.py` | `add_portfolio_review_sections()` | Portfolio overview sections |
| `portfolio_review_html.py` | `add_rebalancing_sections()` | Rebalancing summary sections |

## Data Format Handling

The `individual_report_generator.py` handles two JSON formats:

1. **Nested format** (enriched JSON): Qualitative sections under `result["qualitative"]`
2. **Flat format** (legacy): Qualitative sections at top-level

The generator automatically checks both locations using fallback pattern:
```python
sec_insights = result.get("sec_insights") or qualitative_container.get("sec_insights", {})
```

## AI Minimalism Principle

Report generation is 100% Python - no AI involved:

| Task | Approach | Cost | Reliability |
|------|----------|------|-------------|
| Data gathering | AI Crews | $$$ | 95% |
| Report rendering | Python/Jinja2 | $0 | 100% |

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   AI Crews      │ --> │   JSON Export   │ --> │ Python Template │
│ (analysis)      │     │ (Pydantic)      │     │ (Jinja2)        │
└─────────────────┘     └─────────────────┘     └─────────────────┘
      $$$                     Free                    Free
```

## Output Structure

Reports are generated to a unified output directory structure:

```
output/
├── stock/
│   ├── AAPL_enriched.json      # Enriched analysis data
│   ├── AAPL_report.html        # Individual detailed report
│   └── discovery_output*.json  # A+ discovery results
├── etf/
│   └── (same structure)
├── crypto/
│   └── (same structure)
└── portfolio/
    └── portfolio_review.html   # Consolidated portfolio report
```

**On-the-fly Generation**: Individual reports (`{ticker}_report.html`) are generated immediately after each holding analysis by `DeepAnalysisOrchestrator._store_enriched_analysis()`. This eliminates duplicate generation and reduces processing time.

## Usage

### Using CREW_GENERATORS Registry (Recommended)

```python
from finwiz.reporting import CREW_GENERATORS, get_generator_for_crew

# Get generator for a specific crew
generator = get_generator_for_crew("stock_crew")
if generator:
    html = generator.generate_report(
        data={"ticker": "AAPL", "grade": "A", "composite_score": 0.85},
        output_path="output/stock/AAPL_report.html"
    )

# Available crew mappings:
# "stock_crew" -> StockReportGenerator
# "etf_crew" -> ETFReportGenerator
# "crypto_crew" -> CryptoReportGenerator
# "investment_discovery_crew" -> DiscoveryReportGenerator
# "portfolio_rebalancing_crew" -> RebalancingReportGenerator
# "deep_analysis_crew" -> DeepAnalysisReportGenerator
```

### Using Individual Generators

```python
from finwiz.reporting.stock_report_generator import StockReportGenerator

generator = StockReportGenerator()
html_path = generator.generate_report(
    data={
        "ticker": "AAPL",
        "grade": "A",
        "composite_score": 0.85,
        "recommendation": "BUY",
        "generation_date": "2025-12-29"
    },
    output_path="output/reports/stock/AAPL_report.html"
)
```

### Auto-Generation via ReportingOrchestrator

```python
from finwiz.orchestrators.reporting_orchestrator import ReportingOrchestrator
from finwiz.flow_state import FinwizState

orchestrator = ReportingOrchestrator(FinwizState())

# Consolidate AND auto-generate HTML reports
result = orchestrator.consolidate_reports(
    crew_export_paths={
        "stock_crew": ["output/stock/AAPL_export.json"],
        "etf_crew": ["output/etf/SPY_export.json"],
    },
    generate_html=True  # Default: auto-generates HTML
)

# Result includes HTML paths
print(result["html_report_paths"])
# {"stock_crew": ["output/stock/AAPL_export.html"], ...}
```

### Generate Single Report (Legacy)

```python
from finwiz.reporting.python_report_generator import PythonReportGenerator
from finwiz.schemas.crew_exports import StockCrewExport

# Load export data
with open("output/reports/session_123/stock/AAPL_export.json") as f:
    export_data = StockCrewExport.model_validate_json(f.read())

# Generate HTML report
generator = PythonReportGenerator()
html_path = generator.generate_report(
    template_name="stock_report.html",
    data=export_data.model_dump(),
    output_path="output/reports/session_123/stock/AAPL_report.html"
)
```

### Generate Deep Analysis Report

```python
from finwiz.reporting.deep_analysis_report_generator import DeepAnalysisReportGenerator
from finwiz.flow_state import DeepAnalysisResult

generator = DeepAnalysisReportGenerator()

# Generate for single holding
html_path = generator.generate_holding_report(
    result=deep_analysis_result,
    output_dir="output/reports/session_123/deep_analysis"
)

# Generate consolidated report
consolidated_path = generator.generate_consolidated_report(
    results={"AAPL": result1, "GOOGL": result2, "MSFT": result3},
    output_path="output/reports/session_123/deep_analysis_consolidated.html"
)
```

### Generate Enriched Analysis Report

```python
from finwiz.reporting.enriched_analysis_report_generator import EnrichedAnalysisReportGenerator

generator = EnrichedAnalysisReportGenerator()
html_path = generator.generate(
    enriched_data=enriched_analysis,
    output_path="output/reports/session_123/enriched_analysis.html"
)
```

## Template Location

Templates are in `src/finwiz/templates/`:

```
templates/
├── crew_reports/
│   ├── base.html              # Base template
│   ├── stock_report.html      # Stock crew reports
│   ├── etf_report.html        # ETF crew reports
│   ├── crypto_report.html     # Crypto crew reports
│   ├── deep_analysis_report.html.j2  # Deep analysis
│   ├── discovery_report.html  # A+ discovery
│   ├── rebalancing_report.html # Rebalancing
│   └── final_report.html      # Final consolidated
├── portfolio_review.html      # Portfolio review
├── enriched_analysis_report.html
└── [other templates]
```

## Template Pattern

```html
<!-- templates/crew_reports/stock_report.html -->
{% extends "base.html" %}

{% block title %}{{ ticker }} Stock Analysis{% endblock %}

{% block content %}
<div class="report-header">
    <h1>{{ ticker }} Analysis</h1>
    <div class="grade grade-{{ grade|lower }}">{{ grade }}</div>
</div>

<div class="recommendation {{ recommendation|lower }}">
    <h2>Recommendation: {{ recommendation }}</h2>
    <p>{{ rationale }}</p>
</div>

<div class="scores">
    <div class="score">
        <span class="label">Composite Score</span>
        <span class="value">{{ "%.2f"|format(composite_score) }}</span>
    </div>
</div>
{% endblock %}
```

## Report Generator Pattern

```python
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

class ReportGenerator:
    """Base class for report generators."""

    def __init__(self):
        template_dir = Path(__file__).parent.parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=True
        )

    def generate_report(
        self,
        template_name: str,
        data: dict,
        output_path: str
    ) -> str:
        """Generate HTML report from template and data."""
        template = self.env.get_template(template_name)
        html_content = template.render(**data)

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(html_content, encoding="utf-8")

        return output_path
```

## Testing

```bash
# Test all report generators
uv run pytest tests/unit/reporting/ -v

# Test specific generator
uv run pytest tests/unit/reporting/test_python_report_generator.py -v

# Generate test report
uv run python -c "
from finwiz.reporting.python_report_generator import PythonReportGenerator
gen = PythonReportGenerator()
# ... test generation
"
```

## Related Modules

- `finwiz.templates` - Jinja2 HTML templates
- `finwiz.schemas.crew_exports` - Export schemas for data
- `finwiz.tools.html_report_generator` - Tool wrapper for crews
- `finwiz.utils.template_renderer` - Template rendering utilities
