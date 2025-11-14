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
                with open(json_path, "r", encoding="utf-8") as f:
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

        logger.info(
            f"Conversion complete: {len(results['success'])} succeeded, "
            f"{len(results['failed'])} failed"
        )
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
    print(f"\n✅ Conversion complete!")
    print(f"   Success: {len(results['success'])} files")
    print(f"   Failed: {len(results['failed'])} files")
    
    if results["failed"]:
        print("\n❌ Failed files:")
        for failed in results["failed"]:
            print(f"   - {failed}")
