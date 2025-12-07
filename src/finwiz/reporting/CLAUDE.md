# Reporting Module

This directory contains report generation logic using Python templates (Jinja2). Following AI Minimalism principles, all report rendering is done with Python - NOT AI agents.

## Directory Structure

```
reporting/
├── __init__.py
├── deep_analysis_report_generator.py    # Per-holding analysis reports
├── enriched_analysis_report_generator.py # Enriched analysis reports
└── python_report_generator.py           # Main Python report generator
```

## Major Entry Points

| File | Class | Purpose |
|------|-------|---------|
| `python_report_generator.py` | `PythonReportGenerator` | Main report generation engine |
| `deep_analysis_report_generator.py` | `DeepAnalysisReportGenerator` | Per-holding detailed reports |
| `enriched_analysis_report_generator.py` | `EnrichedAnalysisReportGenerator` | Enriched analysis reports |

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

## Usage

### Generate Single Report

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
