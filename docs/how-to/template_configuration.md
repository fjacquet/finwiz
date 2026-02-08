---
title: "Template Configuration"
description: "How to configure and customize Jinja2 templates for FinWiz report generation"
category: "how-to"
tags:
  - "templates"
  - "configuration"
  - "jinja2"
  - "reports"
date: "2025-10-26"
source: "how-to/JINJA2_TEMPLATES.md"
---

# Template Configuration

## Overview

FinWiz uses Jinja2 templates for generating professional HTML reports from Python data structures. This approach provides fast, deterministic, and maintainable report generation without AI costs or variability.

## Template Architecture

### Template Hierarchy

```
src/finwiz/templates/
├── crew_reports/
│   ├── base.html                    # Base template with common layout
│   ├── deep_analysis_report.html.j2 # Deep analysis specific template
│   ├── stock_crew_report.html.j2    # Stock analysis template
│   ├── etf_crew_report.html.j2      # ETF analysis template
│   ├── crypto_crew_report.html.j2   # Crypto analysis template
│   └── final_report.html.j2         # Consolidated final report
├── email/
│   └── notification.html.j2         # Email notification template
└── static/
    ├── css/
    │   ├── base.css                 # Base styles
    │   ├── light-theme.css          # Light mode theme
    │   └── dark-theme.css           # Dark mode theme
    └── js/
        └── theme-switcher.js        # Theme switching logic
```

### Template Inheritance

All report templates extend the base template:

{% raw %}

```jinja
{% extends "crew_reports/base.html" %}

{% block title %}Analyse Approfondie {{ ticker }} - FinWiz{% endblock %}

{% block content %}
<!-- Template-specific content -->
{% endblock %}
```

{% endraw %}

## Deep Analysis Template Structure

### Template Sections

The deep analysis template (`deep_analysis_report.html.j2`) includes:

1. **Header Section**: Ticker, asset class, analysis date
2. **Executive Summary**: Key findings and recommendation
3. **Recommendation Section**: Grade, scores, and rationale
4. **Key Metrics**: Asset-specific fundamental and technical metrics
5. **Risk Assessment**: Risk scores and identified risk factors
6. **Data Sources**: Attribution and metadata

### Input Data Structure

The template expects a structured data dictionary:

```python
template_data = {
    # Basic Information
    "ticker": "AAPL",
    "asset_class": "stock",
    "analysis_date": datetime.now(),
    "session_id": "analysis_2025_01_25",

    # Scores and Grades
    "composite_score": 0.78,        # 0.0-1.0
    "fundamental_score": 0.82,      # 0.0-1.0
    "technical_score": 0.75,        # 0.0-1.0
    "risk_score": 0.77,            # 0.0-1.0 (1.0 = low risk)
    "grade": "A",                  # A+, A, B, C, D, F
    "recommendation": "BUY",        # BUY, HOLD, SELL
    "confidence": 0.85,            # 0.0-1.0
    "rationale": "Strong fundamentals...",

    # Component Details
    "fundamental_details": {
        "roe": 0.25,               # Stock-specific
        "debt_to_equity": 0.3,
        "revenue_growth": 0.15,
        "profit_margin": 0.22,
        # ETF-specific
        "expense_ratio": 0.0015,
        "tracking_error": 0.002,
        "aum": 5000000000,
        # Crypto-specific
        "market_cap": 100000000000,
        "volume_24h": 2000000000,
        "age_years": 5.2
    },

    "technical_details": {
        "rsi": 55.0,
        "trend_direction": "uptrend",
        "current_price": 150.0,
        "moving_avg_50": 145.0,
        "moving_avg_200": 140.0,
        "macd_diff": 0.5
    },

    "risk_details": {
        "volatility": 0.18,
        "max_drawdown": -0.15,
        "beta": 1.1,
        "beta_deviation": 0.1
    },

    # Metadata
    "data_sources": ["Yahoo Finance", "SEC EDGAR", "Alpha Vantage"],
    "report_html_path": "output/reports/.../report.html",
    "report_json_path": "output/reports/.../export.json"
}
```

## Template Features

### French Localization

All templates use professional French financial terminology:

{% raw %}

```jinja2
<!-- Executive Summary -->
<h2>📋 Résumé Exécutif</h2>
<p>
    L'analyse approfondie de <strong>{{ ticker }}</strong> révèle un actif de classe {{ asset_class|upper }}
    avec un score composite de <strong>{{ "%.1f"|format(composite_score * 100) }}%</strong>
    et une note de <strong>{{ grade }}</strong>.
</p>

<!-- Recommendation -->
<h2>💡 Recommandation</h2>
<p>Notre recommandation est de <strong>{{ recommendation }}</strong> cet actif</p>
```

{% endraw %}

**Key French Terms:**

- **Résumé Exécutif**: Executive Summary
- **Recommandation**: Recommendation
- **Métriques Clés**: Key Metrics
- **Analyse Fondamentale**: Fundamental Analysis
- **Analyse Technique**: Technical Analysis
- **Évaluation des Risques**: Risk Assessment
- **Sources de Données**: Data Sources

### Responsive Design

Templates include responsive CSS for multiple screen sizes:

```css
/* Mobile-first responsive design */
.metrics-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 1rem;
}

@media (min-width: 768px) {
    .metrics-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (min-width: 1024px) {
    .metrics-grid {
        grid-template-columns: repeat(3, 1fr);
    }
}
```

### Light/Dark Mode Support

Templates support automatic theme switching:

```css
/* CSS Custom Properties for theming */
:root {
    --bg-primary: #ffffff;
    --text-primary: #2c3e50;
    --accent-color: #3498db;
}

[data-theme="dark"] {
    --bg-primary: #1a1a1a;
    --text-primary: #ecf0f1;
    --accent-color: #5dade2;
}

body {
    background-color: var(--bg-primary);
    color: var(--text-primary);
}
```

### Asset-Specific Sections

Templates dynamically show relevant metrics based on asset class:

{% raw %}

```jinja

<!-- Stock-specific metrics -->
{% if asset_class == 'stock' %}
    {% if fundamental_details.roe is defined %}
    <div class="metric-card">
        <h4>ROE (Rendement des Capitaux Propres)</h4>
        <p class="metric-value">{{ "%.1f"|format(fundamental_details.roe * 100) }}%</p>
    </div>
    {% endif %}
{% endif %}

<!-- ETF-specific metrics -->
{% elif asset_class == 'etf' %}
    {% if fundamental_details.expense_ratio is defined %}
    <div class="metric-card">
        <h4>Ratio de Frais</h4>
        <p class="metric-value">{{ "%.2f"|format(fundamental_details.expense_ratio) }}%</p>
    </div>
    {% endif %}
{% endif %}

<!-- Crypto-specific metrics -->
{% elif asset_class == 'crypto' %}
    {% if fundamental_details.market_cap is defined %}
    <div class="metric-card">
        <h4>Capitalisation Boursière</h4>
        <p class="metric-value">${{ "%.1f"|format(fundamental_details.market_cap / 1e9) }}B</p>
    </div>
    {% endif %}
{% endif %}

```

{% endraw %}

### Conditional Formatting

Templates include conditional CSS classes based on values:

{% raw %}

```jinja

<!-- Risk-based color coding -->
<p class="metric-value {% if technical_details.rsi < 30 %}risk-high{% elif technical_details.rsi > 70 %}risk-high{% else %}risk-low{% endif %}">
    {{ "%.1f"|format(technical_details.rsi) }}
</p>

<!-- Grade-based styling -->
<p class="grade-{{ grade|lower|replace('+', '-plus') }}" style="font-size: 1.5rem;">
    {% if recommendation == 'BUY' %}✅{% elif recommendation == 'SELL' %}❌{% else %}⏸️{% endif %}
    <strong>{{ recommendation }}</strong> - Grade {{ grade }}
</p>

```

{% endraw %}

**CSS Classes:**

```css
.risk-low { color: #27ae60; }      /* Green for low risk */
.risk-medium { color: #f39c12; }   /* Orange for medium risk */
.risk-high { color: #e74c3c; }     /* Red for high risk */

.grade-a-plus { color: #27ae60; font-weight: bold; }
.grade-a { color: #2ecc71; }
.grade-b { color: #f39c12; }
.grade-c { color: #e67e22; }
.grade-d { color: #e74c3c; }
.grade-f { color: #c0392b; font-weight: bold; }
```

## Template Customization

### Adding New Sections

To add a new section to the template:

1. **Define the section structure**:
{% raw %}

```jinja

<!-- New Performance Metrics Section -->
<div class="section performance-metrics">
    <h2>📈 Métriques de Performance</h2>
    {% if performance_data %}
    <div class="metrics-grid">
        {% if performance_data.sharpe_ratio is defined %}
        <div class="metric-card">
            <h4>Ratio de Sharpe</h4>
            <p class="metric-value">{{ "%.2f"|format(performance_data.sharpe_ratio) }}</p>
        </div>
        {% endif %}
    </div>
    {% endif %}
</div>

```

{% endraw %}

1. **Add corresponding CSS**:

```css
.performance-metrics {
    margin: 2rem 0;
    padding: 1.5rem;
    border-left: 4px solid var(--accent-color);
}

.performance-metrics h2 {
    color: var(--accent-color);
    margin-bottom: 1rem;
}
```

1. **Update data structure**:

```python
template_data["performance_data"] = {
    "sharpe_ratio": 1.25,
    "sortino_ratio": 1.45,
    "max_drawdown": -0.15,
    "calmar_ratio": 0.85
}
```

### Custom Filters

Add custom Jinja2 filters for specialized formatting:

```python
def format_currency(value, currency="USD"):
    """Format currency values."""
    if currency == "USD":
        return f"${value:,.2f}"
    elif currency == "EUR":
        return f"€{value:,.2f}"
    return f"{value:,.2f} {currency}"

def format_percentage(value, decimals=1):
    """Format percentage values."""
    return f"{value * 100:.{decimals}f}%"

def risk_level_text(risk_score):
    """Convert risk score to text."""
    if risk_score >= 0.7:
        return "Faible"
    elif risk_score >= 0.4:
        return "Modéré"
    else:
        return "Élevé"

# Register filters
jinja_env.filters['currency'] = format_currency
jinja_env.filters['percentage'] = format_percentage
jinja_env.filters['risk_level'] = risk_level_text
```

**Usage in templates**:
{% raw %}

```jinja2
<p>Prix: {{ current_price|currency("USD") }}</p>
<p>Croissance: {{ revenue_growth|percentage(1) }}</p>
<p>Risque: {{ risk_score|risk_level }}</p>
```

{% endraw %}

### Template Inheritance

Create specialized templates by extending the base:

{% raw %}

```jinja

<!-- etf_deep_analysis_report.html.j2 -->
{% extends "crew_reports/deep_analysis_report.html.j2" %}

{% block asset_specific_metrics %}
<!-- ETF-specific additional metrics -->
<div class="section etf-specific">
    <h3>📊 Métriques ETF Spécialisées</h3>

    {% if holdings_data %}
    <h4>Top Holdings</h4>
    <table class="holdings-table">
        <thead>
            <tr>
                <th>Titre</th>
                <th>Poids</th>
                <th>Secteur</th>
            </tr>
        </thead>
        <tbody>
            {% for holding in holdings_data[:10] %}
            <tr>
                <td>{{ holding.symbol }}</td>
                <td>{{ "%.1f"|format(holding.weight * 100) }}%</td>
                <td>{{ holding.sector }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% endif %}
</div>
{% endblock %}

```

{% endraw %}

## Report Generation

### DeepAnalysisReportGenerator

The report generator handles template rendering:

```python
from finwiz.reporting.deep_analysis_report_generator import DeepAnalysisReportGenerator

class DeepAnalysisReportGenerator:
    """Generate HTML reports from DeepAnalysisResult using Jinja2 templates."""

    def __init__(self):
        """Initialize report generator with Jinja2 environment."""
        template_dir = Path(__file__).parent.parent / "templates"
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )

        # Register custom filters
        self._register_custom_filters()

    def generate_report(
        self,
        result: DeepAnalysisResult,
        detailed_analysis: Dict[str, Any],
        output_path: str
    ) -> str:
        """Generate HTML report from analysis result."""

        # Prepare template data
        template_data = self._prepare_template_data(result, detailed_analysis)

        # Load and render template
        template = self.jinja_env.get_template("crew_reports/deep_analysis_report.html.j2")
        html_content = template.render(**template_data)

        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return output_path
```

### Performance Characteristics

**Template Rendering Performance:**

- **Execution Time**: <100ms per report
- **Memory Usage**: <10MB per report
- **CPU Usage**: Minimal (template compilation cached)
- **Scalability**: 1000+ reports per minute

**Benefits over AI Generation:**

- **Speed**: 100-1000x faster than AI report generation
- **Cost**: $0 vs $0.01-0.05 per report
- **Consistency**: 100% consistent formatting
- **Reliability**: No hallucinations or errors
- **Maintainability**: Developers can edit templates directly

## Testing Templates

### Unit Testing

Test template rendering with mock data:

```python
def test_should_render_deep_analysis_template_with_stock_data():
    """Test deep analysis template rendering for stocks."""
    generator = DeepAnalysisReportGenerator()

    # Mock DeepAnalysisResult
    result = DeepAnalysisResult(
        ticker="AAPL",
        asset_class="stock",
        composite_score=0.78,
        grade="A",
        recommendation="BUY",
        confidence=0.85,
        rationale="Strong fundamentals support BUY recommendation.",
        fundamental_score=0.82,
        technical_score=0.75,
        risk_score=0.77,
        fundamental_details={"roe": 0.25, "debt_to_equity": 0.3},
        technical_details={"rsi": 55.0, "trend_direction": "uptrend"},
        risk_details={"volatility": 0.18, "max_drawdown": -0.15}
    )

    # Mock detailed analysis
    detailed_analysis = {
        "data_sources": ["Yahoo Finance", "SEC EDGAR"],
        "analysis_timestamp": "2025-01-25T10:30:00Z"
    }

    # Generate report
    output_path = "/tmp/test_report.html"
    generated_path = generator.generate_report(result, detailed_analysis, output_path)

    # Verify file created
    assert Path(generated_path).exists()

    # Verify HTML content
    with open(generated_path, 'r') as f:
        html_content = f.read()

    assert "AAPL" in html_content
    assert "Grade A" in html_content
    assert "BUY" in html_content
    assert "78%" in html_content  # Composite score
```

### Visual Testing

Test template appearance across different scenarios:

```python
def test_template_visual_scenarios():
    """Test template rendering for different visual scenarios."""
    scenarios = [
        # High-grade stock
        {"ticker": "AAPL", "grade": "A+", "recommendation": "BUY", "asset_class": "stock"},
        # Low-grade crypto
        {"ticker": "DOGE", "grade": "D", "recommendation": "SELL", "asset_class": "crypto"},
        # Medium-grade ETF
        {"ticker": "SPY", "grade": "B", "recommendation": "HOLD", "asset_class": "etf"},
    ]

    for scenario in scenarios:
        result = create_mock_result(**scenario)
        html = generator.generate_report(result, {}, f"/tmp/{scenario['ticker']}.html")

        # Verify scenario-specific content
        with open(html, 'r') as f:
            content = f.read()

        assert scenario["grade"] in content
        assert scenario["recommendation"] in content
        assert scenario["asset_class"].upper() in content
```

### Accessibility Testing

Ensure templates meet accessibility standards:

```python
def test_template_accessibility():
    """Test template accessibility compliance."""
    html_content = generate_sample_report()

    # Parse HTML
    soup = BeautifulSoup(html_content, 'html.parser')

    # Check for required accessibility features
    assert soup.find('html').get('lang') == 'fr'  # Language specified
    assert soup.find('title') is not None         # Title present

    # Check heading hierarchy
    headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    assert len(headings) > 0
    assert headings[0].name == 'h1'  # Starts with h1

    # Check alt text for images (if any)
    images = soup.find_all('img')
    for img in images:
        assert img.get('alt') is not None

    # Check color contrast (would need additional tools)
    # Check keyboard navigation (would need browser testing)
```

## Template Maintenance

### Version Control

Track template changes with clear commit messages:

```bash
# Template update examples
git commit -m "feat(templates): Add ESG metrics section to deep analysis template"
git commit -m "fix(templates): Correct French translation for risk assessment"
git commit -m "style(templates): Improve mobile responsiveness for metrics grid"
```

### Documentation Updates

Keep template documentation synchronized:

1. **Update this document** when adding new sections or features
2. **Document data requirements** for new template variables
3. **Provide usage examples** for custom filters or functions
4. **Update test cases** to cover new template features

### Performance Monitoring

Monitor template rendering performance:

```python
import time
from finwiz.utils.performance_monitor import PerformanceMonitor

def monitor_template_performance():
    """Monitor template rendering performance."""
    monitor = PerformanceMonitor()

    start_time = time.time()
    html_content = generator.generate_report(result, detailed_analysis, output_path)
    render_time = time.time() - start_time

    # Log performance metrics
    monitor.log_template_render(
        template_name="deep_analysis_report",
        render_time=render_time,
        output_size=len(html_content),
        data_complexity=len(detailed_analysis)
    )

    # Alert if performance degrades
    if render_time > 0.5:  # 500ms threshold
        logger.warning(f"Template rendering slow: {render_time:.2f}s")
```

## Best Practices

### Template Organization

1. **Use template inheritance** to avoid duplication
2. **Keep templates focused** - one template per report type
3. **Separate logic from presentation** - use Python for calculations
4. **Use meaningful variable names** in templates
5. **Comment complex template logic**

### Data Preparation

1. **Validate data before rendering** using Pydantic models
2. **Handle missing data gracefully** with default values
3. **Format data in Python** before passing to templates
4. **Use consistent data structures** across all templates

### Performance Optimization

1. **Cache compiled templates** for repeated use
2. **Minimize template complexity** - move logic to Python
3. **Use efficient filters** and avoid expensive operations
4. **Optimize CSS and JavaScript** for faster loading

### Internationalization

1. **Use translation functions** for user-facing text
2. **Support multiple currencies** and number formats
3. **Handle right-to-left languages** if needed
4. **Test with different locales**

## Troubleshooting

### Common Issues

**Issue**: Template not found

```python
# Solution: Check template path and loader configuration
template_dir = Path(__file__).parent.parent / "templates"
assert template_dir.exists(), f"Template directory not found: {template_dir}"

loader = FileSystemLoader(template_dir)
env = Environment(loader=loader)
```

**Issue**: Missing template variables

```python
# Solution: Provide default values
template_data = {
    "ticker": result.ticker,
    "grade": result.grade,
    "recommendation": result.recommendation,
    # Provide defaults for optional fields
    "data_sources": template_data.get("data_sources", ["Internal Analysis"]),
    "analysis_date": template_data.get("analysis_date", datetime.now())
}
```

**Issue**: Formatting errors
{% raw %}

```jinja

<!-- Solution: Use safe filters and error handling -->
{{ value|default("N/A") }}
{{ percentage_value|default(0)|round(1) }}%
{% if complex_data is defined and complex_data %}
    <!-- Render complex data -->
{% else %}
    <p>Données non disponibles</p>
{% endif %}

```

{% endraw %}

### Debug Mode

Enable template debugging for development:

```python
# Enable debug mode
jinja_env = Environment(
    loader=FileSystemLoader(template_dir),
    autoescape=select_autoescape(['html', 'xml']),
    undefined=StrictUndefined  # Raise errors for undefined variables
)

# Add debug information to templates
template_data["debug_info"] = {
    "render_time": datetime.now(),
    "template_version": "1.0",
    "data_keys": list(template_data.keys())
}
```

## Conclusion

The Jinja2 template system in FinWiz provides:

- **Professional report generation** with consistent formatting
- **French localization** for international users
- **Responsive design** for multiple devices
- **Asset-specific customization** for different analysis types
- **High performance** with <100ms rendering times
- **Full maintainability** by developers
- **Complete testability** with unit and visual tests

This template system enables FinWiz to generate high-quality reports at scale while maintaining the flexibility to customize and extend report formats as needed.

---

**Version**: 1.0
**Last Updated**: 2025-01-25
**Related Documentation**:

- [Python Scoring Engine Documentation](PYTHON_SCORING_ENGINE.md)
- Deep Analysis Report Generator API
- [Template Testing Guide](TEMPLATE_TESTING.md)
