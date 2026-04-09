"""
Python-based report consolidation (NO AI).

This module implements pure Python consolidation of crew JSON exports into a
single consolidated report. Following the AI Minimalism principle, this uses
deterministic Python code instead of AI agents for data aggregation.

Key Features:
- Fast: Completes in milliseconds (not seconds)
- Deterministic: Same inputs = same outputs
- Testable: Full unit test coverage with mocks
- Cost-effective: No LLM API calls
- Type-safe: Pydantic validation for all data

Usage:
    from finwiz.reporting.consolidator import ReportConsolidator

    consolidator = ReportConsolidator(
        session_id="abc-123",
        output_dir=Path("output/reports/abc-123")
    )

    consolidated = consolidator.consolidate_reports({
        "stock_crew": ["path/to/AAPL_export.json", "path/to/MSFT_export.json"],
        "etf_crew": ["path/to/SPY_export.json"],
        "crypto_crew": ["path/to/BTC_export.json"]
    })
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import cast

from pydantic import BaseModel

from finwiz.reporting.export_loaders import load_deep_analysis_exports, load_exports
from finwiz.reporting.html_collector import (
    HTMLReportPath,
    add_html_paths_to_analyses,
    collect_html_report_paths,
)
from finwiz.schemas.crew_exports import (
    ConsolidatedReportExport,
    CryptoCrewExport,
    DeepAnalysisCrewExport,
    DiscoveryCrewExport,
    ETFCrewExport,
    RebalancingCrewExport,
    StockCrewExport,
)
from finwiz.schemas.python_analysis import PythonDeepAnalysisResult
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


# Re-export HTMLReportPath for backward compatibility
__all__ = ["HTMLReportPath", "ReportConsolidator"]


class ReportConsolidator:
    """
    Consolidate crew reports using pure Python (NO AI).

    This class reads JSON export files from all crews, validates them against
    Pydantic schemas, and creates a consolidated report object. All operations
    are deterministic and complete in milliseconds.

    Attributes:
        session_id: Flow session identifier for tracking
        output_dir: Directory where consolidated report will be saved

    """

    def __init__(self, session_id: str, output_dir: Path) -> None:
        """
        Initialize report consolidator.

        Args:
            session_id: Flow session identifier
            output_dir: Directory for output files (e.g., output/reports/{session_id})

        """
        self.session_id = session_id
        self.output_dir = Path(output_dir)
        self._html_report_paths: list[HTMLReportPath] = []
        self._validation_errors: list[dict] = []

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initialized ReportConsolidator for session {session_id}")

    def get_html_report_paths(self) -> list[HTMLReportPath]:
        """
        Get collected HTML report paths for final report template.

        Returns:
            List of HTMLReportPath objects collected during consolidation

        """
        return self._html_report_paths

    def get_html_paths_for_template(self) -> tuple[list[dict], int]:
        """
        Get HTML paths formatted for final report template.

        Returns:
            Tuple of (list of path dicts, count of individual reports)
            Each dict contains: ticker, crew, path

        """
        paths_for_template = [{"ticker": hp.ticker, "crew": hp.crew, "path": hp.path, "asset_class": hp.asset_class} for hp in self._html_report_paths]
        return paths_for_template, len(paths_for_template)

    def consolidate_reports(self, crew_export_paths: dict[str, list[str]]) -> ConsolidatedReportExport:
        """
        Consolidate all crew JSON exports into a single report with error recovery.

        This method reads all crew export files, validates them against their
        respective Pydantic schemas, and creates a consolidated export object.
        The consolidation is pure Python (NO AI) and completes in milliseconds.

        Args:
            crew_export_paths: Dict mapping crew names to list of export file paths

        Returns:
            ConsolidatedReportExport: Validated consolidated report object

        """
        start_time = time.time()
        logger.info(f"Starting report consolidation for session {self.session_id}")
        logger.debug(f"Crew export paths: {crew_export_paths}")

        # Reset validation errors
        self._validation_errors = []

        # Initialize consolidated report
        consolidated = ConsolidatedReportExport(
            session_id=self.session_id,
            crew_execution_status={},
            total_execution_time=0.0,
            errors=[],
        )

        # Consolidate each crew type
        self._consolidate_typed_crews(consolidated, crew_export_paths)
        self._consolidate_special_crews(consolidated, crew_export_paths)

        # Include validation errors in consolidated report metadata
        self._add_validation_errors_to_report(consolidated)

        # Collect HTML report paths and add to analyses
        self._collect_and_add_html_paths(consolidated, crew_export_paths)

        # Finalize and save
        consolidated.total_execution_time = time.time() - start_time
        self._save_consolidated_report(consolidated)

        return consolidated

    def _consolidate_typed_crews(
        self,
        consolidated: ConsolidatedReportExport,
        crew_export_paths: dict[str, list[str]],
    ) -> None:
        """Consolidate typed crew exports (stock, ETF, crypto, etc.)."""
        # Crew configurations: (key, attribute, schema_class)
        crew_configs = [
            ("stock_crew", "stock_analyses", StockCrewExport),
            ("etf_crew", "etf_analyses", ETFCrewExport),
            ("crypto_crew", "crypto_analyses", CryptoCrewExport),
        ]

        for crew_key, attr_name, schema_class in crew_configs:
            if crew_key in crew_export_paths:
                logger.info(f"Consolidating {len(crew_export_paths[crew_key])} {crew_key} analyses")
                exports = load_exports(
                    crew_export_paths[crew_key],
                    cast(type[BaseModel], schema_class),
                    crew_key,
                    self.session_id,
                    self._validation_errors,
                )
                setattr(consolidated, attr_name, exports)
                status = "completed" if exports else "failed"
                consolidated.crew_execution_status[crew_key] = status
                logger.info(f"{crew_key} consolidation: {status} ({len(exports)} exports)")

        # Handle deep analysis separately (multiple schemas)
        if "deep_analysis_crew" in crew_export_paths:
            logger.info(f"Consolidating {len(crew_export_paths['deep_analysis_crew'])} deep analyses")
            deep_analysis_results: list[DeepAnalysisCrewExport | PythonDeepAnalysisResult] = cast(
                list[DeepAnalysisCrewExport | PythonDeepAnalysisResult],
                load_deep_analysis_exports(
                    crew_export_paths["deep_analysis_crew"],
                    self._validation_errors,
                ),
            )
            consolidated.deep_analyses = deep_analysis_results
            status = "completed" if consolidated.deep_analyses else "failed"
            consolidated.crew_execution_status["deep_analysis_crew"] = status
            logger.info(f"Deep analysis consolidation: {status} ({len(consolidated.deep_analyses)} exports)")

        # Handle single-result crews (discovery, rebalancing)
        self._consolidate_single_result_crew(consolidated, crew_export_paths, "discovery_crew", "discovery_results", DiscoveryCrewExport)
        self._consolidate_single_result_crew(consolidated, crew_export_paths, "rebalancing_crew", "rebalancing_results", RebalancingCrewExport)

    def _consolidate_single_result_crew(
        self,
        consolidated: ConsolidatedReportExport,
        crew_export_paths: dict[str, list[str]],
        crew_key: str,
        attr_name: str,
        schema_class: type,
    ) -> None:
        """Consolidate a crew that produces a single result."""
        if crew_key in crew_export_paths:
            logger.info(f"Consolidating {crew_key} results")
            exports = load_exports(
                crew_export_paths[crew_key],
                schema_class,
                crew_key,
                self.session_id,
                self._validation_errors,
            )
            setattr(consolidated, attr_name, exports[0] if exports else None)
            status = "completed" if getattr(consolidated, attr_name) else "failed"
            consolidated.crew_execution_status[crew_key] = status
            logger.info(f"{crew_key} consolidation: {status}")

    def _consolidate_special_crews(
        self,
        consolidated: ConsolidatedReportExport,
        crew_export_paths: dict[str, list[str]],
    ) -> None:
        """Consolidate special crew types (portfolio, A+, backtesting)."""
        # Portfolio data
        if "portfolio_crew" in crew_export_paths:
            self._load_generic_json_data(consolidated, crew_export_paths["portfolio_crew"], "portfolio_data", "portfolio_crew")

        # A+ opportunities
        if "aplus_crew" in crew_export_paths:
            self._load_aplus_data(consolidated, crew_export_paths["aplus_crew"])

        # Backtesting results
        if "backtesting_crew" in crew_export_paths:
            self._load_generic_json_data(consolidated, crew_export_paths["backtesting_crew"], "backtesting_data", "backtesting_crew")

    def _load_generic_json_data(
        self,
        consolidated: ConsolidatedReportExport,
        file_paths: list[str],
        attr_name: str,
        crew_name: str,
    ) -> None:
        """Load generic JSON data for a crew."""
        logger.info(f"Consolidating {crew_name}")
        try:
            for file_path in file_paths:
                with open(file_path, encoding="utf-8") as f:
                    data = json.load(f)
                    if not hasattr(consolidated, attr_name):
                        setattr(consolidated, attr_name, data)
                    logger.info(f"Loaded {crew_name} data from {file_path}")
            consolidated.crew_execution_status[crew_name] = "completed"
        except Exception as e:
            logger.error(f"Failed to load {crew_name}: {e}")
            consolidated.crew_execution_status[crew_name] = "failed"

    def _load_aplus_data(
        self,
        consolidated: ConsolidatedReportExport,
        file_paths: list[str],
    ) -> None:
        """Load A+ opportunities data."""
        logger.info("Consolidating A+ opportunities")
        try:
            aplus_data = {}
            for file_path in file_paths:
                with open(file_path, encoding="utf-8") as f:
                    data = json.load(f)
                    file_name = Path(file_path).stem
                    aplus_data[file_name] = data
                    logger.info(f"Loaded A+ data from {file_path}")

            if not hasattr(consolidated, "aplus_opportunities"):
                consolidated.aplus_opportunities = aplus_data
            consolidated.crew_execution_status["aplus_crew"] = "completed"
        except Exception as e:
            logger.error(f"Failed to load A+ opportunities: {e}")
            consolidated.crew_execution_status["aplus_crew"] = "failed"

    def _add_validation_errors_to_report(self, consolidated: ConsolidatedReportExport) -> None:
        """Add validation errors to the consolidated report."""
        if self._validation_errors:
            logger.warning(f"Consolidation completed with {len(self._validation_errors)} validation errors")
            for error in self._validation_errors:
                error_msg = f"{error['crew']}: {error['message']}"
                consolidated.errors.append(error_msg)
                logger.debug(f"Validation error detail: {error}")

    def _collect_and_add_html_paths(
        self,
        consolidated: ConsolidatedReportExport,
        crew_export_paths: dict[str, list[str]],
    ) -> None:
        """Collect HTML report paths and add to analyses."""
        html_paths = collect_html_report_paths(crew_export_paths)
        if html_paths:
            add_html_paths_to_analyses(consolidated, html_paths)
            self._html_report_paths = html_paths

    def _save_consolidated_report(self, consolidated: ConsolidatedReportExport) -> None:
        """Save consolidated report to JSON file."""
        output_path = self.output_dir / "consolidated_report.json"
        logger.info(f"Saving consolidated report to {output_path}")

        try:
            output_path.write_text(consolidated.model_dump_json(indent=2), encoding="utf-8")
            logger.info(f"Consolidation complete in {consolidated.total_execution_time:.3f}s - saved to {output_path}")
        except Exception as e:
            logger.error(f"Failed to save consolidated report: {e}")
            consolidated.errors.append(f"Failed to save consolidated report: {e!s}")
            raise
