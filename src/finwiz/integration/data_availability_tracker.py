"""
Data Availability Tracker for Report Generation.

This module tracks data source availability and freshness for financial report generation.
It provides transparency about which data sources are available, stale, or missing,
helping users assess the reliability of the analysis.
"""

import logging
from datetime import datetime

from pydantic import BaseModel, Field


class SourceStatus(BaseModel):
    """Status information for a single data source."""

    source_name: str = Field(..., description="Name of the data source")
    status: str = Field(..., description="Status: available, unavailable, stale")
    age_hours: float | None = Field(None, description="Age of data in hours")
    last_updated: datetime | None = Field(None, description="When data was last updated")
    error_message: str | None = Field(None, description="Error message if unavailable")
    record_count: int | None = Field(None, description="Number of records in data source")


class DataAvailabilitySummary(BaseModel):
    """Summary of data availability across all sources."""

    total_sources: int = Field(..., ge=0, description="Total number of data sources tracked")
    available_sources: int = Field(..., ge=0, description="Number of available sources")
    unavailable_sources: int = Field(..., ge=0, description="Number of unavailable sources")
    stale_sources: int = Field(..., ge=0, description="Number of stale sources (>7 days)")
    freshness_warnings: list[str] = Field(default_factory=list, description="List of freshness warnings")
    source_details: dict[str, SourceStatus] = Field(default_factory=dict, description="Detailed status for each source")
    summary_timestamp: datetime = Field(default_factory=datetime.now, description="When summary was generated")


class DataAvailabilityTracker:
    """
    Track and report data availability and freshness for report generation.

    This class provides methods to track data sources, calculate data age,
    identify stale data, and generate comprehensive availability summaries
    for inclusion in financial reports.
    """

    def __init__(
        self,
        stale_threshold_hours: float = 168.0,  # 7 days
        logger: logging.Logger | None = None,
    ) -> None:
        """
        Initialize the data availability tracker.

        Args:
            stale_threshold_hours: Hours after which data is considered stale (default: 168 = 7 days)
            logger: Optional logger instance for logging operations

        """
        self.stale_threshold_hours = stale_threshold_hours
        self.logger = logger or logging.getLogger(__name__)
        self._tracked_sources: dict[str, SourceStatus] = {}

        self.logger.info(
            "DataAvailabilityTracker initialized",
            extra={"stale_threshold_hours": stale_threshold_hours},
        )

    def track_data_source(
        self,
        source: str,
        status: str,
        age_hours: float | None = None,
        last_updated: datetime | None = None,
        error_message: str | None = None,
        record_count: int | None = None,
    ) -> None:
        """
        Track availability of a data source.

        Args:
            source: Name of the data source (e.g., "sentiment", "sec_filings", "portfolio")
            status: Status of the source ("available", "unavailable", "stale")
            age_hours: Age of the data in hours (optional)
            last_updated: When the data was last updated (optional)
            error_message: Error message if source is unavailable (optional)
            record_count: Number of records in the data source (optional)

        """
        try:
            # Calculate age_hours from last_updated if not provided
            if age_hours is None and last_updated is not None:
                # Handle both datetime objects and ISO format strings
                if isinstance(last_updated, str):
                    from dateutil import parser
                    last_updated = parser.isoparse(last_updated)
                
                age_delta = datetime.now() - last_updated
                age_hours = age_delta.total_seconds() / 3600

            # Determine if data is stale
            if status == "available" and age_hours is not None:
                if age_hours > self.stale_threshold_hours:
                    status = "stale"

            source_status = SourceStatus(
                source_name=source,
                status=status,
                age_hours=age_hours,
                last_updated=last_updated,
                error_message=error_message,
                record_count=record_count,
            )

            self._tracked_sources[source] = source_status

            self.logger.info(
                f"Tracked data source: {source}",
                extra={
                    "source": source,
                    "status": status,
                    "age_hours": age_hours,
                    "record_count": record_count,
                },
            )

        except Exception as e:
            self.logger.error(f"Failed to track data source {source}: {str(e)}", exc_info=True)

    def get_availability_summary(self) -> DataAvailabilitySummary:
        """
        Get summary of all tracked data sources.

        Returns:
            DataAvailabilitySummary with aggregated availability information

        """
        try:
            total_sources = len(self._tracked_sources)
            available_sources = sum(1 for s in self._tracked_sources.values() if s.status == "available")
            unavailable_sources = sum(1 for s in self._tracked_sources.values() if s.status == "unavailable")
            stale_sources = sum(1 for s in self._tracked_sources.values() if s.status == "stale")

            # Generate freshness warnings
            freshness_warnings = self.get_freshness_warnings()

            summary = DataAvailabilitySummary(
                total_sources=total_sources,
                available_sources=available_sources,
                unavailable_sources=unavailable_sources,
                stale_sources=stale_sources,
                freshness_warnings=freshness_warnings,
                source_details=self._tracked_sources.copy(),
                summary_timestamp=datetime.now(),
            )

            self.logger.info(
                "Generated availability summary",
                extra={
                    "total_sources": total_sources,
                    "available": available_sources,
                    "unavailable": unavailable_sources,
                    "stale": stale_sources,
                },
            )

            return summary

        except Exception as e:
            self.logger.error(f"Failed to generate availability summary: {str(e)}", exc_info=True)
            # Return empty summary on error
            return DataAvailabilitySummary(
                total_sources=0,
                available_sources=0,
                unavailable_sources=0,
                stale_sources=0,
                freshness_warnings=["Error generating availability summary"],
                source_details={},
            )

    def get_freshness_warnings(self) -> list[str]:
        """
        Get list of freshness warnings for stale data.

        Returns:
            List of warning messages for stale or unavailable data sources

        """
        warnings = []

        try:
            for source_name, source_status in self._tracked_sources.items():
                # Stale data warning
                if source_status.status == "stale" and source_status.age_hours is not None:
                    age_days = source_status.age_hours / 24
                    warnings.append(f"{source_name}: Data is {age_days:.1f} days old (threshold: {self.stale_threshold_hours / 24:.1f} days)")

                # Unavailable data warning
                elif source_status.status == "unavailable":
                    error_msg = source_status.error_message or "No error details"
                    warnings.append(f"{source_name}: Data not available - {error_msg}")

            self.logger.debug(f"Generated {len(warnings)} freshness warnings")

        except Exception as e:
            self.logger.error(f"Failed to generate freshness warnings: {str(e)}", exc_info=True)
            warnings.append("Error generating freshness warnings")

        return warnings

    def get_source_status(self, source: str) -> SourceStatus | None:
        """
        Get status for a specific data source.

        Args:
            source: Name of the data source

        Returns:
            SourceStatus for the source, or None if not tracked

        """
        return self._tracked_sources.get(source)

    def is_source_available(self, source: str) -> bool:
        """
        Check if a data source is available (not stale or unavailable).

        Args:
            source: Name of the data source

        Returns:
            True if source is available, False otherwise

        """
        source_status = self.get_source_status(source)
        if source_status is None:
            return False
        return source_status.status == "available"

    def is_source_stale(self, source: str) -> bool:
        """
        Check if a data source is stale.

        Args:
            source: Name of the data source

        Returns:
            True if source is stale, False otherwise

        """
        source_status = self.get_source_status(source)
        if source_status is None:
            return False
        return source_status.status == "stale"

    def clear_tracked_sources(self) -> None:
        """Clear all tracked data sources."""
        self._tracked_sources.clear()
        self.logger.info("Cleared all tracked data sources")

    def get_tracked_source_names(self) -> list[str]:
        """
        Get list of all tracked source names.

        Returns:
            List of source names

        """
        return list(self._tracked_sources.keys())

    def format_summary_for_report(self, summary: DataAvailabilitySummary | None = None) -> str:
        """
        Format availability summary for inclusion in reports.

        Args:
            summary: Optional DataAvailabilitySummary to format (generates new one if None)

        Returns:
            Formatted string for report display

        """
        if summary is None:
            summary = self.get_availability_summary()

        try:
            lines = []
            lines.append("=== Data Availability Summary ===")
            lines.append(f"Total Data Sources: {summary.total_sources}")
            lines.append(f"Available: {summary.available_sources}")
            lines.append(f"Unavailable: {summary.unavailable_sources}")
            lines.append(f"Stale (>7 days): {summary.stale_sources}")
            lines.append("")

            # List sources by status
            if summary.source_details:
                lines.append("Source Details:")
                for source_name, source_status in sorted(summary.source_details.items()):
                    status_icon = {
                        "available": "✅",
                        "stale": "⚠️",
                        "unavailable": "❌",
                    }.get(source_status.status, "❓")

                    age_str = ""
                    if source_status.age_hours is not None:
                        age_days = source_status.age_hours / 24
                        age_str = f" ({age_days:.1f} days old)"

                    count_str = ""
                    if source_status.record_count is not None:
                        count_str = f" - {source_status.record_count} records"

                    lines.append(f"  {status_icon} {source_name}: {source_status.status}{age_str}{count_str}")

            # Add freshness warnings
            if summary.freshness_warnings:
                lines.append("")
                lines.append("Freshness Warnings:")
                for warning in summary.freshness_warnings:
                    lines.append(f"  ⚠️ {warning}")

            lines.append("")
            lines.append(f"Summary generated: {summary.summary_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

            return "\n".join(lines)

        except Exception as e:
            self.logger.error(f"Failed to format summary for report: {str(e)}", exc_info=True)
            return "Error formatting data availability summary"
