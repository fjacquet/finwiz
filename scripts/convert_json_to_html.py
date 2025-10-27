#!/usr/bin/env python3
"""
Convert JSON analysis files to HTML reports using Jinja2 templates.
This script addresses the issue where JSON files are generated but not converted to HTML.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment


def load_json_file(file_path: Path) -> dict[str, Any]:
    """Load and parse a JSON file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return {}


def get_grade_class(grade: str) -> str:
    """Get CSS class for grade styling."""
    grade_classes = {
        "A+": "grade-a-plus",
        "A": "grade-a",
        "B+": "grade-b",
        "B": "grade-b",
        "C": "grade-c",
        "D": "grade-d",
        "F": "grade-f",
    }
    return grade_classes.get(grade, "grade-b")


def get_recommendation_class(recommendation: str) -> str:
    """Get CSS class for recommendation styling."""
    rec_classes = {"BUY": "recommendation buy", "HOLD": "recommendation hold", "SELL": "recommendation sell"}
    return rec_classes.get(recommendation, "recommendation hold")


def format_percentage(value: float) -> str:
    """Format a decimal as percentage."""
    return f"{value * 100:.1f}%"


def format_currency(value: float) -> str:
    """Format a value as currency."""
    return f"${value:,.2f}"


def create_html_template() -> str:
    """Create the HTML template for individual analysis reports."""
    return """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Analyse {{ ticker }} - FinWiz</title>
    <style>
        /* Base Styles */
        :root {
            --bg-primary: #ffffff;
            --bg-secondary: #f8f9fa;
            --bg-card: #ffffff;
            --text-primary: #2c3e50;
            --text-secondary: #34495e;
            --text-muted: #666;
            --border-color: #ddd;
            --accent: #3498db;
            --success: #27ae60;
            --warning: #f39c12;
            --danger: #e74c3c;
            --shadow: rgba(0, 0, 0, 0.1);
        }

        @media (prefers-color-scheme: dark) {
            :root {
                --bg-primary: #1a1a1a;
                --bg-secondary: #2d2d2d;
                --bg-card: #2d2d2d;
                --text-primary: #ecf0f1;
                --text-secondary: #bdc3c7;
                --text-muted: #95a5a6;
                --border-color: #444;
                --shadow: rgba(0, 0, 0, 0.3);
            }
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: var(--text-primary);
            background-color: var(--bg-secondary);
            margin: 0;
            padding: 20px;
        }

        .container {
            max-width: 1000px;
            margin: 0 auto;
            background-color: var(--bg-primary);
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px var(--shadow);
        }

        h1 {
            color: var(--text-primary);
            font-size: 2.5rem;
            margin-bottom: 1rem;
            border-bottom: 3px solid var(--accent);
            padding-bottom: 0.5rem;
        }

        h2 {
            color: var(--text-secondary);
            font-size: 1.8rem;
            margin-top: 2rem;
            margin-bottom: 1rem;
            border-bottom: 2px solid var(--border-color);
            padding-bottom: 0.5rem;
        }

        h3 {
            color: var(--text-secondary);
            font-size: 1.4rem;
            margin-top: 1.5rem;
            margin-bottom: 0.75rem;
        }

        .grade-a-plus { color: var(--success); font-weight: bold; }
        .grade-a { color: #2ecc71; }
        .grade-b { color: var(--warning); }
        .grade-c { color: #e67e22; }
        .grade-d { color: var(--danger); }
        .grade-f { color: #c0392b; font-weight: bold; }

        .recommendation {
            padding: 1.5rem;
            border-radius: 8px;
            margin: 1.5rem 0;
            background-color: var(--bg-card);
            border-left: 4px solid var(--accent);
        }

        .recommendation.buy {
            border-left-color: var(--success);
            background-color: rgba(39, 174, 96, 0.1);
        }

        .recommendation.sell {
            border-left-color: var(--danger);
            background-color: rgba(231, 76, 60, 0.1);
        }

        .recommendation.hold {
            border-left-color: var(--warning);
            background-color: rgba(243, 156, 18, 0.1);
        }

        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin: 1.5rem 0;
        }

        .metric-card {
            background-color: var(--bg-card);
            border-radius: 8px;
            padding: 1.5rem;
            text-align: center;
            border-left: 4px solid var(--accent);
            box-shadow: 0 2px 5px var(--shadow);
        }

        .metric-card h4 {
            font-size: 1rem;
            color: var(--text-muted);
            margin-bottom: 0.5rem;
            margin-top: 0;
        }

        .metric-value {
            font-size: 2rem;
            font-weight: bold;
            color: var(--text-primary);
        }

        .section {
            background-color: var(--bg-card);
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            box-shadow: 0 2px 5px var(--shadow);
        }

        .footer {
            margin-top: 3rem;
            padding-top: 1.5rem;
            border-top: 1px solid var(--border-color);
            text-align: center;
            color: var(--text-muted);
            font-size: 0.9rem;
        }

        @media (max-width: 768px) {
            body { padding: 10px; }
            .container { padding: 15px; }
            h1 { font-size: 2rem; }
            h2 { font-size: 1.5rem; }
            .metrics-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Analyse {{ ticker }}</h1>
        <p><strong>Classe d'actif:</strong> {{ asset_class|upper }}</p>
        <p><strong>Date d'analyse:</strong> {{ analysis_timestamp }}</p>
        <p><strong>ID d'exécution:</strong> {{ execution_id }}</p>

        <div class="recommendation {{ recommendation_class }}">
            <h2>🎯 Recommandation</h2>
            <p><strong>Note:</strong> <span class="{{ grade_class }}">{{ grade }}</span></p>
            <p><strong>Score composite:</strong> {{ "%.3f"|format(composite_score) }}</p>
            <p><strong>Recommandation:</strong> {{ recommendation }}</p>
            <p><strong>Confiance:</strong> {{ "%.1f"|format(confidence * 100) }}%</p>
        </div>

        <div class="section">
            <h2>📈 Métriques de Performance</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <h4>Score Fondamental</h4>
                    <div class="metric-value">{{ "%.3f"|format(fundamental_score) }}</div>
                </div>
                <div class="metric-card">
                    <h4>Score Technique</h4>
                    <div class="metric-value">{{ "%.3f"|format(technical_score) }}</div>
                </div>
                <div class="metric-card">
                    <h4>Score de Risque</h4>
                    <div class="metric-value">{{ "%.3f"|format(risk_score) }}</div>
                </div>
                <div class="metric-card">
                    <h4>Temps d'Exécution</h4>
                    <div class="metric-value">{{ "%.3f"|format(performance_metrics.execution_time_seconds) }}s</div>
                </div>
            </div>
        </div>

        {% if risk_details %}
        <div class="section">
            <h2>⚠️ Analyse des Risques</h2>
            <div class="metrics-grid">
                {% if risk_details.volatility %}
                <div class="metric-card">
                    <h4>Volatilité</h4>
                    <div class="metric-value">{{ "%.1f"|format(risk_details.volatility * 100) }}%</div>
                </div>
                {% endif %}
                {% if risk_details.max_drawdown %}
                <div class="metric-card">
                    <h4>Drawdown Max</h4>
                    <div class="metric-value">{{ "%.1f"|format(risk_details.max_drawdown * 100) }}%</div>
                </div>
                {% endif %}
                {% if risk_details.beta %}
                <div class="metric-card">
                    <h4>Bêta</h4>
                    <div class="metric-value">{{ "%.2f"|format(risk_details.beta) }}</div>
                </div>
                {% endif %}
            </div>
        </div>
        {% endif %}

        <div class="section">
            <h2>💡 Rationale</h2>
            <p>{{ rationale }}</p>
        </div>

        <div class="section">
            <h2>⚡ Performance d'Exécution</h2>
            <ul>
                <li><strong>Appels LLM:</strong> {{ performance_metrics.llm_calls }}</li>
                <li><strong>Coût:</strong> ${{ "%.4f"|format(performance_metrics.cost_usd) }}</li>
                <li><strong>Temps d'exécution:</strong> {{ "%.3f"|format(performance_metrics.execution_time_seconds) }} secondes</li>
            </ul>
        </div>

        <div class="footer">
            <p><strong>Rapport généré par FinWiz</strong></p>
            <p>Ce rapport est fourni à titre informatif uniquement et ne constitue pas un conseil en investissement.</p>
            <p><em>Généré le {{ current_date }}</em></p>
        </div>
    </div>
</body>
</html>"""


def convert_json_to_html(json_data: dict[str, Any], output_path: Path) -> bool:
    """Convert JSON analysis data to HTML report."""
    try:
        # Create Jinja2 environment
        template_str = create_html_template()
        env = Environment()
        template = env.from_string(template_str)

        # Prepare template data
        template_data = {
            **json_data,
            "grade_class": get_grade_class(json_data.get("grade", "B")),
            "recommendation_class": get_recommendation_class(json_data.get("recommendation", "HOLD")),
            "current_date": datetime.now().strftime("%d %B %Y à %H:%M"),
        }

        # Render HTML
        html_content = template.render(**template_data)

        # Write to file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return True
    except Exception as e:
        print(f"Error converting {output_path}: {e}")
        return False


def main():
    """Main function to convert all JSON files to HTML."""
    base_dir = Path("output")

    # Asset class directories
    asset_dirs = {"stock": base_dir / "stock", "etf": base_dir / "etf", "crypto": base_dir / "crypto"}

    total_converted = 0

    for asset_class, asset_dir in asset_dirs.items():
        if not asset_dir.exists():
            print(f"Directory {asset_dir} does not exist, skipping...")
            continue

        print(f"\n🔄 Processing {asset_class.upper()} files...")

        # Create HTML output directory
        html_dir = base_dir / f"{asset_class}_html"
        html_dir.mkdir(exist_ok=True)

        # Process all JSON files
        json_files = list(asset_dir.glob("*.json"))
        print(f"Found {len(json_files)} JSON files")

        for json_file in json_files:
            # Load JSON data
            json_data = load_json_file(json_file)
            if not json_data:
                continue

            # Create HTML filename
            html_filename = json_file.stem + ".html"
            html_path = html_dir / html_filename

            # Convert to HTML
            if convert_json_to_html(json_data, html_path):
                print(f"✅ Converted {json_file.name} -> {html_filename}")
                total_converted += 1
            else:
                print(f"❌ Failed to convert {json_file.name}")

    print(f"\n🎉 Conversion complete! {total_converted} files converted to HTML")
    print("📁 HTML files saved in:")
    for asset_class in asset_dirs.keys():
        html_dir = base_dir / f"{asset_class}_html"
        if html_dir.exists():
            print(f"   - {html_dir}")


if __name__ == "__main__":
    main()
