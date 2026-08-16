# HTML Reports Reference

Complete reference for FinWiz HTML report generation system.

## Overview

FinWiz automatically converts JSON outputs into professional, responsive HTML reports with dark/light mode support. The system includes 9 report types with consistent styling and interactive features.

## Report Types

### 1. Backtesting Results

**JSON Pattern**: `backtesting_results_*.json`
**Template**: `backtesting_results.html`
**Purpose**: Investment candidate performance analysis

**Key Features**:

- Candidate performance metrics
- Risk-adjusted returns
- Comparative analysis
- Grade distribution

**Generation**:

```bash
# output/backtesting_results_default.json is picked up automatically by filename pattern —
# there is no --file or --type flag; the script only accepts
# --output-dir, --force, --verbose
uv run python scripts/generate_html_reports.py --output-dir output --force
```

---

### 2. Portfolio Review

**JSON Pattern**: `portfolio_review.json`
**Template**: `portfolio_review.html`
**Purpose**: Portfolio holdings analysis and recommendations

**Key Features**:

- Holdings overview with grades
- Keep/sell recommendations
- Alternative suggestions
- Portfolio composition

**Generation**:

```bash
# output/portfolio/portfolio_review.json is picked up automatically by filename pattern —
# there is no --file or --type flag; the script only accepts
# --output-dir, --force, --verbose
uv run python scripts/generate_html_reports.py --output-dir output --force
```

---

### 3. A+ Discovery Reports

**JSON Pattern**: `a_plus_*.json`
**Template**: `a_plus_discovery.html`
**Purpose**: A+ investment opportunities by asset class

**Variants**:

- `a_plus_stocks.json` - Stock opportunities
- `a_plus_etfs.json` - ETF opportunities
- `a_plus_crypto.json` - Cryptocurrency opportunities

**Key Features**:

- Top-rated candidates
- Detailed rationales
- Asset-specific metrics
- Screening criteria

**Generation**:

```bash
# output/discovery/a_plus_stocks.json is picked up automatically by filename pattern —
# there is no --file or --type flag; the script only accepts
# --output-dir, --force, --verbose
uv run python scripts/generate_html_reports.py --output-dir output --force
```

---

### 4. Deep Analysis Consolidated

**JSON Pattern**: `deep_analysis_consolidated_*.json`
**Template**: `deep_analysis_consolidated.html`
**Purpose**: Consolidated deep analysis results for all holdings

**Key Features**:

- Comprehensive analysis summary
- Grade distribution
- Performance metrics
- Individual holding details

**Generation**:

```bash
# output/deep_analysis_consolidated_default.json is picked up automatically by filename pattern —
# there is no --file or --type flag; the script only accepts
# --output-dir, --force, --verbose
uv run python scripts/generate_html_reports.py --output-dir output --force
```

---

### 5. Discovery Latest

**JSON Pattern**: `discovery_latest.json`
**Template**: `discovery_latest.html`
**Purpose**: Latest investment discovery results

**Key Features**:

- Recent opportunities
- Market context
- Screening criteria
- Data sources

**Data Structure Note**: Handles CrewAI output format with `pydantic` wrapper:

```json
{
  "pydantic": {
    "opportunities": [...],
    "analysis_date": "2025-10-27T00:00:00Z",
    "screening_criteria": {...}
  }
}
```

**Generation**:

```bash
# output/discovery/discovery_latest.json is picked up automatically by filename pattern —
# there is no --file or --type flag; the script only accepts
# --output-dir, --force, --verbose
uv run python scripts/generate_html_reports.py --output-dir output --force
```

---

### 6. Validation Report

**JSON Pattern**: `validation_report.json`
**Template**: `validation_report.html`
**Purpose**: Data validation status and quality metrics

**Key Features**:

- Validation results
- Data quality scores
- Error summaries
- Compliance status

**Generation**:

```bash
# output/discovery/validation_report.json is picked up automatically by filename pattern —
# there is no --file or --type flag; the script only accepts
# --output-dir, --force, --verbose
uv run python scripts/generate_html_reports.py --output-dir output --force
```

---

### 7. Portfolio Processing Summary

**JSON Pattern**: `portfolio_processing_summary.json`
**Template**: `portfolio_processing_summary.html`
**Purpose**: Processing performance and statistics

**Key Features**:

- Processing metrics
- Success/failure rates
- Performance statistics
- Error tracking

**Generation**:

```bash
# output/portfolio/portfolio_processing_summary.json is picked up automatically by filename pattern —
# there is no --file or --type flag; the script only accepts
# --output-dir, --force, --verbose
uv run python scripts/generate_html_reports.py --output-dir output --force
```

---

### 8. Optimization Report

**JSON Pattern**: `optimization_report.json`
**Template**: `optimization_report.html`
**Purpose**: Portfolio optimization recommendations

**Key Features**:

- Optimization strategies
- Rebalancing suggestions
- Risk-return analysis
- Implementation plan

**Generation**:

```bash
# output/discovery/optimization_report.json is picked up automatically by filename pattern —
# there is no --file or --type flag; the script only accepts
# --output-dir, --force, --verbose
uv run python scripts/generate_html_reports.py --output-dir output --force
```

---

### 9. Feedback Learning Report — template missing

**JSON Pattern**: `feedback_learning_report.json`
**Template**: `feedback_learning_report.html` — **does not exist** in
`src/finwiz/templates/`. The mapping in `JsonToHtmlConverter.TEMPLATE_MAPPING`
still points at it, so converting a `feedback_learning_report.json` file
currently fails with a Jinja2 `TemplateNotFound` error. Only 8 of these 9
documented report types actually have a template on disk.
**Purpose**: Feedback analysis and learning insights

**Key Features**:

- Success metrics dashboard (6 key metrics)
- Feedback analysis summary
- Performance outcome tracking
- Criteria optimization recommendations
- Asset-specific learning insights
- Implementation plan with phases
- Statistical significance analysis
- Rollback & safety mechanisms
- Quality assurance metrics

**Expected JSON Structure**:

```json
{
  "pydantic": {
    "objective": "string",
    "key_findings": ["string"],
    "acceptance_rate": 0.642,
    "grade_maintenance_6m": 0.76,
    "portfolio_grade_improvement": 0.108,
    "discovery_rate": 6.2,
    "relative_outperformance": 0.016,
    "user_satisfaction": 4.05,
    "feedback_summary": {
      "total_events": 1242,
      "data_quality_score": 0.87
    },
    "acceptance_by_asset_class": {
      "etf": {"rate": 0.71, "sample_size": 450}
    },
    "performance_outcomes": {
      "tracking_period": "180-day",
      "precision": 0.74
    },
    "optimization_recommendations": {...},
    "asset_specific_insights": {...},
    "implementation_plan": [...],
    "statistical_analysis": [...],
    "rollback_mechanisms": {...},
    "next_steps": [...],
    "qa_metrics": {...}
  }
}
```

**Generation**:

```bash
# output/discovery/feedback_learning_report.json is picked up automatically by filename pattern —
# there is no --file or --type flag; the script only accepts
# --output-dir, --force, --verbose
uv run python scripts/generate_html_reports.py --output-dir output --force
```

---

## Template Features

### Dark/Light Mode

All templates include theme switching:

- **Automatic Detection**: Reads system preferences
- **Manual Toggle**: Button in top-right corner
- **Persistent Storage**: Remembers user preference via localStorage
- **Smooth Transitions**: Animated theme changes

### Responsive Design

Templates adapt to screen size:

- **Desktop (>768px)**: Multi-column grids, full features
- **Tablet (768px)**: Adjusted layouts, optimized spacing
- **Mobile (<768px)**: Single-column, touch-friendly

### Professional Styling

Consistent visual language:

- **Grade Colors**: A+ (green), A (light green), B (orange), C (yellow), D (red), F (dark red)
- **Status Indicators**: BUY (green), HOLD (orange), SELL (red)
- **Risk Levels**: Low (green), Medium (orange), High (red)
- **Interactive Elements**: Hover effects, smooth animations

### Print Optimization

Print-friendly formatting:

- Black text on white background
- Proper page breaks
- Optimized font sizes
- Hidden interactive elements

---

## Batch Generation

`scripts/generate_html_reports.py`'s `ArgumentParser` defines exactly three
options — `--output-dir` (default `output`), `--force`, `--verbose` — and no
positional argument or `--file`/`--type`/`--all` flags. The script always
batch-scans a directory for known filename patterns; there is no per-file
mode.

**`make html-reports` and `make html-report` are both currently broken** —
they invoke `--all` and `--file "$(FILE)" --type "$(TYPE)"` respectively,
neither of which the script accepts, so both exit with "unrecognized
arguments". `make html-convert` is the one Makefile target that actually
works, since it calls the script with no extra flags.

### Generate All Reports

```bash
# The working invocation:
make html-convert
# or directly:
uv run python scripts/generate_html_reports.py --output-dir output --force
```

### Generate Specific Report

There is no way to target a single file — the script always scans the whole
`--output-dir` for files matching its known patterns and converts every
match it finds.

---

## Inline Generation

### Automatic HTML Generation

Use `auto_generate_html` to convert a JSON output file to HTML after saving:

```python
from pathlib import Path
from finwiz.reporting.html_auto_generator import auto_generate_html

json_path = Path("output/portfolio_review.json")
html_path = auto_generate_html(json_path)
if html_path:
    print(f"HTML report: {html_path}")
```

The function returns the `Path` of the generated HTML, or `None` if no matching
template exists for that JSON file type.

---

## Troubleshooting

### Common Issues

#### 1. Template Not Found

**Error**: `Template not found: report_type.html`

**Solution**: Check template exists in `src/finwiz/templates/`

#### 2. Data Structure Mismatch

**Error**: `'dict' object has no attribute 'field_name'`

**Solution**: Check if data uses CrewAI format with `pydantic` wrapper:

```python
# Extract from pydantic field if present
if "pydantic" in json_data and json_data["pydantic"]:
    data = json_data["pydantic"]
else:
    data = json_data
```

#### 3. Missing Required Fields

**Error**: `KeyError: 'required_field'`

**Solution**: Provide default values in template:

{% raw %}

```html
{{ data.get('field_name', 'Default Value') }}
```

{% endraw %}

#### 4. Date Parsing Errors

**Error**: `Invalid date format`

**Solution**: Parse date strings properly:

```python
from dateutil import parser

if isinstance(date_str, str):
    date_obj = parser.parse(date_str)
```

### Template Attribute vs Dict Access

Templates must handle both Python objects and dicts:

{% raw %}

```html
<!-- For Python objects (attribute access) -->
{{ candidate.ticker }}

<!-- For dicts (dict access) -->
{{ candidate['ticker'] }}

<!-- Safe approach (works for both) -->
{{ candidate.get('ticker') if candidate is mapping else candidate.ticker }}
```

{% endraw %}

---

## Template Customization

### Location

Templates are in `src/finwiz/templates/`

### Base Template

All templates extend `base_template.html` which provides:

- Theme switching logic
- Common CSS styles
- Responsive design framework
- Print optimization

### Creating Custom Templates

1. Create new template in `src/finwiz/templates/`
2. Extend base template:
{% raw %}

   ```html
   {% extends "base_template.html" %}

   {% block title %}Custom Report{% endblock %}

   {% block content %}
   <!-- Your content here -->
   {% endblock %}
   ```

{% endraw %}

Neither `template_renderer.py` nor `html_generator.py` exists anywhere in
this repo, and there is no `render_methods` dict or `_save_with_html`
helper. Template registration is a single entry in
`JsonToHtmlConverter.TEMPLATE_MAPPING`
(`src/finwiz/infrastructure/json/to_html_converter.py:30-47`):

1. Add your JSON filename pattern and template name to `TEMPLATE_MAPPING`:

   ```python
   TEMPLATE_MAPPING = {
       ...
       "custom_report.json": "custom_report.html",
   }
   ```

2. Drop the corresponding `custom_report.html` file in
   `src/finwiz/templates/` — no separate Python registration step is
   needed.

---

## Performance

### Non-blocking Design

HTML generation failures don't break JSON saves:

```python
try:
    html_path = generate_html(json_path)
except Exception as e:
    logger.warning(f"HTML generation failed: {e}")
    # JSON save still succeeds
```

### Template Caching

Templates are cached automatically by Jinja2 for performance.

---

## Success Metrics

⚠️ **8 of 9 Professional Templates** - `feedback_learning_report.html` is missing; see "9. Feedback Learning Report" above
✅ **Automatic Generation** - Inline generation working
✅ **Dark/Light Mode** - Fully functional theme switching
✅ **Responsive Design** - Mobile, tablet, desktop support
✅ **Print Ready** - Optimized for PDF export
✅ **Error Resilient** - Non-blocking, graceful degradation

---

## See Also

- HTML auto-generator: `src/finwiz/reporting/html_auto_generator.py`
- JSON-to-HTML converter: `src/finwiz/infrastructure/json/to_html_converter.py`
- Templates: `src/finwiz/templates/`
- Generation script: `scripts/generate_html_reports.py`

---

**Version**: 1.0
**Last Updated**: 2025-10-28
**Status**: Production Ready
