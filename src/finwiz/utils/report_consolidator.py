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
    from finwiz.utils.report_consolidator import ReportConsolidator

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

import json
import time
from pathlib import Path

from pydantic import BaseModel, ValidationError

from finwiz.schemas.crew_exports import (
    ConsolidatedReportExport,
    CryptoCrewExport,
    DeepAnalysisCrewExport,
    DiscoveryCrewExport,
    ETFCrewExport,
    RebalancingCrewExport,
    StockCrewExport,
)
from finwiz.schemas.hybrid_analysis import EnrichedAnalysis
from finwiz.schemas.python_analysis import PythonDeepAnalysisResult
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


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

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initialized ReportConsolidator for session {session_id}")

    def consolidate_reports(self, crew_export_paths: dict[str, list[str]]) -> ConsolidatedReportExport:
        """
        Consolidate all crew JSON exports into a single report with error recovery.

        This method reads all crew export files, validates them against their
        respective Pydantic schemas, and creates a consolidated export object.
        The consolidation is pure Python (NO AI) and completes in milliseconds.

        Enhanced error handling:
        - Tracks validation errors in consolidated report metadata
        - Continues consolidation with valid exports even if some fail
        - Includes validation error details for debugging
        - Gracefully handles missing files and invalid data

        Args:
            crew_export_paths: Dict mapping crew names to list of export file paths
                Example:
                {
                    "stock_crew": ["path/to/AAPL_export.json", "path/to/MSFT_export.json"],
                    "etf_crew": ["path/to/SPY_export.json"],
                    "crypto_crew": ["path/to/BTC_export.json"],
                    "deep_analysis_crew": ["path/to/IBM_deep_export.json"],
                    "discovery_crew": ["path/to/discovery_export.json"],
                    "rebalancing_crew": ["path/to/rebalancing_export.json"]
                }

        Returns:
            ConsolidatedReportExport: Validated consolidated report object

        Raises:
            ValueError: If output directory doesn't exist or is not writable

        Requirements: 10.1, 10.2, 10.3, 10.4, 10.5

        """
        start_time = time.time()
        logger.info(f"Starting report consolidation for session {self.session_id}")
        logger.debug(f"Crew export paths: {crew_export_paths}")

        # Initialize validation error tracking
        self._validation_errors: list[dict] = []

        # Initialize consolidated report
        consolidated = ConsolidatedReportExport(session_id=self.session_id, crew_execution_status={}, total_execution_time=0.0, errors=[])

        # Consolidate stock analyses
        if "stock_crew" in crew_export_paths:
            logger.info(f"Consolidating {len(crew_export_paths['stock_crew'])} stock analyses")
            consolidated.stock_analyses = self._load_exports(crew_export_paths["stock_crew"], StockCrewExport, crew_name="stock_crew")
            status = "completed" if consolidated.stock_analyses else "failed"
            consolidated.crew_execution_status["stock_crew"] = status
            logger.info(f"Stock crew consolidation: {status} ({len(consolidated.stock_analyses)} exports)")

        # Consolidate ETF analyses
        if "etf_crew" in crew_export_paths:
            logger.info(f"Consolidating {len(crew_export_paths['etf_crew'])} ETF analyses")
            consolidated.etf_analyses = self._load_exports(crew_export_paths["etf_crew"], ETFCrewExport, crew_name="etf_crew")
            status = "completed" if consolidated.etf_analyses else "failed"
            consolidated.crew_execution_status["etf_crew"] = status
            logger.info(f"ETF crew consolidation: {status} ({len(consolidated.etf_analyses)} exports)")

        # Consolidate crypto analyses
        if "crypto_crew" in crew_export_paths:
            logger.info(f"Consolidating {len(crew_export_paths['crypto_crew'])} crypto analyses")
            consolidated.crypto_analyses = self._load_exports(crew_export_paths["crypto_crew"], CryptoCrewExport, crew_name="crypto_crew")
            status = "completed" if consolidated.crypto_analyses else "failed"
            consolidated.crew_execution_status["crypto_crew"] = status
            logger.info(f"Crypto crew consolidation: {status} ({len(consolidated.crypto_analyses)} exports)")

        # Consolidate deep analyses (supports both Python and CrewAI)
        if "deep_analysis_crew" in crew_export_paths:
            logger.info(f"Consolidating {len(crew_export_paths['deep_analysis_crew'])} deep analyses")
            consolidated.deep_analyses = self._load_deep_analysis_exports(crew_export_paths["deep_analysis_crew"])
            status = "completed" if consolidated.deep_analyses else "failed"
            consolidated.crew_execution_status["deep_analysis_crew"] = status
            logger.info(f"Deep analysis crew consolidation: {status} ({len(consolidated.deep_analyses)} exports)")

        # Consolidate discovery results (single file)
        if "discovery_crew" in crew_export_paths:
            logger.info("Consolidating discovery crew results")
            discovery_exports = self._load_exports(crew_export_paths["discovery_crew"], DiscoveryCrewExport, crew_name="discovery_crew")
            consolidated.discovery_results = discovery_exports[0] if discovery_exports else None
            status = "completed" if consolidated.discovery_results else "failed"
            consolidated.crew_execution_status["discovery_crew"] = status
            logger.info(f"Discovery crew consolidation: {status}")

        # Consolidate rebalancing results (single file)
        if "rebalancing_crew" in crew_export_paths:
            logger.info("Consolidating rebalancing crew results")
            rebalancing_exports = self._load_exports(crew_export_paths["rebalancing_crew"], RebalancingCrewExport, crew_name="rebalancing_crew")
            consolidated.rebalancing_results = rebalancing_exports[0] if rebalancing_exports else None
            status = "completed" if consolidated.rebalancing_results else "failed"
            consolidated.crew_execution_status["rebalancing_crew"] = status
            logger.info(f"Rebalancing crew consolidation: {status}")

        # CRITICAL FIX: Handle additional data files
        # Handle portfolio data
        if "portfolio_crew" in crew_export_paths:
            logger.info("Consolidating portfolio review data")
            try:
                for file_path in crew_export_paths["portfolio_crew"]:
                    with open(file_path, encoding="utf-8") as f:
                        portfolio_data = json.load(f)
                        # Store portfolio data in consolidated report
                        if not hasattr(consolidated, "portfolio_data"):
                            consolidated.portfolio_data = portfolio_data
                        logger.info(f"✅ Loaded portfolio data from {file_path}")
                consolidated.crew_execution_status["portfolio_crew"] = "completed"
            except Exception as e:
                logger.error(f"Failed to load portfolio data: {e}")
                consolidated.crew_execution_status["portfolio_crew"] = "failed"

        # Handle A+ opportunities
        if "aplus_crew" in crew_export_paths:
            logger.info("Consolidating A+ opportunities")
            try:
                aplus_data = {}
                for file_path in crew_export_paths["aplus_crew"]:
                    with open(file_path, encoding="utf-8") as f:
                        data = json.load(f)
                        file_name = Path(file_path).stem
                        aplus_data[file_name] = data
                        logger.info(f"✅ Loaded A+ data from {file_path}")

                # Store A+ data in consolidated report
                if not hasattr(consolidated, "aplus_opportunities"):
                    consolidated.aplus_opportunities = aplus_data
                consolidated.crew_execution_status["aplus_crew"] = "completed"
            except Exception as e:
                logger.error(f"Failed to load A+ opportunities: {e}")
                consolidated.crew_execution_status["aplus_crew"] = "failed"

        # Handle backtesting results
        if "backtesting_crew" in crew_export_paths:
            logger.info("Consolidating backtesting results")
            try:
                for file_path in crew_export_paths["backtesting_crew"]:
                    with open(file_path, encoding="utf-8") as f:
                        backtesting_data = json.load(f)
                        # Store backtesting data in consolidated report
                        if not hasattr(consolidated, "backtesting_data"):
                            consolidated.backtesting_data = backtesting_data
                        logger.info(f"✅ Loaded backtesting data from {file_path}")
                consolidated.crew_execution_status["backtesting_crew"] = "completed"
            except Exception as e:
                logger.error(f"Failed to load backtesting data: {e}")
                consolidated.crew_execution_status["backtesting_crew"] = "failed"

        # Include validation errors in consolidated report metadata
        if self._validation_errors:
            logger.warning(f"Consolidation completed with {len(self._validation_errors)} validation errors")
            for error in self._validation_errors:
                error_msg = f"{error['crew']}: {error['message']}"
                consolidated.errors.append(error_msg)
                logger.debug(f"Validation error detail: {error}")

        # Calculate total execution time
        consolidated.total_execution_time = time.time() - start_time

        # Save consolidated export to JSON
        output_path = self.output_dir / "consolidated_report.json"
        logger.info(f"Saving consolidated report to {output_path}")

        try:
            output_path.write_text(consolidated.model_dump_json(indent=2), encoding="utf-8")
            logger.info(f"Consolidation complete in {consolidated.total_execution_time:.3f}s - saved to {output_path}")
        except Exception as e:
            logger.error(f"Failed to save consolidated report: {e}")
            consolidated.errors.append(f"Failed to save consolidated report: {str(e)}")
            raise

        return consolidated

    def _load_exports(self, file_paths: list[str], schema_class: type[BaseModel], crew_name: str = "") -> list[BaseModel]:
        """
        Load and validate JSON export files with enhanced error recovery.

        This helper method reads JSON files from disk, validates them against
        the specified Pydantic schema, and returns a list of validated objects.
        It handles missing files and validation errors gracefully with detailed
        logging and error tracking in consolidated report metadata.

        Args:
            file_paths: List of file paths to load
            schema_class: Pydantic schema class for validation
            crew_name: Name of crew for error tracking (optional)

        Returns:
            List of validated export objects (may be empty if all files fail)

        Notes:
            - Missing files are logged as warnings and skipped
            - Validation errors are logged with field-level details and tracked
            - Other errors (I/O, JSON parsing) are logged and skipped
            - Continues consolidation with valid exports even if some fail
            - Validation errors are included in consolidated report metadata
            - Deterministic: same inputs always produce same outputs
            - Fast: completes in milliseconds for typical file counts

        Requirements: 10.1, 10.2, 10.3, 10.4, 10.5

        """
        exports: list[BaseModel] = []
        schema_name = schema_class.__name__

        logger.debug(f"Loading {len(file_paths)} files for schema {schema_name}")

        for path_str in file_paths:
            path = Path(path_str)

            # Check if file exists
            if not path.exists():
                error_msg = f"Export file not found: {path}"
                logger.warning(error_msg)
                # Track missing file error
                if hasattr(self, "_validation_errors"):
                    self._validation_errors.append({"crew": crew_name, "file": str(path), "error_type": "missing_file", "message": error_msg})
                continue

            try:
                # Read and parse JSON
                logger.debug(f"Reading {path}")
                data = json.loads(path.read_text(encoding="utf-8"))

                # Filter data to only include fields defined in the schema
                # This handles cases where crew exports include extra fields (like raw CrewAI output)
                schema_fields = schema_class.model_fields.keys()
                filtered_data = {k: v for k, v in data.items() if k in schema_fields}

                # Add default values for missing required fields if possible
                if schema_name == "DiscoveryCrewExport":
                    # Handle discovery crew exports that may be missing required fields
                    if "session_id" not in filtered_data:
                        filtered_data["session_id"] = self.session_id
                    if "market_context" not in filtered_data:
                        filtered_data["market_context"] = "Market context not available from discovery crew export"
                    if "report_html_path" not in filtered_data:
                        filtered_data["report_html_path"] = str(path.parent / "discovery_latest.html")
                    if "report_json_path" not in filtered_data:
                        filtered_data["report_json_path"] = str(path)

                # Validate against Pydantic schema
                export = schema_class.model_validate(filtered_data)
                exports.append(export)
                logger.debug(f"Successfully validated {path} as {schema_name}")

            except ValidationError as e:
                # Log detailed validation errors with field paths
                logger.error(f"Validation failed for {path} against {schema_name}:")
                validation_details = []
                for error in e.errors():
                    field_path = " -> ".join(str(loc) for loc in error["loc"])
                    error_detail = f"Field '{field_path}': {error['msg']}"
                    logger.error(f"  {error_detail}")
                    validation_details.append(error_detail)

                # Track validation error in metadata
                if hasattr(self, "_validation_errors"):
                    self._validation_errors.append(
                        {
                            "crew": crew_name,
                            "file": str(path),
                            "error_type": "validation_error",
                            "schema": schema_name,
                            "details": validation_details,
                            "message": f"Validation failed: {len(validation_details)} field errors",
                        }
                    )

                # Skip invalid export with warning (graceful degradation)
                logger.warning(f"Skipping invalid export {path} - continuing with valid exports")

            except json.JSONDecodeError as e:
                # Log JSON parsing errors
                error_msg = f"Invalid JSON in {path}: {e}"
                logger.error(error_msg)
                # Track JSON parsing error
                if hasattr(self, "_validation_errors"):
                    self._validation_errors.append({"crew": crew_name, "file": str(path), "error_type": "json_parse_error", "message": error_msg})

            except Exception as e:
                # Log any other unexpected errors
                error_msg = f"Failed to load {path}: {e}"
                logger.error(error_msg, exc_info=True)
                # Track unexpected error
                if hasattr(self, "_validation_errors"):
                    self._validation_errors.append({"crew": crew_name, "file": str(path), "error_type": "unexpected_error", "message": error_msg})

        logger.info(f"Loaded {len(exports)}/{len(file_paths)} valid {schema_name} exports")

        # Log warning if no valid exports loaded
        if len(file_paths) > 0 and len(exports) == 0:
            logger.warning(f"No valid {schema_name} exports loaded from {len(file_paths)} files")

        return exports

    def _load_deep_analysis_exports(self, file_paths: list[str]) -> list[DeepAnalysisCrewExport | PythonDeepAnalysisResult | EnrichedAnalysis]:
        """
        Load deep analysis exports with automatic schema detection.

        Supports:
        - CrewAI deep analysis exports (legacy)
        - Python analyzer results (legacy)
        - EnrichedAnalysis (new hybrid analysis schema)

        Automatically detects which schema to use based on the crew_name field
        or presence of hybrid analysis fields.

        Args:
            file_paths: List of file paths to load

        Returns:
            List of validated export objects (mixed CrewAI, Python, and hybrid)

        Requirements: 9.1 (Support new schema formats)

        """
        exports: list[DeepAnalysisCrewExport | PythonDeepAnalysisResult | EnrichedAnalysis] = []

        logger.debug(f"Loading {len(file_paths)} deep analysis files with auto-detection")

        for path_str in file_paths:
            path = Path(path_str)

            if not path.exists():
                error_msg = f"Export file not found: {path}"
                logger.warning(error_msg)
                if hasattr(self, "_validation_errors"):
                    self._validation_errors.append({"crew": "deep_analysis_crew", "file": str(path), "error_type": "missing_file", "message": error_msg})
                continue

            try:
                # Read and parse JSON
                data = json.loads(path.read_text(encoding="utf-8"))

                # Detect schema based on structure
                crew_name = data.get("crew_name", "")

                # Check for EnrichedAnalysis (new hybrid schema)
                if "quantitative" in data and "qualitative" in data:
                    # New hybrid analysis format
                    export = EnrichedAnalysis.model_validate(data)
                    logger.debug(f"✅ Validated {path} as EnrichedAnalysis (hybrid)")
                elif crew_name == "PythonDeepAnalyzer":
                    # Python analyzer output (legacy)
                    export = PythonDeepAnalysisResult.model_validate(data)
                    logger.debug(f"✅ Validated {path} as PythonDeepAnalysisResult (legacy)")
                else:
                    # CrewAI deep analysis output (legacy)
                    export = DeepAnalysisCrewExport.model_validate(data)
                    logger.debug(f"✅ Validated {path} as DeepAnalysisCrewExport (legacy)")

                exports.append(export)

            except ValidationError as e:
                # Log detailed validation errors
                if "quantitative" in data and "qualitative" in data:
                    schema_name = "EnrichedAnalysis"
                elif crew_name == "PythonDeepAnalyzer":
                    schema_name = "PythonDeepAnalysisResult"
                else:
                    schema_name = "DeepAnalysisCrewExport"
                logger.error(f"Validation failed for {path} against {schema_name}:")
                validation_details = []
                for error in e.errors():
                    field_path = " -> ".join(str(loc) for loc in error["loc"])
                    error_detail = f"Field '{field_path}': {error['msg']}"
                    logger.error(f"  {error_detail}")
                    validation_details.append(error_detail)

                if hasattr(self, "_validation_errors"):
                    self._validation_errors.append(
                        {
                            "crew": "deep_analysis_crew",
                            "file": str(path),
                            "error_type": "validation_error",
                            "schema": schema_name,
                            "details": validation_details,
                            "message": f"Validation failed: {len(validation_details)} field errors",
                        }
                    )

                logger.warning(f"Skipping invalid export {path}")

            except json.JSONDecodeError as e:
                error_msg = f"Invalid JSON in {path}: {e}"
                logger.error(error_msg)
                if hasattr(self, "_validation_errors"):
                    self._validation_errors.append({"crew": "deep_analysis_crew", "file": str(path), "error_type": "json_parse_error", "message": error_msg})

            except Exception as e:
                error_msg = f"Failed to load {path}: {e}"
                logger.error(error_msg, exc_info=True)
                if hasattr(self, "_validation_errors"):
                    self._validation_errors.append({"crew": "deep_analysis_crew", "file": str(path), "error_type": "unexpected_error", "message": error_msg})

        logger.info(f"Loaded {len(exports)}/{len(file_paths)} valid deep analysis exports")

        if len(file_paths) > 0 and len(exports) == 0:
            logger.warning(f"No valid deep analysis exports loaded from {len(file_paths)} files")

        return exports
