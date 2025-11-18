"""
Reporting Orchestrator for FinWiz Flow.

This module provides report consolidation and HTML generation including:
- Report consolidation from crew exports
- Final HTML report generation
- HTML generation from export data using Jinja2
- Crew export path management
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from finwiz.flow_state import FinwizState
from finwiz.schemas.portfolio_review import PortfolioReview
from finwiz.tools.logger import get_logger


class ReportingOrchestrator:
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

            # Generate Python-based report
            report_path = self._generate_python_report(portfolio_review, deep_analysis_results)

            # Update state with success
            self.state.report_generation_success = True
            self.state.report_path = report_path
            self.state.report_generation_method = "python_templates"

            self.logger.info(f"✅ Python report generation completed: {report_path}")

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
    ) -> dict[str, Any]:
        """
        Consolidate crew reports into single structure.

        Args:
            crew_export_paths: Dictionary mapping crew names to lists of export file paths

        Returns:
            Dictionary with consolidated report data

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

            return {
                "success": True,
                "consolidated_data": consolidated,
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
            from jinja2 import Environment, FileSystemLoader

            # Setup Jinja2 environment
            template_dir = Path("src/finwiz/reporting/templates")
            env = Environment(loader=FileSystemLoader(str(template_dir)))

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

    # ===== PRIVATE HELPER METHODS =====

    def _get_portfolio_review_from_state(self) -> dict[str, Any] | None:
        """Get portfolio review data from state."""
        if hasattr(self.state, "portfolio_review") and self.state.portfolio_review:
            return self.state.portfolio_review
        return None

    def _convert_to_portfolio_review(
        self,
        portfolio_review_data: dict[str, Any] | PortfolioReview,
    ) -> PortfolioReview:
        """Convert portfolio review data to PortfolioReview object."""
        if isinstance(portfolio_review_data, PortfolioReview):
            return portfolio_review_data

        # Handle nested structure
        if isinstance(portfolio_review_data, dict):
            if "portfolio_review" in portfolio_review_data:
                return PortfolioReview.model_validate(portfolio_review_data["portfolio_review"])
            return PortfolioReview.model_validate(portfolio_review_data)

        raise ValueError(f"Invalid portfolio review data type: {type(portfolio_review_data)}")

    def _read_deep_analysis_from_files(self) -> dict[str, Any] | None:
        """Read deep analysis results from JSON files on disk."""
        try:
            self.logger.info("Reading deep analysis results from JSON files...")

            raw_deep_analysis = {}
            session_id = self.state.session_id or "default"

            # Read JSON files from disk for each asset class
            for asset_class in ["stock", "etf", "crypto"]:
                asset_dir = Path(f"output/{asset_class}")
                if asset_dir.exists():
                    for json_file in asset_dir.glob(f"*_{session_id}.json"):
                        try:
                            data = self._read_json_file(str(json_file))
                            ticker = data.get("ticker")
                            if ticker:
                                raw_deep_analysis[ticker] = data
                                self.logger.debug(f"Loaded {ticker} from {json_file}: Score={data.get('composite_score', 0):.3f}, Grade={data.get('grade', 'N/A')}")
                        except Exception as e:
                            self.logger.warning(f"Failed to load {json_file}: {e}")

            if not raw_deep_analysis:
                self.logger.warning("No deep analysis results found in JSON files")
                return None

            self.logger.info(f"Loaded {len(raw_deep_analysis)} deep analysis results")

            # Transform to expected format
            return self._transform_deep_analysis_results(raw_deep_analysis)

        except Exception as e:
            self.logger.error(f"Failed to read deep analysis from files: {e}")
            return None

    def _transform_deep_analysis_results(
        self,
        raw_deep_analysis: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        """Transform raw deep analysis results to expected format."""
        successful_count = len(raw_deep_analysis)
        total_holdings = self.state.total_holdings or successful_count
        failed_count = total_holdings - successful_count

        # Calculate average composite score
        scores = [r.get("composite_score", 0.0) for r in raw_deep_analysis.values()]
        avg_score = sum(scores) / len(scores) if scores else 0.0

        return {
            "successful_analyses": successful_count,
            "failed_analyses": failed_count,
            "total_holdings": total_holdings,
            "performance_metrics": {
                "average_composite_score": avg_score,
                "grade_distribution": self._calculate_grade_distribution(raw_deep_analysis),
                "analysis_method": "python_scorer",
            },
            "results_by_ticker": {
                ticker: {
                    "ticker": result.get("ticker"),
                    "grade": result.get("grade"),
                    "composite_score": result.get("composite_score", 0.0),
                    "recommendation": result.get("recommendation", "HOLD"),
                    "asset_class": result.get("asset_class"),
                }
                for ticker, result in raw_deep_analysis.items()
            },
        }

    def _calculate_grade_distribution(
        self,
        deep_analysis_results: dict[str, dict[str, Any]],
    ) -> dict[str, int]:
        """Calculate grade distribution from deep analysis results."""
        grade_counts: dict[str, int] = {
            "A+": 0,
            "A": 0,
            "B": 0,
            "C": 0,
            "D": 0,
            "F": 0,
        }

        for result in deep_analysis_results.values():
            grade = result.get("grade", "F")
            if grade in grade_counts:
                grade_counts[grade] += 1

        return grade_counts

    def _merge_deep_analysis_into_portfolio(
        self,
        portfolio_review: PortfolioReview,
        deep_analysis_results: dict[str, Any],
    ) -> None:
        """Merge deep analysis results into portfolio review holdings."""
        if "results_by_ticker" not in deep_analysis_results:
            return

        self.logger.info("Merging deep analysis results into portfolio review...")
        merged_count = 0

        for holding in portfolio_review.holdings:
            ticker = holding.ticker
            if ticker in deep_analysis_results["results_by_ticker"]:
                deep_result = deep_analysis_results["results_by_ticker"][ticker]

                # Update holding with deep analysis results
                holding.composite_score = deep_result["composite_score"]
                holding.grade = deep_result["grade"]
                holding.decision = deep_result["recommendation"]
                holding.recommended_action = f"{deep_result['recommendation']} - Analyse approfondie Python"

                # Update rationale with real analysis
                holding.rationale_bullets = [
                    f"📊 Score composite: {deep_result['composite_score']:.3f}",
                    f"🎯 Note: {deep_result['grade']}",
                    f"💡 Recommandation: {deep_result['recommendation']}",
                    "✅ Analyse approfondie Python (déterministe)",
                    f"📈 Classe d'actif: {deep_result['asset_class']}",
                ]

                merged_count += 1

        self.logger.info(f"Merged {merged_count} deep analysis results into portfolio review")

    def _generate_python_report(
        self,
        portfolio_review: PortfolioReview,
        deep_analysis_results: dict[str, Any] | None,
    ) -> str:
        """Generate Python-based HTML report."""
        from finwiz.reporting.python_report_generator import generate_python_report

        session_id = self.state.session_id or "default"
        report_path = generate_python_report(
            portfolio_review=portfolio_review,
            deep_analysis_results=deep_analysis_results,
            session_id=session_id,
        )

        return report_path

    def _read_json_file(self, file_path: str) -> dict[str, Any]:
        """Read and parse JSON file."""
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)

    def _extract_portfolio_review(
        self,
        consolidated_data: dict[str, Any],
    ) -> PortfolioReview:
        """Extract portfolio review from consolidated data."""
        # Implementation depends on consolidated data structure
        # For now, get from state
        portfolio_review_data = self._get_portfolio_review_from_state()
        if not portfolio_review_data:
            raise ValueError("No portfolio review in consolidated data")

        return self._convert_to_portfolio_review(portfolio_review_data)

    def _extract_deep_analysis(
        self,
        consolidated_data: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Extract deep analysis results from consolidated data."""
        # Check if deep analysis is in consolidated data
        if "deep_analysis" in consolidated_data:
            return consolidated_data["deep_analysis"]

        # Otherwise read from files
        return self._read_deep_analysis_from_files()
