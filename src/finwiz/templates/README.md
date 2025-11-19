# FinWiz HTML Templates

Professional HTML report templates with dark/light mode support for FinWiz JSON outputs.

## Overview

This directory contains Jinja2 templates that convert FinWiz JSON data into professional, responsive HTML reports. All templates support:

- **Dark/Light Mode Toggle** - Users can switch themes with a button
- **Responsive Design** - Works on desktop, tablet, and mobile
- **Professional Styling** - Clean, modern design with proper typography
- **Print Support** - Optimized for PDF generation and printing
- **Accessibility** - Screen reader friendly with proper ARIA labels

## Template Structure

### Base Template

- `base_template.html` - Master template with shared CSS, JavaScript, and layout
- All other templates extend this base template
- Contains theme switching logic and responsive design

### Report Templates

| Template | JSON File Pattern | Description |
|----------|------------------|-------------|
| `backtesting_results.html` | `backtesting_results_*.json` | Investment candidate backtesting analysis |
| `portfolio_review.html` | `portfolio_review.json` | Complete portfolio holdings review |
| `a_plus_discovery.html` | `a_plus_*.json` | A+ investment opportunity discovery |
| `deep_analysis_consolidated.html` | `deep_analysis_consolidated_*.json` | Consolidated deep analysis results |
| `optimization_report.html` | `optimization_report.json` | Portfolio optimization recommendations |
| `validation_report.html` | `validation_report.json` | Data validation and quality checks |
| `feedback_learning_report.html` | `feedback_learning_report.json` | Feedback learning and criteria optimization |
| `discovery_latest.html` | `discovery_latest.json` | Latest investment discovery results |
| `portfolio_processing_summary.html` | `portfolio_processing_summary.json` | Processing status and performance |

## Usage

### Command Line

Generate all HTML reports:
```bash
# Using Python script
python scripts/generate_html_reports.py --all

# Using Makefile
make html-reports
```

Generate specific report:
```bash
# Using Python script
python scripts/generate_html_reports.py --file output/portfolio_review.json --type portfolio_review

# Using Makefile
make html-report FILE=output/portfolio_review.json TYPE=portfolio_review
```

### Programmatic Usage

```python
from finwiz.utils.template_renderer import TemplateRenderer

# Initialize renderer
renderer = TemplateRenderer()

# Generate HTML from JSON file
html_content = renderer.render_from_file(
    json_file_path=Path("output/portfolio_review.json"),
    template_type="portfolio_review"
)

# Save HTML file
html_file = renderer.save_html_report(
    json_file_path=Path("output/portfolio_review.json"),
    template_type="portfolio_review",
    output_path=Path("reports/portfolio.html")  # Optional
)
```

## Template Types

### `backtesting_results`
- **Purpose**: Display investment candidate performance analysis
- **Key Features**: Candidate rankings, grade distribution, asset class breakdown
- **Data Structure**: Array of candidates with ticker, grade, score, recommendation

### `portfolio_review`
- **Purpose**: Comprehensive portfolio holdings analysis
- **Key Features**: Holdings table, risk assessment, keep/sell decisions
- **Data Structure**: Holdings array with grades, decisions, risk factors

### `a_plus_discovery`
- **Purpose**: A+ investment opportunity presentation
- **Key Features**: Discovery criteria, candidate details, performance insights
- **Data Structure**: Discovery metadata with candidates array

### `deep_analysis_consolidated`
- **Purpose**: Consolidated deep analysis results
- **Key Features**: Analysis summary, detailed results table, individual breakdowns
- **Data Structure**: Analysis results array with grades, recommendations, metrics

### `optimization_report`
- **Purpose**: Portfolio optimization recommendations
- **Key Features**: Current vs optimized comparison, allocation changes, risk analysis
- **Data Structure**: Optimization results with before/after metrics

### `validation_report`
- **Purpose**: Data quality and validation status
- **Key Features**: Validation summary, failed checks, schema validation
- **Data Structure**: Validation results with status, errors, recommendations

### `discovery_latest`
- **Purpose**: Latest investment discovery results
- **Key Features**: Discovery summary, top opportunities, performance metrics
- **Data Structure**: Discovery metadata with opportunities array

### `portfolio_processing_summary`
- **Purpose**: Processing status and performance metrics
- **Key Features**: Processing timeline, holdings status, error summary
- **Data Structure**: Processing metadata with steps and status arrays

## Styling Features

### Theme Support

The templates use CSS custom properties (variables) for theming:

```css
:root {
    --bg-primary: #ffffff;
    --text-primary: #212529;
    --accent-primary: #0d6efd;
    /* ... more variables */
}

[data-theme="dark"] {
    --bg-primary: #212529;
    --text-primary: #f8f9fa;
    /* ... dark theme overrides */
}
```

### Responsive Design

- **Desktop**: Full layout with multi-column grids
- **Tablet**: Adjusted grid layouts and spacing
- **Mobile**: Single-column layout with optimized touch targets

### Grade and Status Styling

```css
.grade-a-plus { color: var(--success-color); font-weight: 700; }
.grade-a { color: #28a745; font-weight: 600; }
.grade-b { color: var(--warning-color); font-weight: 600; }
.status-buy { background-color: rgba(25, 135, 84, 0.1); }
.status-sell { background-color: rgba(220, 53, 69, 0.1); }
```

## Customization

### Adding New Templates

1. Create new template file extending `base_template.html`:

```html
{% raw %}
{% extends "base_template.html" %}

{% block content %}
<!-- Your template content -->
{% endblock %}
{% endraw %}
```

2. Add render method to `TemplateRenderer`:
```python
def render_my_report(self, json_data: Dict[str, Any]) -> str:
    template = self.env.get_template('my_report.html')
    context = {
        'title': 'My Report',
        'timestamp': datetime.now(),
        'data': json_data,
        'language': 'en'
    }
    return template.render(**context)
```

3. Update file mappings in `generate_html_reports()`:
```python
file_mappings = {
    'my_report.json': 'my_report',
    # ... existing mappings
}
```

### Custom Styling

Override CSS variables in your template:
```html
<style>
:root {
    --accent-primary: #your-color;
    --bg-primary: #your-bg;
}
</style>
```

### JavaScript Enhancements

Add custom JavaScript in your template:
```html
<script>
document.addEventListener('DOMContentLoaded', function() {
    // Your custom JavaScript
});
</script>
```

## Best Practices

### Template Development

1. **Extend Base Template**: Always extend `base_template.html` for consistency
2. **Use CSS Variables**: Leverage theme variables for colors and spacing
3. **Responsive Design**: Test on multiple screen sizes
4. **Accessibility**: Include proper ARIA labels and semantic HTML
5. **Performance**: Minimize inline styles and scripts

### Data Handling

1. **Null Safety**: Always check for null/undefined values
2. **Default Values**: Provide sensible defaults using Jinja2 filters
3. **Type Checking**: Validate data types before rendering
4. **Error Handling**: Gracefully handle missing or malformed data

### Styling Guidelines

1. **Consistent Spacing**: Use utility classes (mb-1, mt-2, etc.)
2. **Color Coding**: Use semantic colors for grades and statuses
3. **Typography**: Maintain consistent font weights and sizes
4. **Interactive Elements**: Provide hover states and transitions

## Troubleshooting

### Common Issues

**Template Not Found**:
```
jinja2.exceptions.TemplateNotFound: my_template.html
```
- Ensure template file exists in templates directory
- Check file name spelling and extension

**Missing Data Errors**:

```text
'dict object' has no attribute 'field_name'
```

- Add null checks: {% raw %}`{{ data.field_name if data.field_name else 'N/A' }}`{% endraw %}
- Use default filter: {% raw %}`{{ data.field_name | default('N/A') }}`{% endraw %}

**CSS Not Loading**:
- Ensure base template is properly extended
- Check CSS variable names match theme definitions
- Verify responsive breakpoints

### Debugging

Enable template debugging:
```python
renderer = TemplateRenderer()
renderer.env.globals['debug'] = True
```

Add debug output in templates:

```html
{% raw %}
{% if debug %}
<pre>{{ data | tojson(indent=2) }}</pre>
{% endif %}
{% endraw %}
```

## File Structure

```
src/finwiz/templates/
├── README.md                           # This file
├── base_template.html                  # Master template
├── backtesting_results.html           # Backtesting analysis
├── portfolio_review.html              # Portfolio holdings
├── a_plus_discovery.html              # A+ opportunities
├── deep_analysis_consolidated.html    # Deep analysis results
├── optimization_report.html           # Portfolio optimization
├── validation_report.html             # Data validation
├── discovery_latest.html              # Latest discoveries
├── portfolio_processing_summary.html  # Processing status
└── crew_reports/                      # Legacy crew reports
    └── ...
```

## Dependencies

- **Jinja2**: Template engine
- **Python 3.8+**: Runtime environment
- **Modern Browser**: For theme switching and responsive features

## Contributing

When adding new templates:

1. Follow existing naming conventions
2. Extend base template for consistency
3. Include responsive design considerations
4. Add proper documentation
5. Test with sample data
6. Update this README

---

**Version**: 1.0  
**Last Updated**: 2025-10-27  
**Maintainer**: FinWiz Development Team