# Templates Module

This directory contains Jinja2 HTML templates for report generation. Templates are used by Python (NOT AI) to generate consistent, styled reports.

## Directory Structure

```
templates/
├── crew_reports/                    # Per-crew report templates
│   ├── base.html                   # Base template with common styles
│   └── deep_analysis_report.html.j2 # Deep analysis report (live)
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

`BaseReportGenerator` (implementing `get_template_name()`,
`get_required_fields()`, and `prepare_template_variables()`) had subclasses
for the per-crew templates below; those subclasses were deleted along with
`crew_reports/{stock,etf,crypto,discovery,rebalancing}_report.html` and
`crew_reports/final_report.html` — the crew subsystem that produced their
JSON inputs was removed and nothing else loaded them (see #187).
`BaseReportGenerator` itself was later deleted once its last subclass was
gone; `create_report_jinja_env()` in the same file is unrelated and stays live.

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

- `finwiz.reporting.base_report_generator` - `create_report_jinja_env()`
- `finwiz.tools.html_report_generator` - HTML generation tool
- `finwiz.reporting` - Report generation logic
