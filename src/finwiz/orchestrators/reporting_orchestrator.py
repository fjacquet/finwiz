"""
Reporting Orchestrator for FinWiz Flow.

This module provides report consolidation and HTML generation including:
- Report consolidation from crew exports
- Final HTML report generation
- HTML generation from export data using Jinja2
- Crew export path management

The implementation is split across cohesive mixins under
``finwiz.orchestrators.reporting`` (data loading/merge, enrichment, crew HTML);
``ReportingOrchestrator`` composes them so behavior is unchanged.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from finwiz.flow_state import FinwizState
from finwiz.orchestrators.reporting.crew_html import CrewHtmlMixin
from finwiz.orchestrators.reporting.data_loading import ReportDataLoadingMixin
from finwiz.orchestrators.reporting.enrichment import ReportEnrichmentMixin
from finwiz.tools.logger import get_logger


class ReportingOrchestrator(ReportDataLoadingMixin, ReportEnrichmentMixin, CrewHtmlMixin):
    """Generates consolidated reports and final HTML output."""

    def __init__(self, state: FinwizState, **dependencies: Any) -> None:
        """
        Initialize the ReportingOrchestrator.

        Args:
            state: FinwizState instance for accessing workflow state
            **dependencies: Additional dependencies including:
                - integration_manager: CrewDataIntegrationManager for data access
                - data_accessor: For consolidated data retrieval

        """
        self.state = state
        self.logger = get_logger(self.__class__.__name__)
        self.integration_manager = dependencies.get("integration_manager")
        self.data_accessor = dependencies.get("data_accessor")

    def report(self) -> dict[str, Any]:
        """
        Main report generation entry point.

        Generates a consolidated HTML report using Python templates (no AI).
        This method:
        1. Validates report inputs
        2. Reads deep analysis results from JSON files
        3. Merges deep analysis into portfolio review
        4. Generates HTML report using Python templates

        Returns:
            Dictionary with report generation results including:
                - report_generation_complete: bool
                - success: bool
                - report_path: str (if successful)
                - error: str (if failed)

        """
        try:
            self.logger.info("Starting Python-based report generation")

            # Get portfolio review from state
            portfolio_review_data = self._get_portfolio_review_from_state()
            if not portfolio_review_data:
                raise ValueError("No portfolio review data available for report generation")

            # Convert to PortfolioReview object
            portfolio_review = self._convert_to_portfolio_review(portfolio_review_data)

            # Read deep analysis results from JSON files
            deep_analysis_results = self._read_deep_analysis_from_files()

            # Merge deep analysis into portfolio review
            if deep_analysis_results:
                self._merge_deep_analysis_into_portfolio(portfolio_review, deep_analysis_results)

                # Save the merged portfolio review back to disk
                self._save_merged_portfolio_review(portfolio_review)

            # Generate Python-based report
            report_path = self._generate_python_report(portfolio_review, deep_analysis_results)

            # Generate individual HTML reports from enriched JSON files
            enriched_html_paths = self.generate_enriched_html_reports()
            enriched_count = sum(len(paths) for paths in enriched_html_paths.values())
            if enriched_count > 0:
                self.logger.info(f"✅ Generated {enriched_count} individual HTML reports from enriched data")

            # Update state with success
            self.state.report_generation_success = True
            self.state.report_path = report_path
            self.state.report_generation_method = "python_templates"

            self.logger.info(f"✅ Python report generation completed: {report_path}")

            # Print to console for visibility
            print(f"\n{'=' * 80}")
            print(f"✅ REPORT GENERATED: {report_path}")
            print(f"{'=' * 80}\n")

            return {
                "report_generation_complete": True,
                "success": True,
                "report_path": report_path,
            }

        except Exception as e:
            self.logger.error(f"Report generation failed: {e}", exc_info=True)
            self.state.report_generation_success = False
            self.state.report_generation_error = str(e)

            return {
                "report_generation_complete": False,
                "success": False,
                "error": str(e),
            }

    def consolidate_reports(
        self,
        crew_export_paths: dict[str, list[str]],
        generate_html: bool = True,
    ) -> dict[str, Any]:
        """
        Consolidate crew reports into single structure.

        Args:
            crew_export_paths: Dictionary mapping crew names to lists of export file paths
            generate_html: If True, auto-generate HTML reports for all exports (default: True)

        Returns:
            Dictionary with consolidated report data and generated HTML paths

        """
        try:
            self.logger.info(f"Consolidating reports from {len(crew_export_paths)} crews")

            consolidated = {
                "crews": {},
                "timestamp": datetime.now().isoformat(),
                "total_reports": 0,
            }

            for crew_name, export_paths in crew_export_paths.items():
                crew_reports = []
                for export_path in export_paths:
                    try:
                        report_data = self._read_json_file(export_path)
                        crew_reports.append(report_data)
                    except Exception as e:
                        self.logger.warning(f"Failed to read {export_path}: {e}")

                consolidated["crews"][crew_name] = crew_reports
                consolidated["total_reports"] += len(crew_reports)

            self.logger.info(f"Consolidated {consolidated['total_reports']} reports")

            # Auto-generate HTML reports (zero cost, Python-based)
            html_reports: dict[str, list[Path]] = {}
            if generate_html:
                html_reports = self.generate_all_crew_html_reports(crew_export_paths)
                consolidated["html_reports_generated"] = sum(len(v) for v in html_reports.values())

            return {
                "success": True,
                "consolidated_data": consolidated,
                "html_report_paths": {k: [str(p) for p in v] for k, v in html_reports.items()},
            }

        except Exception as e:
            self.logger.error(f"Report consolidation failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
            }

    def generate_final_report(
        self,
        consolidated_data: dict[str, Any],
    ) -> str:
        """
        Generate final HTML report from consolidated data.

        Args:
            consolidated_data: Consolidated report data from all crews

        Returns:
            Path to generated HTML report

        """
        try:
            self.logger.info("Generating final HTML report")

            # Extract portfolio review from consolidated data
            portfolio_review = self._extract_portfolio_review(consolidated_data)

            # Extract deep analysis results
            deep_analysis = self._extract_deep_analysis(consolidated_data)

            # Generate HTML report
            report_path = self._generate_python_report(portfolio_review, deep_analysis)

            self.logger.info(f"Final report generated: {report_path}")

            return report_path

        except Exception as e:
            self.logger.error(f"Final report generation failed: {e}", exc_info=True)
            raise
