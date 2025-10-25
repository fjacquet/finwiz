"""
Data Quality Metrics Tracker for FinWiz.

Tracks data quality metrics throughout the flow execution to ensure
that expensive crew analysis is being properly consumed and not replaced
with fallback data.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class DataQualityMetrics(BaseModel):
    """
    Track data quality metrics throughout flow execution.

    Monitors:
    - Fallback grades usage (Grade D with score 0.6)
    - Placeholder URLs (example.com)
    - Missing data fields
    - Successful/failed data merges
    - Overall quality score
    """

    # Counters for data quality issues
    fallback_grades_count: int = Field(default=0, description="Count of fallback Grade D usage")
    placeholder_urls_count: int = Field(default=0, description="Count of example.com placeholder URLs")
    missing_data_count: int = Field(default=0, description="Count of missing data fields")

    # Counters for merge operations
    successful_merges_count: int = Field(default=0, description="Count of successful data merges")
    failed_merges_count: int = Field(default=0, description="Count of failed data merges")

    # Tracking details
    fallback_tickers: list[str] = Field(default_factory=list, description="Tickers with fallback data")
    placeholder_url_locations: list[str] = Field(default_factory=list, description="Locations with placeholder URLs")
    missing_data_fields: list[str] = Field(default_factory=list, description="Missing data field names")

    # Metadata
    flow_execution_id: str | None = Field(default=None, description="Flow execution identifier")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Metrics timestamp")

    model_config = {"extra": "forbid"}

    def record_fallback_grade(self, ticker: str) -> None:
        """
        Record when a fallback grade is used.

        Args:
            ticker: Ticker symbol with fallback grade

        """
        self.fallback_grades_count += 1
        if ticker not in self.fallback_tickers:
            self.fallback_tickers.append(ticker)

        logger.warning(f"⚠️ Fallback grade detected for {ticker} (total fallbacks: {self.fallback_grades_count})")

    def record_placeholder_url(self, location: str) -> None:
        """
        Record when a placeholder URL is detected.

        Args:
            location: Location/context where placeholder was found

        """
        self.placeholder_urls_count += 1
        if location not in self.placeholder_url_locations:
            self.placeholder_url_locations.append(location)

        logger.warning(f"⚠️ Placeholder URL detected at {location} (total placeholders: {self.placeholder_urls_count})")

    def record_missing_data(self, field_name: str) -> None:
        """
        Record when required data is missing.

        Args:
            field_name: Name of the missing data field

        """
        self.missing_data_count += 1
        if field_name not in self.missing_data_fields:
            self.missing_data_fields.append(field_name)

        logger.warning(f"⚠️ Missing data field: {field_name} (total missing: {self.missing_data_count})")

    def record_successful_merge(self, ticker: str) -> None:
        """
        Record a successful data merge.

        Args:
            ticker: Ticker symbol that was successfully merged

        """
        self.successful_merges_count += 1
        logger.info(f"✅ Successful merge for {ticker} (total successful: {self.successful_merges_count})")

    def record_failed_merge(self, ticker: str, reason: str) -> None:
        """
        Record a failed data merge.

        Args:
            ticker: Ticker symbol that failed to merge
            reason: Reason for merge failure

        """
        self.failed_merges_count += 1
        logger.error(f"❌ Failed merge for {ticker}: {reason} (total failures: {self.failed_merges_count})")

    def calculate_quality_score(self) -> float:
        """
        Calculate overall data quality score (0-1).

        Score calculation:
        - Start with 1.0 (perfect quality)
        - Penalize for fallback grades
        - Penalize for placeholder URLs
        - Penalize for missing data
        - Penalize for failed merges
        - Reward for successful merges

        Returns:
            Quality score between 0.0 and 1.0

        """
        total_operations = self.successful_merges_count + self.failed_merges_count

        if total_operations == 0:
            # No operations yet, return neutral score
            return 0.5

        # Calculate penalties
        penalties = (
            self.fallback_grades_count
            + self.placeholder_urls_count
            + self.missing_data_count
            + (self.failed_merges_count * 2)  # Failed merges are worse
        )

        # Calculate quality score
        # Each penalty reduces score proportionally to total operations
        penalty_ratio = penalties / max(total_operations, 1)
        quality_score = max(0.0, 1.0 - penalty_ratio)

        return quality_score

    def get_summary(self) -> dict[str, Any]:
        """
        Get a summary of data quality metrics.

        Returns:
            Dictionary with metrics summary

        """
        quality_score = self.calculate_quality_score()

        summary = {
            "quality_score": quality_score,
            "quality_grade": self._get_quality_grade(quality_score),
            "metrics": {
                "fallback_grades": self.fallback_grades_count,
                "placeholder_urls": self.placeholder_urls_count,
                "missing_data": self.missing_data_count,
                "successful_merges": self.successful_merges_count,
                "failed_merges": self.failed_merges_count,
            },
            "details": {
                "fallback_tickers": self.fallback_tickers,
                "placeholder_locations": self.placeholder_url_locations,
                "missing_fields": self.missing_data_fields,
            },
            "timestamp": self.timestamp,
            "flow_execution_id": self.flow_execution_id,
        }

        return summary

    def _get_quality_grade(self, score: float) -> str:
        """
        Convert quality score to letter grade.

        Args:
            score: Quality score (0-1)

        Returns:
            Letter grade (A+, A, B, C, D, F)

        """
        if score >= 0.95:
            return "A+"
        elif score >= 0.90:
            return "A"
        elif score >= 0.80:
            return "B"
        elif score >= 0.70:
            return "C"
        elif score >= 0.60:
            return "D"
        else:
            return "F"

    def log_summary(self) -> None:
        """Log a summary of data quality metrics."""
        summary = self.get_summary()
        quality_score = summary["quality_score"]
        quality_grade = summary["quality_grade"]

        logger.info("=" * 80)
        logger.info("DATA QUALITY METRICS SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Overall Quality Score: {quality_score:.2f} (Grade: {quality_grade})")
        logger.info("")
        logger.info("Metrics:")
        logger.info(f"  ✅ Successful Merges: {self.successful_merges_count}")
        logger.info(f"  ❌ Failed Merges: {self.failed_merges_count}")
        logger.info(f"  ⚠️  Fallback Grades: {self.fallback_grades_count}")
        logger.info(f"  ⚠️  Placeholder URLs: {self.placeholder_urls_count}")
        logger.info(f"  ⚠️  Missing Data: {self.missing_data_count}")

        if self.fallback_tickers:
            logger.info("")
            logger.info(f"Tickers with fallback data: {', '.join(self.fallback_tickers)}")

        if self.placeholder_url_locations:
            logger.info("")
            logger.info(f"Placeholder URL locations: {', '.join(self.placeholder_url_locations)}")

        if self.missing_data_fields:
            logger.info("")
            logger.info(f"Missing data fields: {', '.join(self.missing_data_fields)}")

        logger.info("=" * 80)

        # Log warnings if quality is poor
        if quality_score < 0.70:
            logger.warning(f"⚠️ DATA QUALITY BELOW ACCEPTABLE THRESHOLD: {quality_score:.2f} < 0.70")

        if self.fallback_grades_count > 0:
            logger.warning(
                f"⚠️ FALLBACK GRADES DETECTED: {self.fallback_grades_count} holdings "
                f"using Grade D fallback instead of actual analysis"
            )

        if self.placeholder_urls_count > 0:
            logger.warning(
                f"⚠️ PLACEHOLDER URLS DETECTED: {self.placeholder_urls_count} locations using example.com instead of real URLs"
            )

    def export_to_file(self, output_dir: Path) -> Path:
        """
        Export metrics to JSON file for monitoring.

        Args:
            output_dir: Directory to write metrics file

        Returns:
            Path to exported metrics file

        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data_quality_metrics_{timestamp}.json"
        filepath = output_dir / filename

        # Get summary and write to file
        summary = self.get_summary()

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        logger.info(f"📊 Data quality metrics exported to: {filepath}")

        return filepath

    def reset(self) -> None:
        """Reset all metrics to zero."""
        self.fallback_grades_count = 0
        self.placeholder_urls_count = 0
        self.missing_data_count = 0
        self.successful_merges_count = 0
        self.failed_merges_count = 0
        self.fallback_tickers = []
        self.placeholder_url_locations = []
        self.missing_data_fields = []
        self.timestamp = datetime.now().isoformat()

        logger.info("🔄 Data quality metrics reset")
