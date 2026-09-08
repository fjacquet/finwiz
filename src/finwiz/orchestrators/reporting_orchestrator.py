"""
Reporting Orchestrator for FinWiz Flow.

This module provides HTML report generation:
- Per-holding reports rendered from the enriched analysis files
- Final HTML report generation

The implementation is split across cohesive mixins under
``finwiz.orchestrators.reporting`` (data loading/merge, enrichment, enriched-file HTML);
``ReportingOrchestrator`` composes them so behavior is unchanged.
"""

from typing import Any

from finwiz.flow_state import FinwizState
from finwiz.orchestrators.reporting.data_loading import ReportDataLoadingMixin
from finwiz.orchestrators.reporting.enriched_html import EnrichedHtmlMixin
from finwiz.orchestrators.reporting.enrichment import ReportEnrichmentMixin
from finwiz.tools.logger import get_logger


class ReportingOrchestrator(ReportDataLoadingMixin, ReportEnrichmentMixin, EnrichedHtmlMixin):
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
