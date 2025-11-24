"""
JSON to HTML Converter Utility.

Converts all JSON output files to HTML using Jinja2 templates.
This ensures all analysis results have both machine-readable (JSON) and
human-readable (HTML) formats.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class JsonToHtmlConverter:
    """
    Convert JSON output files to HTML using Jinja2 templates.

    Maps JSON files to their corresponding templates and generates
    professional HTML reports for human consumption.
    """

    # Mapping of JSON file patterns to template names
    TEMPLATE_MAPPING = {
        "portfolio_review.json": "portfolio_review.html",
        "portfolio_processing_summary.json": "portfolio_processing_summary.html",
        "backtesting_results_*.json": "backtesting_results.html",
        "deep_analysis_consolidated_*.json": "deep_analysis_consolidated.html",
        "deep_analysis_stock_*.json": "enriched_analysis_report.html",
        "deep_analysis_etf_*.json": "enriched_analysis_report.html",
        "deep_analysis_crypto_*.json": "enriched_analysis_report.html",
        "discovery_output_*.json": "discovery_latest.html",
        "discovery_latest.json": "discovery_latest.html",
        "a_plus_stocks.json": "a_plus_discovery.html",
        "a_plus_etfs.json": "a_plus_discovery.html",
        "a_plus_crypto.json": "a_plus_discovery.html",
        "feedback_learning_report.json": "feedback_learning_report.html",
        "validation_report.json": "validation_report.html",
        "optimization_report.json": "optimization_report.html",
        "consolidated_report.json": "consolidated_report.html",
    }

    def __init__(self, template_dir: str = "src/finwiz/templates"):
        """
        Initialize the converter with template directory.

        Args:
            template_dir: Path to Jinja2 templates directory

        """
        self.template_dir = Path(template_dir)
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        logger.info(f"JsonToHtmlConverter initialized with template_dir: {template_dir}")

    def convert_file(self, json_path: Path) -> str | None:
        """
        Convert a single JSON file to HTML.

        Args:
            json_path: Path to JSON file

        Returns:
            Path to generated HTML file, or None if conversion failed

        """
        try:
            # Find matching template
            template_name = self._find_template_for_file(json_path)
            if not template_name:
                logger.debug(f"No template found for {json_path.name}")
                return None

            # Load JSON data
            try:
                with open(json_path, encoding="utf-8") as f:
                    data = json.load(f)
            except json.JSONDecodeError as e:
                logger.warning(f"Skipping malformed JSON file {json_path.name}: {e}")
                return None
            except Exception as e:
                logger.warning(f"Skipping unreadable file {json_path.name}: {e}")
                return None

            # Skip empty files
            if not data:
                logger.debug(f"Skipping empty JSON file {json_path.name}")
                return None

            # Load template
            try:
                template = self.env.get_template(template_name)
            except TemplateNotFound:
                logger.warning(f"Template not found: {template_name}")
                return None

            # Prepare template context
            context = self._prepare_context(data, json_path)

            # Render template
            html_content = template.render(**context)

            # Save HTML file
            html_path = json_path.with_suffix(".html")
            html_path.write_text(html_content, encoding="utf-8")

            logger.info(f"✅ Generated HTML: {html_path}")
            return str(html_path)

        except Exception as e:
            logger.warning(f"Failed to convert {json_path.name}: {str(e)}")
            return None

    def convert_directory(self, output_dir: Path = Path("output")) -> dict[str, list[str]]:
        """
        Convert all JSON files in output directory to HTML.

        Args:
            output_dir: Root output directory to scan

        Returns:
            Dict with 'success' and 'failed' lists of file paths

        """
        results = {"success": [], "failed": []}

        # Find all JSON files
        json_files = list(output_dir.rglob("*.json"))
        logger.info(f"Found {len(json_files)} JSON files to convert")

        for json_path in json_files:
            # Skip files in certain directories
            if any(skip in str(json_path) for skip in ["__pycache__", ".pytest_cache", "node_modules"]):
                continue

            html_path = self.convert_file(json_path)
            if html_path:
                results["success"].append(str(json_path))
            else:
                results["failed"].append(str(json_path))

        logger.info(f"Conversion complete: {len(results['success'])} succeeded, {len(results['failed'])} failed")
        return results

    def _find_template_for_file(self, json_path: Path) -> str | None:
        """
        Find the appropriate template for a JSON file.

        Args:
            json_path: Path to JSON file

        Returns:
            Template name, or None if no match found

        """
        filename = json_path.name

        # Check exact matches first
        if filename in self.TEMPLATE_MAPPING:
            return self.TEMPLATE_MAPPING[filename]

        # Check pattern matches
        for pattern, template in self.TEMPLATE_MAPPING.items():
            if "*" in pattern:
                # Convert glob pattern to simple prefix/suffix check
                prefix = pattern.split("*")[0]
                suffix = pattern.split("*")[-1]
                if filename.startswith(prefix) and filename.endswith(suffix):
                    return template

        # Special handling for deep analysis individual files
        if json_path.parent.name in ["stock", "etf", "crypto"]:
            # Individual deep analysis results
            return "crew_reports/deep_analysis_report.html.j2"

        return None

    def _prepare_context(self, data: dict[str, Any], json_path: Path) -> dict[str, Any]:
        """
        Prepare template context from JSON data.

        Args:
            data: JSON data dictionary
            json_path: Path to source JSON file

        Returns:
            Context dictionary for template rendering

        """
        # Start with all JSON data
        context = data.copy()

        # Add metadata - use datetime object, not string
        context["generation_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        context["timestamp"] = datetime.now()  # For templates expecting datetime object
        context["source_file"] = str(json_path)

        # Add special handling for specific file types
        if "portfolio_review" in json_path.name:
            context.setdefault("base_currency", "USD")
            context.setdefault("holdings", [])

        elif "a_plus" in json_path.name:
            # For A+ discovery files, infer asset type from filename
            asset_type = self._infer_asset_class(json_path)
            context.setdefault("asset_type", asset_type)
            context.setdefault("asset_class", asset_type)
            context.setdefault("grade", "A+")

        elif "discovery" in json_path.name:
            context.setdefault("asset_class", self._infer_asset_class(json_path))

        elif "backtesting" in json_path.name:
            context.setdefault("strategy_name", "Default Strategy")

        # Handle deep_analysis output format with raw_output string
        elif "deep_analysis" in json_path.name and "raw_output" in data:
            # Parse the raw_output string to extract fields
            raw_output = data.get("raw_output", "")
            context = self._parse_raw_output(raw_output, context)

            # Add default values for missing template fields
            context.setdefault("processing_time_seconds", 0.0)
            context.setdefault("llm_cost_dollars", 0.0)
            context.setdefault("company_name", context.get("ticker", "Unknown"))
            context.setdefault("analysis_date", datetime.now())
            context.setdefault("executive_summary", context.get("rationale", "No summary available"))
            context.setdefault("final_recommendation", context.get("recommendation", "HOLD"))
            context.setdefault("final_grade", context.get("grade", "N/A"))
            context.setdefault("recommendation_confidence", "Medium")
            context.setdefault("final_score", context.get("composite_score", 0.0))
            context.setdefault("investment_rationale", context.get("rationale", ""))

            # Extract metrics from parsed details
            context.setdefault("fundamental_metrics", context.get("fundamental_details", {}))
            context.setdefault("technical_indicators", context.get("technical_details", {}))
            context.setdefault("risk_metrics", context.get("risk_details", {}))

            # Set default empty structures for missing sections
            context.setdefault("sec_insights", {
                "business_model": "Not available",
                "competitive_advantages": [],
                "strategic_initiatives": []
            })
            context.setdefault("fundamental_context", {
                "industry_analysis": "Not available",
                "growth_drivers": [],
                "competitive_positioning": "Not available",
                "management_assessment": "Not available"
            })
            context.setdefault("technical_strategy", {
                "chart_patterns": [],
                "support_resistance": "Not available",
                "entry_exit_strategy": "Not available",
                "timing_assessment": "Not available"
            })
            context.setdefault("contextual_risks", {
                "regulatory_risks": [],
                "geopolitical_risks": [],
                "competitive_risks": [],
                "operational_risks": [],
                "stress_scenarios": []
            })
            context.setdefault("investment_synthesis", {
                "scenario_probabilities": {"bull": 0.33, "base": 0.34, "bear": 0.33},
                "bull_case": "Not available",
                "base_case": "Not available",
                "bear_case": "Not available",
                "action_plan": {
                    "immediate_actions": [],
                    "monitoring_points": [],
                    "exit_triggers": []
                }
            })
            context.setdefault("report_word_count", 0)
            context.setdefault("unique_insights_count", 0)
            context.setdefault("qualitative", {"ai_confidence": 0.0})

        return context

    def _infer_asset_class(self, json_path: Path) -> str:
        """Infer asset class from file path or name."""
        name_lower = json_path.name.lower()
        if "stock" in name_lower:
            return "stock"
        elif "etf" in name_lower:
            return "etf"
        elif "crypto" in name_lower:
            return "crypto"
        return "mixed"

    def _parse_raw_output(self, raw_output: str, context: dict[str, Any]) -> dict[str, Any]:
        """
        Parse raw_output string from deep analysis to extract fields.

        The raw_output is a string representation of a Pydantic model with key=value pairs.

        Args:
            raw_output: String containing key=value pairs
            context: Existing context dictionary to update

        Returns:
            Updated context dictionary

        """
        import re

        # Extract simple key=value pairs (for strings, numbers, booleans)
        simple_pattern = r"(\w+)=(['\"]?)([^'\"=\s{}[\]]+)\2(?=\s+\w+=|\s*$)"
        for match in re.finditer(simple_pattern, raw_output):
            key, _, value = match.groups()
            # Try to convert to appropriate type
            if value.lower() in ('true', 'false'):
                context[key] = value.lower() == 'true'
            elif value.replace('.', '', 1).replace('-', '', 1).isdigit():
                context[key] = float(value) if '.' in value else int(value)
            else:
                context[key] = value

        # Extract dict values (e.g., risk_details={...})
        dict_pattern = r"(\w+)=\{([^}]+)\}"
        for match in re.finditer(dict_pattern, raw_output):
            key, dict_content = match.groups()
            # Parse the dict content
            dict_data = {}
            for item_match in re.finditer(r"'(\w+)':\s*([^,}]+)", dict_content):
                item_key, item_value = item_match.groups()
                item_value = item_value.strip()
                # Convert to appropriate type
                if item_value.replace('.', '', 1).replace('-', '', 1).isdigit():
                    dict_data[item_key] = float(item_value) if '.' in item_value else int(item_value)
                else:
                    dict_data[item_key] = item_value.strip("'\"")
            context[key] = dict_data

        return context


def convert_all_json_to_html(output_dir: str = "output") -> dict[str, list[str]]:
    """
    Convenience function to convert all JSON files to HTML.

    Args:
        output_dir: Root output directory

    Returns:
        Dict with conversion results

    """
    converter = JsonToHtmlConverter()
    return converter.convert_directory(Path(output_dir))


if __name__ == "__main__":
    # Run conversion when executed directly
    results = convert_all_json_to_html()
    print("\n✅ Conversion complete!")
    print(f"   Success: {len(results['success'])} files")
    print(f"   Failed: {len(results['failed'])} files")

    if results["failed"]:
        print("\n❌ Failed files:")
        for failed in results["failed"]:
            print(f"   - {failed}")
