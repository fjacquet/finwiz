"""Crew/enriched HTML report generation and export-path management mixin."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from finwiz.reporting import get_generator_for_crew

if TYPE_CHECKING:
    from finwiz.flow_state import FinwizState


class CrewHtmlMixin:
    """Generates per-crew and per-enriched-file HTML reports and manages export paths."""

    # Provided by ReportingOrchestrator.__init__
    state: FinwizState
    logger: Any

    def generate_html_from_export(
        self,
        export_data: dict[str, Any],
        template_name: str,
    ) -> str:
        """
        Generate HTML using Jinja2 templates.

        Args:
            export_data: Data to render in template
            template_name: Name of Jinja2 template to use

        Returns:
            Generated HTML string

        """
        try:
            from jinja2 import Environment, FileSystemLoader, select_autoescape

            # Setup Jinja2 environment with autoescape to prevent XSS
            template_dir = Path("src/finwiz/reporting/templates")
            env = Environment(loader=FileSystemLoader(str(template_dir)), autoescape=select_autoescape(["html", "htm", "xml"]))

            # Load template
            template = env.get_template(template_name)

            # Render template
            html = template.render(**export_data)

            self.logger.info(f"Generated HTML from template: {template_name}")

            return html

        except Exception as e:
            self.logger.error(f"HTML generation failed: {e}", exc_info=True)
            raise

    def store_crew_export_paths(
        self,
        crew_name: str,
        export_paths: list[str],
    ) -> None:
        """
        Store crew export paths in state.

        Args:
            crew_name: Name of the crew
            export_paths: List of export file paths

        """
        if not hasattr(self.state, "crew_export_paths"):
            self.state.crew_export_paths = {}

        self.state.crew_export_paths[crew_name] = export_paths
        self.logger.debug(f"Stored {len(export_paths)} export paths for {crew_name}")

    def get_crew_export_path(
        self,
        crew_name: str,
        ticker: str,
    ) -> str:
        """
        Calculate crew export path.

        Args:
            crew_name: Name of the crew
            ticker: Ticker symbol

        Returns:
            Export path following pattern: output/{crew_name}/{ticker}_export.json

        """
        session_id = self.state.session_id or "default"
        export_path = f"output/{crew_name}/{ticker}_{session_id}.json"
        return export_path

    def generate_crew_html_report(
        self,
        crew_name: str,
        export_path: str | Path,
    ) -> Path | None:
        """
        Auto-generate HTML report for a crew's export data.

        Uses the CREW_GENERATORS registry to find the appropriate generator
        for each crew type. This is a zero-cost Python operation using Jinja2.

        Args:
            crew_name: Name of the crew (e.g., 'stock_crew', 'etf_crew')
            export_path: Path to the JSON export file

        Returns:
            Path to generated HTML file, or None if generation failed/not supported

        """
        try:
            export_path = Path(export_path)
            if not export_path.exists():
                self.logger.warning(f"Export file not found: {export_path}")
                return None

            # Get generator for this crew type
            generator = get_generator_for_crew(crew_name)
            if generator is None:
                self.logger.debug(f"No HTML generator registered for {crew_name}")
                return None

            # Load export data
            data = json.loads(export_path.read_text())

            # Determine HTML output path
            html_path = export_path.with_suffix(".html")

            # Generate HTML report
            html_content = generator.generate_report(data)
            html_path.write_text(html_content, encoding="utf-8")

            self.logger.info(f"✅ Generated HTML report: {html_path}")
            return html_path

        except Exception as e:
            self.logger.error(f"Failed to generate HTML for {crew_name}: {e}")
            return None

    def generate_all_crew_html_reports(
        self,
        crew_export_paths: dict[str, list[str]],
    ) -> dict[str, list[Path]]:
        """
        Generate HTML reports for all crew exports.

        This is a batch operation that generates individual HTML reports
        for each crew export, using the appropriate template for each crew type.

        Args:
            crew_export_paths: Dictionary mapping crew names to lists of export paths

        Returns:
            Dictionary mapping crew names to lists of generated HTML paths

        """
        generated_reports: dict[str, list[Path]] = {}
        total_generated = 0
        total_failed = 0

        self.logger.info(f"🔄 Generating HTML reports for {len(crew_export_paths)} crews...")

        for crew_name, export_paths in crew_export_paths.items():
            generated_for_crew: list[Path] = []

            for export_path in export_paths:
                html_path = self.generate_crew_html_report(crew_name, export_path)
                if html_path:
                    generated_for_crew.append(html_path)
                    total_generated += 1
                else:
                    total_failed += 1

            if generated_for_crew:
                generated_reports[crew_name] = generated_for_crew

        self.logger.info(f"✅ HTML generation complete: {total_generated} generated, {total_failed} skipped/failed")

        # Store in state for final report access
        if hasattr(self.state, "generated_html_reports"):
            self.state.generated_html_reports = generated_reports

        return generated_reports

    def generate_enriched_html_reports(self) -> dict[str, list[Path]]:
        """
        Generate HTML reports from all enriched JSON files.

        Scans output/enriched/{asset_class}/ directories for *_enriched.json files
        and generates corresponding HTML reports using EnrichedAnalysisReportGenerator.

        Returns:
            Dictionary mapping asset classes to lists of generated HTML paths

        """
        from finwiz.reporting.enriched_analysis_report_generator import EnrichedAnalysisReportGenerator

        generated_reports: dict[str, list[Path]] = {}
        total_generated = 0
        total_failed = 0

        generator = EnrichedAnalysisReportGenerator()
        self.logger.info("🔄 Generating HTML reports from enriched JSON files...")

        # Scan enriched directories for each asset class
        for asset_class in ["stock", "etf", "crypto"]:
            generated_for_asset: list[Path] = []

            # Check both session-specific and direct asset class directories
            session_id = self.state.session_id or "default"
            for base_dir in [f"output/enriched/{session_id}/{asset_class}", f"output/enriched/{asset_class}"]:
                enriched_dir = Path(base_dir)
                if not enriched_dir.exists():
                    continue

                for json_file in enriched_dir.glob("*_enriched.json"):
                    try:
                        # Load enriched data
                        data = json.loads(json_file.read_text())
                        ticker = data.get("ticker", json_file.stem.replace("_enriched", ""))

                        # Generate HTML path
                        html_path = json_file.with_suffix(".html")

                        # Generate HTML report
                        generator.generate_and_save_report(data, str(html_path))

                        generated_for_asset.append(html_path)
                        total_generated += 1
                        self.logger.debug(f"✅ Generated HTML: {html_path}")

                    except Exception as e:
                        total_failed += 1
                        self.logger.warning(f"Failed to generate HTML for {json_file}: {e}")

            if generated_for_asset:
                generated_reports[asset_class] = generated_for_asset

        self.logger.info(f"📊 HTML report generation complete: {total_generated} generated, {total_failed} failed")

        return generated_reports
