"""
File and directory management utilities for FinWiz report generation.

This module provides utilities for creating output directories, generating
consistent file paths, and managing report manifests. All operations follow
the AI Minimalism principle - pure Python, no AI agents.

Key Features:
- Automatic directory structure creation
- Consistent file path generation with timestamps
- Report manifest tracking
- Permission error handling
- Type-safe with Pydantic models

Usage:
    from finwiz.utils.file_management import DirectoryManager, FilePathHelper

    # Create directory structure
    dir_manager = DirectoryManager(session_id="abc-123")
    dir_manager.create_output_directories()

    # Generate file paths
    path_helper = FilePathHelper(session_id="abc-123")
    export_path = path_helper.get_export_path("stock_crew", "AAPL")
    html_path = path_helper.get_html_path("stock_crew", "AAPL")
"""

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class ReportManifest(BaseModel):
    """
    Manifest tracking all generated report files with metadata.

    This model tracks all files generated during a report session, including
    crew exports, HTML reports, and consolidated reports. It provides a
    complete audit trail of generated files.

    Attributes:
        session_id: Unique session identifier
        creation_date: When the manifest was created
        last_updated: When the manifest was last updated
        files: List of file entries with metadata

    Requirements: 9.5, 9.6, 9.7

    """

    session_id: str = Field(..., description="Unique session identifier")
    creation_date: datetime = Field(default_factory=datetime.now, description="Manifest creation timestamp")
    last_updated: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    files: list[dict[str, str]] = Field(default_factory=list, description="List of generated files with metadata")

    model_config = {"extra": "forbid", "ser_json_timedelta": "iso8601"}

    def add_file(
        self,
        crew_name: str,
        ticker: str,
        asset_class: str,
        status: str,
        export_path: str | None = None,
        html_path: str | None = None,
    ) -> None:
        """
        Add a file entry to the manifest.

        Args:
            crew_name: Name of the crew that generated the file
            ticker: Asset ticker symbol
            asset_class: Asset class (stock, etf, crypto)
            status: Generation status (completed, failed)
            export_path: Path to JSON export file (optional)
            html_path: Path to HTML report file (optional)

        """
        entry = {
            "crew_name": crew_name,
            "ticker": ticker,
            "asset_class": asset_class,
            "status": status,
            "timestamp": datetime.now().isoformat(),
        }

        if export_path:
            entry["export_path"] = export_path
        if html_path:
            entry["html_path"] = html_path

        self.files.append(entry)
        self.last_updated = datetime.now()

        logger.debug(f"Added file entry to manifest: {crew_name}/{ticker}")

    def get_files_by_crew(self, crew_name: str) -> list[dict[str, str]]:
        """
        Get all file entries for a specific crew.

        Args:
            crew_name: Name of the crew

        Returns:
            List of file entries for the specified crew

        """
        return [f for f in self.files if f.get("crew_name") == crew_name]

    def get_files_by_status(self, status: str) -> list[dict[str, str]]:
        """
        Get all file entries with a specific status.

        Args:
            status: Status to filter by (completed, failed)

        Returns:
            List of file entries with the specified status

        """
        return [f for f in self.files if f.get("status") == status]


class DirectoryManager:
    """
    Manage output directory structure for report generation.

    This class handles creation of the output directory structure for a
    report session, including subdirectories for each crew type. It ensures
    directories exist before crew execution and handles permission errors
    gracefully.

    Attributes:
        session_id: Unique session identifier
        base_output_dir: Base output directory (default: output/reports)
        session_dir: Session-specific directory

    Requirements:
        9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7

    """

    # Crew types that need subdirectories
    CREW_TYPES = [
        "stock_crew",
        "etf_crew",
        "crypto_crew",
        "deep_analysis_crew",
        "discovery_crew",
        "rebalancing_crew",
    ]

    def __init__(self, session_id: str, base_output_dir: str = "output/reports") -> None:
        """
        Initialize directory manager.

        Args:
            session_id: Unique session identifier
            base_output_dir: Base output directory (default: output/reports)

        """
        self.session_id = session_id
        self.base_output_dir = Path(base_output_dir)
        self.session_dir = self.base_output_dir / session_id

        logger.info(f"Initialized DirectoryManager for session {session_id}")
        logger.debug(f"Session directory: {self.session_dir}")

    def create_output_directories(self) -> dict[str, Path]:
        """
        Create output directory structure for the session.

        Creates the following structure:
        output/reports/{session_id}/
        ├── stock_crew/
        ├── etf_crew/
        ├── crypto_crew/
        ├── deep_analysis_crew/
        ├── discovery_crew/
        └── rebalancing_crew/

        Returns:
            Dict mapping crew names to their directory paths

        Raises:
            PermissionError: If directories cannot be created due to permissions
            OSError: If directory creation fails for other reasons

        Requirements:
            9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7

        """
        logger.info(f"Creating output directory structure for session {self.session_id}")

        directories = {}

        try:
            # Create session directory
            self.session_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created session directory: {self.session_dir}")

            # Create subdirectories for each crew type
            for crew_type in self.CREW_TYPES:
                crew_dir = self.session_dir / crew_type
                crew_dir.mkdir(parents=True, exist_ok=True)
                directories[crew_type] = crew_dir
                logger.debug(f"Created crew directory: {crew_dir}")

            logger.info(f"Successfully created {len(directories)} crew directories")
            return directories

        except PermissionError as e:
            error_msg = f"Permission denied creating directories in {self.session_dir}: {e}"
            logger.error(error_msg)
            raise PermissionError(error_msg) from e

        except OSError as e:
            error_msg = f"Failed to create directories in {self.session_dir}: {e}"
            logger.error(error_msg)
            raise OSError(error_msg) from e

    def ensure_directory_exists(self, directory: Path) -> None:
        """
        Ensure a specific directory exists, creating it if necessary.

        Args:
            directory: Path to directory

        Raises:
            PermissionError: If directory cannot be created due to permissions
            OSError: If directory creation fails for other reasons

        """
        try:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {directory}")
        except PermissionError as e:
            error_msg = f"Permission denied creating directory {directory}: {e}"
            logger.error(error_msg)
            raise PermissionError(error_msg) from e
        except OSError as e:
            error_msg = f"Failed to create directory {directory}: {e}"
            logger.error(error_msg)
            raise OSError(error_msg) from e

    def get_crew_directory(self, crew_name: str) -> Path:
        """
        Get the directory path for a specific crew.

        Args:
            crew_name: Name of the crew

        Returns:
            Path to crew directory

        """
        return self.session_dir / crew_name

    def get_session_directory(self) -> Path:
        """
        Get the session directory path.

        Returns:
            Path to session directory

        """
        return self.session_dir


class FilePathHelper:
    """
    Generate consistent file paths for report files.

    This class provides helper methods for generating consistent file paths
    for JSON exports and HTML reports. It follows standardized naming patterns
    with timestamps for versioning.

    Patterns:
    - JSON exports: {crew_name}/{ticker}_{timestamp}.json
    - HTML reports: {crew_name}/{ticker}_{timestamp}.html

    Attributes:
        session_id: Unique session identifier
        base_output_dir: Base output directory
        session_dir: Session-specific directory

    Requirements:
        9.2, 9.3, 9.4

    """

    def __init__(self, session_id: str, base_output_dir: str = "output/reports") -> None:
        """
        Initialize file path helper.

        Args:
            session_id: Unique session identifier
            base_output_dir: Base output directory (default: output/reports)

        """
        self.session_id = session_id
        self.base_output_dir = Path(base_output_dir)
        self.session_dir = self.base_output_dir / session_id

        logger.debug(f"Initialized FilePathHelper for session {session_id}")

    def get_export_path(self, crew_name: str, ticker: str, timestamp: datetime | None = None) -> Path:
        """
        Generate path for JSON export file.

        Pattern: {crew_name}/{ticker}_{timestamp}.json

        Args:
            crew_name: Name of the crew
            ticker: Asset ticker symbol
            timestamp: Optional timestamp (defaults to now)

        Returns:
            Path to JSON export file

        Requirements:
            9.2, 9.3, 9.4

        """
        if timestamp is None:
            timestamp = datetime.now()

        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        filename = f"{ticker}_{timestamp_str}.json"
        path = self.session_dir / crew_name / filename

        logger.debug(f"Generated export path: {path}")
        return path

    def get_html_path(self, crew_name: str, ticker: str, timestamp: datetime | None = None) -> Path:
        """
        Generate path for HTML report file.

        Pattern: {crew_name}/{ticker}_{timestamp}.html

        Args:
            crew_name: Name of the crew
            ticker: Asset ticker symbol
            timestamp: Optional timestamp (defaults to now)

        Returns:
            Path to HTML report file

        Requirements:
            9.2, 9.3, 9.4

        """
        if timestamp is None:
            timestamp = datetime.now()

        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        filename = f"{ticker}_{timestamp_str}.html"
        path = self.session_dir / crew_name / filename

        logger.debug(f"Generated HTML path: {path}")
        return path

    def get_consolidated_json_path(self) -> Path:
        """
        Generate path for consolidated JSON report.

        Pattern: consolidated_report.json (in session root)

        Returns:
            Path to consolidated JSON report

        """
        path = self.session_dir / "consolidated_report.json"
        logger.debug(f"Generated consolidated JSON path: {path}")
        return path

    def get_final_report_path(self) -> Path:
        """
        Generate path for final HTML report.

        Pattern: final_report.html (in session root)

        Returns:
            Path to final HTML report

        """
        path = self.session_dir / "final_report.html"
        logger.debug(f"Generated final report path: {path}")
        return path

    def get_manifest_path(self) -> Path:
        """
        Generate path for report manifest.

        Pattern: manifest.json (in session root)

        Returns:
            Path to manifest file

        Requirements:
            9.5, 9.6, 9.7

        """
        path = self.session_dir / "manifest.json"
        logger.debug(f"Generated manifest path: {path}")
        return path


class ManifestManager:
    """
    Manage report manifest for tracking generated files.

    This class handles creation, updating, and persistence of the report
    manifest. The manifest tracks all generated files with metadata for
    audit and debugging purposes.

    Attributes:
        session_id: Unique session identifier
        manifest_path: Path to manifest file
        manifest: ReportManifest instance

    Requirements:
        9.5, 9.6, 9.7

    """

    def __init__(self, session_id: str, base_output_dir: str = "output/reports") -> None:
        """
        Initialize manifest manager.

        Args:
            session_id: Unique session identifier
            base_output_dir: Base output directory (default: output/reports)

        """
        self.session_id = session_id
        path_helper = FilePathHelper(session_id, base_output_dir)
        self.manifest_path = path_helper.get_manifest_path()

        # Load existing manifest or create new one
        if self.manifest_path.exists():
            logger.info(f"Loading existing manifest from {self.manifest_path}")
            self.manifest = self._load_manifest()
        else:
            logger.info(f"Creating new manifest for session {session_id}")
            self.manifest = ReportManifest(session_id=session_id)

    def _load_manifest(self) -> ReportManifest:
        """
        Load manifest from disk.

        Returns:
            ReportManifest instance

        """
        try:
            import json

            data = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            return ReportManifest.model_validate(data)
        except Exception as e:
            logger.error(f"Failed to load manifest from {self.manifest_path}: {e}")
            logger.warning("Creating new manifest")
            return ReportManifest(session_id=self.session_id)

    def save_manifest(self) -> None:
        """
        Save manifest to disk.

        Raises:
            OSError: If manifest cannot be saved

        Requirements:
            9.5, 9.6, 9.7

        """
        try:
            # Ensure directory exists
            self.manifest_path.parent.mkdir(parents=True, exist_ok=True)

            # Save manifest
            self.manifest_path.write_text(self.manifest.model_dump_json(indent=2), encoding="utf-8")

            logger.debug(f"Saved manifest to {self.manifest_path}")

        except Exception as e:
            error_msg = f"Failed to save manifest to {self.manifest_path}: {e}"
            logger.error(error_msg)
            raise OSError(error_msg) from e

    def add_file(
        self,
        crew_name: str,
        ticker: str,
        asset_class: str,
        status: str,
        export_path: str | None = None,
        html_path: str | None = None,
    ) -> None:
        """
        Add a file entry to the manifest and save.

        Args:
            crew_name: Name of the crew that generated the file
            ticker: Asset ticker symbol
            asset_class: Asset class (stock, etf, crypto)
            status: Generation status (completed, failed)
            export_path: Path to JSON export file (optional)
            html_path: Path to HTML report file (optional)

        Requirements:
            9.5, 9.6, 9.7

        """
        self.manifest.add_file(
            crew_name=crew_name,
            ticker=ticker,
            asset_class=asset_class,
            status=status,
            export_path=export_path,
            html_path=html_path,
        )

        # Save manifest after each update
        self.save_manifest()

        logger.info(f"Added file to manifest: {crew_name}/{ticker} ({status})")

    def get_manifest(self) -> ReportManifest:
        """
        Get the current manifest.

        Returns:
            ReportManifest instance

        """
        return self.manifest

    def get_files_by_crew(self, crew_name: str) -> list[dict[str, str]]:
        """
        Get all file entries for a specific crew.

        Args:
            crew_name: Name of the crew

        Returns:
            List of file entries for the specified crew

        """
        return self.manifest.get_files_by_crew(crew_name)

    def get_files_by_status(self, status: str) -> list[dict[str, str]]:
        """
        Get all file entries with a specific status.

        Args:
            status: Status to filter by (completed, failed)

        Returns:
            List of file entries with the specified status

        """
        return self.manifest.get_files_by_status(status)
