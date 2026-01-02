"""
Template renderer utility for generating HTML reports from JSON data.

This module provides functionality to render various FinWiz JSON reports
into professional HTML format with dark/light mode support.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape


class TemplateRenderer:
    """Renders JSON data into HTML using Jinja2 templates."""

    def __init__(self, templates_dir: Path | None = None):
        """
        Initialize the template renderer.

        Args:
            templates_dir: Path to templates directory. Defaults to src/finwiz/templates

        """
        if templates_dir is None:
            templates_dir = Path(__file__).parent.parent / "templates"

        self.templates_dir = templates_dir
        self.env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Add custom filters
        self.env.filters["extract"] = self._extract_filter

    def _extract_filter(self, items, mapping):
        """Custom Jinja2 filter to extract values from mapping."""
        return [mapping.get(item, 0) for item in items]

    def render_backtesting_results(self, json_data: dict[str, Any]) -> str:
        """
        Render backtesting results JSON to HTML.

        Args:
            json_data: Backtesting results data

        Returns:
            Rendered HTML string

        """
        template = self.env.get_template("backtesting_results.html")

        context = {
            "title": "Backtesting Results Report",
            "timestamp": datetime.now(),
            "candidates": json_data.get("candidates", []),
            "language": "en",
        }

        return template.render(**context)

    def render_portfolio_review(self, json_data: dict[str, Any]) -> str:
        """
        Render portfolio review JSON to HTML.

        Args:
            json_data: Portfolio review data

        Returns:
            Rendered HTML string

        """
        template = self.env.get_template("portfolio_review.html")

        context = {
            "title": "Portfolio Review Report",
            "timestamp": datetime.now(),
            "base_currency": json_data.get("base_currency", "USD"),
            "holdings": json_data.get("holdings", []),
            "as_of": json_data.get("as_of"),
            "language": "en",
        }

        return template.render(**context)

    def render_a_plus_discovery(self, json_data: dict[str, Any]) -> str:
        """
        Render A+ discovery JSON to HTML.

        Args:
            json_data: A+ discovery data

        Returns:
            Rendered HTML string

        """
        template = self.env.get_template("a_plus_discovery.html")

        # Normalize candidates data to handle different field structures
        candidates = json_data.get("candidates", [])
        normalized_candidates = []

        for candidate in candidates:
            if isinstance(candidate, dict):
                # Handle different field name variations
                ticker = candidate.get("ticker") or candidate.get("symbol", "N/A")
                name = candidate.get("name") or candidate.get("company_name", "N/A")
                grade = candidate.get("grade", "N/A")

                # Handle rationale field - check multiple possible locations
                rationale = None
                if "rationale" in candidate:
                    rationale = candidate["rationale"]
                elif "competitive_moat" in candidate:
                    # For stocks data, combine multiple fields into rationale
                    parts = []
                    if candidate.get("competitive_moat"):
                        parts.append(f"Moat: {candidate['competitive_moat']}")
                    if candidate.get("growth_prospects"):
                        parts.append(f"Growth: {candidate['growth_prospects']}")
                    if candidate.get("valuation_assessment"):
                        parts.append(f"Valuation: {candidate['valuation_assessment']}")
                    rationale = " | ".join(parts) if parts else "Strong fundamentals and market position"
                elif "tokenomics_summary" in candidate:
                    # For crypto data, combine relevant fields
                    parts = []
                    if candidate.get("tokenomics_summary"):
                        parts.append(f"Tokenomics: {candidate['tokenomics_summary']}")
                    if candidate.get("utility_summary"):
                        parts.append(f"Utility: {candidate['utility_summary']}")
                    rationale = " | ".join(parts) if parts else "Strong crypto fundamentals"
                else:
                    rationale = "No rationale provided"

                # Truncate rationale if too long
                if len(rationale) > 500:
                    rationale = rationale[:497] + "..."

                normalized_candidates.append(
                    {
                        "ticker": ticker,
                        "company_name": name,
                        "grade": grade,
                        "rationale": rationale,
                        "asset_type": candidate.get("asset_type", json_data.get("asset_type", "investment")),
                        "criteria_used": candidate.get("criteria_used", {}),
                        "risk_assessment": candidate.get("risk_assessment", {}),
                        "fundamentals": candidate.get("fundamentals", {}),
                    }
                )

        context = {
            "title": f"A+ {json_data.get('asset_type', 'Investment').title()} Discovery",
            "timestamp": datetime.now(),
            "discovery_id": json_data.get("discovery_id"),
            "asset_type": json_data.get("asset_type", "investment"),
            "grade": json_data.get("grade", "A+"),
            "discovery_criteria": json_data.get("discovery_criteria", {}),
            "candidates": normalized_candidates,
            "generated_at": json_data.get("generated_at"),
            "language": "en",
        }

        return template.render(**context)

    def render_deep_analysis_consolidated(self, json_data: dict[str, Any]) -> str:
        """
        Render deep analysis consolidated JSON to HTML.

        Args:
            json_data: Deep analysis consolidated data

        Returns:
            Rendered HTML string

        """
        template = self.env.get_template("deep_analysis_consolidated.html")

        # Extract analyses dict and convert to list
        analyses_dict = json_data.get("analyses", {})
        analysis_results = list(analyses_dict.values()) if analyses_dict else []

        # Parse analysis timestamp
        analysis_timestamp = json_data.get("analysis_timestamp") or json_data.get("analysis_date")
        analysis_date = None
        if analysis_timestamp:
            if isinstance(analysis_timestamp, str):
                try:
                    from dateutil import parser

                    analysis_date = parser.parse(analysis_timestamp)
                except Exception:
                    analysis_date = analysis_timestamp
            else:
                analysis_date = analysis_timestamp

        # Calculate summary statistics
        total_analyses = json_data.get("total_analyses", len(analysis_results))
        a_plus_count = len([a for a in analysis_results if a.get("grade") == "A+"])
        buy_count = len([a for a in analysis_results if a.get("recommendation") == "BUY"])

        context = {
            "title": "Deep Analysis Consolidated Report",
            "timestamp": datetime.now(),
            "session_id": json_data.get("session_id"),
            "analysis_date": analysis_date,
            "total_analyses": total_analyses,
            "a_plus_count": a_plus_count,
            "buy_count": buy_count,
            "analysis_results": analysis_results,
            "exported_files": json_data.get("exported_files", []),
            "language": "en",
        }

        return template.render(**context)

    def render_optimization_report(self, json_data: dict[str, Any]) -> str:
        """
        Render optimization report JSON to HTML.

        Args:
            json_data: Optimization report data

        Returns:
            Rendered HTML string

        """
        template = self.env.get_template("optimization_report.html")

        context = {
            "title": "Portfolio Optimization Report",
            "timestamp": datetime.now(),
            "optimization_status": json_data.get("optimization_status"),
            "total_assets": json_data.get("total_assets"),
            "expected_return": json_data.get("expected_return"),
            "portfolio_risk": json_data.get("portfolio_risk"),
            "current_portfolio": json_data.get("current_portfolio"),
            "optimized_portfolio": json_data.get("optimized_portfolio"),
            "recommendations": json_data.get("recommendations", []),
            "allocation_changes": json_data.get("allocation_changes", []),
            "risk_analysis": json_data.get("risk_analysis"),
            "implementation_timeline": json_data.get("implementation_timeline", []),
            "language": "en",
        }

        return template.render(**context)

    def render_validation_report(self, json_data: dict[str, Any]) -> str:
        """
        Render validation report JSON to HTML.

        Args:
            json_data: Validation report data

        Returns:
            Rendered HTML string

        """
        template = self.env.get_template("validation_report.html")

        context = {
            "title": "Data Validation Report",
            "timestamp": datetime.now(),
            "validation_status": json_data.get("validation_status"),
            "total_checks": json_data.get("total_checks"),
            "passed_checks": json_data.get("passed_checks"),
            "failed_checks": json_data.get("failed_checks"),
            "validation_results": json_data.get("validation_results", []),
            "failed_validations": json_data.get("failed_validations", []),
            "warnings": json_data.get("warnings", []),
            "data_quality_metrics": json_data.get("data_quality_metrics", {}),
            "schema_validation": json_data.get("schema_validation", []),
            "recommendations": json_data.get("recommendations", []),
            "validation_config": json_data.get("validation_config", {}),
            "language": "en",
        }

        return template.render(**context)

    def render_discovery_latest(self, json_data: dict[str, Any]) -> str:
        """
        Render discovery latest JSON to HTML.

        Args:
            json_data: Discovery latest data

        Returns:
            Rendered HTML string

        """
        template = self.env.get_template("discovery_latest.html")

        # Extract data from pydantic field if present (CrewAI output format)
        if "pydantic" in json_data and json_data["pydantic"]:
            data = json_data["pydantic"]
        else:
            data = json_data

        # Calculate summary metrics
        opportunities = data.get("opportunities", [])
        total_opportunities = len(opportunities)
        a_plus_count = len([opp for opp in opportunities if opp.get("grade") == "A+"])

        # Asset class breakdown
        asset_class_breakdown = {}
        for opp in opportunities:
            asset_class = opp.get("asset_class", "unknown")
            asset_class_breakdown[asset_class] = asset_class_breakdown.get(asset_class, 0) + 1

        # Parse discovery date if it's a string
        discovery_date_str = data.get("analysis_date") or data.get("discovery_date")
        discovery_date = None
        if discovery_date_str:
            if isinstance(discovery_date_str, str):
                try:
                    from dateutil import parser

                    discovery_date = parser.parse(discovery_date_str)
                except Exception:
                    discovery_date = discovery_date_str
            else:
                discovery_date = discovery_date_str

        context = {
            "title": "Latest Discovery Report",
            "timestamp": datetime.now(),
            "discovery_date": discovery_date,
            "total_opportunities": total_opportunities,
            "a_plus_count": a_plus_count,
            "asset_classes_count": len(asset_class_breakdown),
            "asset_class_breakdown": asset_class_breakdown,
            "top_opportunities": opportunities[:10],  # Top 10
            "discovery_details": opportunities,
            "discovery_criteria": data.get("screening_criteria") or data.get("discovery_criteria", {}),
            "performance_summary": data.get("performance_summary", {}),
            "market_context": data.get("market_context"),
            "data_sources": data.get("data_sources", []),
            "language": "en",
        }

        return template.render(**context)

    def render_feedback_learning_report(self, json_data: dict[str, Any]) -> str:
        """
        Render feedback learning report JSON to HTML.

        Args:
            json_data: Feedback learning report data

        Returns:
            Rendered HTML string

        """
        template = self.env.get_template("feedback_learning_report.html")

        # Extract data from pydantic field if present (CrewAI output format)
        if "pydantic" in json_data and json_data["pydantic"]:
            data = json_data["pydantic"]
        else:
            data = json_data

        context = {
            "title": "Feedback Learning Report",
            "timestamp": datetime.now(),
            "objective": data.get("objective"),
            "key_findings": data.get("key_findings", []),
            "acceptance_rate": data.get("acceptance_rate"),
            "grade_maintenance_6m": data.get("grade_maintenance_6m"),
            "portfolio_grade_improvement": data.get("portfolio_grade_improvement"),
            "discovery_rate": data.get("discovery_rate"),
            "relative_outperformance": data.get("relative_outperformance"),
            "user_satisfaction": data.get("user_satisfaction"),
            "user_confidence_mean": data.get("user_confidence_mean"),
            "feedback_summary": data.get("feedback_summary", {}),
            "acceptance_by_asset_class": data.get("acceptance_by_asset_class", {}),
            "performance_outcomes": data.get("performance_outcomes", {}),
            "optimization_recommendations": data.get("optimization_recommendations", {}),
            "asset_specific_insights": data.get("asset_specific_insights", {}),
            "implementation_plan": data.get("implementation_plan", []),
            "statistical_analysis": data.get("statistical_analysis", []),
            "rollback_mechanisms": data.get("rollback_mechanisms", {}),
            "next_steps": data.get("next_steps", []),
            "qa_metrics": data.get("qa_metrics", {}),
            "language": "en",
        }

        return template.render(**context)

    def render_portfolio_processing_summary(self, json_data: dict[str, Any]) -> str:
        """
        Render portfolio processing summary JSON to HTML.

        Args:
            json_data: Portfolio processing summary data

        Returns:
            Rendered HTML string

        """
        template = self.env.get_template("portfolio_processing_summary.html")

        context = {
            "title": "Portfolio Processing Summary",
            "timestamp": datetime.now(),
            "processing_status": json_data.get("processing_status"),
            "total_holdings": json_data.get("total_holdings"),
            "processed_holdings": json_data.get("processed_holdings"),
            "start_time": json_data.get("start_time"),
            "end_time": json_data.get("end_time"),
            "processing_steps": json_data.get("processing_steps", []),
            "holdings_status": json_data.get("holdings_status", []),
            "errors": json_data.get("errors", []),
            "performance_metrics": json_data.get("performance_metrics", {}),
            "resource_usage": json_data.get("resource_usage", {}),
            "configuration": json_data.get("configuration", {}),
            "language": "en",
        }

        return template.render(**context)

    def render_from_file(self, json_file_path: Path, template_type: str) -> str:
        """
        Render HTML from JSON file.

        Args:
            json_file_path: Path to JSON file
            template_type: Type of template to use

        Returns:
            Rendered HTML string

        Raises:
            ValueError: If template_type is not supported
            FileNotFoundError: If JSON file doesn't exist

        """
        if not json_file_path.exists():
            raise FileNotFoundError(f"JSON file not found: {json_file_path}")

        try:
            with open(json_file_path, encoding="utf-8") as f:
                json_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {json_file_path}: {e}") from e

        # Map template types to render methods
        render_methods = {
            "backtesting_results": self.render_backtesting_results,
            "portfolio_review": self.render_portfolio_review,
            "a_plus_discovery": self.render_a_plus_discovery,
            "deep_analysis_consolidated": self.render_deep_analysis_consolidated,
            "optimization_report": self.render_optimization_report,
            "validation_report": self.render_validation_report,
            "discovery_latest": self.render_discovery_latest,
            "portfolio_processing_summary": self.render_portfolio_processing_summary,
            "feedback_learning_report": self.render_feedback_learning_report,
        }

        if template_type not in render_methods:
            raise ValueError(f"Unsupported template type: {template_type}. Supported types: {list(render_methods.keys())}")

        return render_methods[template_type](json_data)

    def save_html_report(self, json_file_path: Path, template_type: str, output_path: Path | None = None) -> Path:
        """
        Generate and save HTML report from JSON file.

        Args:
            json_file_path: Path to JSON file
            template_type: Type of template to use
            output_path: Output path for HTML file. If None, uses same name as JSON with .html extension

        Returns:
            Path to generated HTML file

        """
        html_content = self.render_from_file(json_file_path, template_type)

        if output_path is None:
            output_path = json_file_path.with_suffix(".html")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return output_path


def generate_html_reports():
    """Generate HTML reports for all JSON files in output directory."""
    renderer = TemplateRenderer()
    output_dir = Path("output")

    # File mappings: filename pattern -> template type
    file_mappings = {
        "backtesting_results_default.json": "backtesting_results",
        "deep_analysis_consolidated_default.json": "deep_analysis_consolidated",
        "a_plus_crypto.json": "a_plus_discovery",
        "a_plus_etfs.json": "a_plus_discovery",
        "a_plus_stocks.json": "a_plus_discovery",
        "discovery_latest.json": "discovery_latest",
        "optimization_report.json": "optimization_report",
        "validation_report.json": "validation_report",
        "portfolio_review.json": "portfolio_review",
        "portfolio_processing_summary.json": "portfolio_processing_summary",
        "feedback_learning_report.json": "feedback_learning_report",
    }

    generated_files = []

    # Search for files in output directory and subdirectories
    for pattern, template_type in file_mappings.items():
        json_files = list(output_dir.rglob(pattern))

        for json_file in json_files:
            try:
                html_file = renderer.save_html_report(json_file, template_type)
                generated_files.append(html_file)
                print(f"✅ Generated: {html_file}")
            except Exception as e:
                print(f"❌ Failed to generate HTML for {json_file}: {e}")

    print(f"\n📊 Generated {len(generated_files)} HTML reports")
    return generated_files


if __name__ == "__main__":
    generate_html_reports()
