# Templates Module

This directory contains Jinja2 HTML templates for report generation. Templates are used by Python (NOT AI) to generate consistent, styled reports.

## Directory Structure

```
templates/
├── crew_reports/                    # Per-crew report templates
│   ├── base.html                   # Base template with common styles
│   ├── stock_report.html           # Stock analysis report
│   ├── etf_report.html             # ETF analysis report
│   ├── crypto_report.html          # Crypto analysis report
│   ├── deep_analysis_report.html.j2 # Deep analysis report
│   ├── discovery_report.html       # A+ discovery report
│   ├── rebalancing_report.html     # Rebalancing recommendations
│   └── final_report.html           # Consolidated final report
├── base_template.html              # Global base template
├── portfolio_review.html           # Portfolio review template
├── a_plus_discovery.html           # A+ discovery template
├── backtesting_results.html        # Backtesting results
├── optimization_report.html        # Portfolio optimization
├── validation_report.html          # Data validation report
└── [other specialized templates]
```

## Major Entry Points

| Template | Purpose |
|----------|---------|
| `crew_reports/base.html` | Base layout with CSS, JS, navigation |
| `portfolio_review.html` | Complete portfolio review with recommendations |
| `a_plus_discovery.html` | A+ investment opportunities |
| `deep_analysis_consolidated.html` | Per-holding deep analysis |
| `rebalancing_template.html` | Rebalancing trades and allocations |

## Usage Pattern

Templates are rendered through a shared Jinja2 environment — there is no
`render_template()` helper.

```python
from finwiz.reporting.base_report_generator import create_report_jinja_env

env = create_report_jinja_env(template_dir)  # autoescape=True, trim/lstrip_blocks
template = env.get_template("portfolio_review.html")

html = template.render(
    session_id=session_id,
    holdings=holdings,
    recommendations=recommendations,
    generated_at=datetime.now(),
)

# Save report
with open(f"output/reports/{session_id}/portfolio_review.html", "w") as f:
    f.write(html)
```

Crew-specific generators subclass `BaseReportGenerator` and implement
`get_template_name()`, `get_required_fields()`, and
`prepare_template_variables()` rather than calling Jinja directly.

## Template Inheritance

```html
{% extends "crew_reports/base.html" %}

{% block title %}Stock Analysis - {{ ticker }}{% endblock %}

{% block content %}
<div class="analysis-container">
    <h1>{{ ticker }} Analysis</h1>
    <!-- Content -->
</div>
{% endblock %}
```

## AI Minimalism

Templates are ALWAYS rendered by Python (Jinja2), NEVER by AI agents:

- Deterministic output
- Zero LLM cost
- 100% reliability
- Consistent styling

## Related Modules

- `finwiz.reporting.base_report_generator` - `create_report_jinja_env()`, `BaseReportGenerator`
- `finwiz.tools.html_report_generator` - HTML generation tool
- `finwiz.reporting` - Report generation logic
