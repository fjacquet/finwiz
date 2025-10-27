"""
Crew Export Data Migration Utility.

This module migrates existing crew output files from the old format to the new
DeepAnalysisCrewExport schema format. This is needed because the current crew
outputs use fields like 'execution_id', 'analysis_timestamp', etc., but the
new schema expects 'session_id', 'risk_assessment', etc.

Usage:
    from finwiz.utils.crew_export_migrator import CrewExportMigrator

    migrator = CrewExportMigrator()
    migrator.migrate_all_outputs("output/")
"""

import json
from pathlib import Path
from typing import Any

from finwiz.schemas.crew_exports import DeepAnalysisCrewExport
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class CrewExportMigrator:
    """Migrates crew export files from old format to new schema format."""

    def __init__(self):
        """Initialize the migrator."""
        self.migrated_count = 0
        self.error_count = 0

    def migrate_all_outputs(self, output_dir: str | Path) -> dict[str, int]:
        """
        Migrate all crew output files in the specified directory.

        Args:
            output_dir: Path to output directory containing crew files

        Returns:
            Dict with migration statistics

        """
        output_path = Path(output_dir)
        stats = {"migrated": 0, "errors": 0, "skipped": 0}

        logger.info(f"Starting migration of crew outputs in {output_path}")

        # Process stock outputs
        stock_dir = output_path / "stock"
        if stock_dir.exists():
            stats_stock = self._migrate_directory(stock_dir, "stock")
            stats["migrated"] += stats_stock["migrated"]
            stats["errors"] += stats_stock["errors"]
            stats["skipped"] += stats_stock["skipped"]

        # Process ETF outputs
        etf_dir = output_path / "etf"
        if etf_dir.exists():
            stats_etf = self._migrate_directory(etf_dir, "etf")
            stats["migrated"] += stats_etf["migrated"]
            stats["errors"] += stats_etf["errors"]
            stats["skipped"] += stats_etf["skipped"]

        # Process crypto outputs
        crypto_dir = output_path / "crypto"
        if crypto_dir.exists():
            stats_crypto = self._migrate_directory(crypto_dir, "crypto")
            stats["migrated"] += stats_crypto["migrated"]
            stats["errors"] += stats_crypto["errors"]
            stats["skipped"] += stats_crypto["skipped"]

        logger.info(f"Migration complete: {stats['migrated']} migrated, {stats['errors']} errors, {stats['skipped']} skipped")
        return stats

    def _migrate_directory(self, directory: Path, asset_class: str) -> dict[str, int]:
        """Migrate all JSON files in a directory."""
        stats = {"migrated": 0, "errors": 0, "skipped": 0}

        for json_file in directory.glob("*.json"):
            try:
                result = self.migrate_file(json_file, asset_class)
                if result:
                    stats["migrated"] += 1
                    logger.debug(f"✅ Migrated {json_file}")
                else:
                    stats["skipped"] += 1
                    logger.debug(f"⏭️ Skipped {json_file} (already migrated)")
            except Exception as e:
                stats["errors"] += 1
                logger.error(f"❌ Failed to migrate {json_file}: {e}")

        return stats

    def migrate_file(self, file_path: str | Path, asset_class: str) -> bool:
        """
        Migrate a single crew output file to new schema format.

        Args:
            file_path: Path to the JSON file to migrate
            asset_class: Asset class (stock, etf, crypto)

        Returns:
            True if migration was performed, False if already migrated or skipped

        """
        path = Path(file_path)

        if not path.exists():
            logger.warning(f"File not found: {path}")
            return False

        try:
            # Read existing data
            with open(path, encoding="utf-8") as f:
                old_data = json.load(f)

            # Check if already migrated (has session_id and risk_assessment)
            if "session_id" in old_data and "risk_assessment" in old_data:
                logger.debug(f"File already migrated: {path}")
                return False

            # Migrate to new format
            migrated_data = self._transform_to_new_format(old_data, asset_class)

            # Validate against new schema
            try:
                DeepAnalysisCrewExport.model_validate(migrated_data)
            except Exception as e:
                logger.error(f"Validation failed for {path}: {e}")
                return False

            # Write migrated data back to file
            with open(path, "w", encoding="utf-8") as f:
                json.dump(migrated_data, f, indent=2, default=str)

            logger.info(f"✅ Successfully migrated {path}")
            return True

        except Exception as e:
            logger.error(f"Failed to migrate {path}: {e}")
            return False

    def _transform_to_new_format(self, old_data: dict[str, Any], asset_class: str) -> dict[str, Any]:
        """Transform old format data to new DeepAnalysisCrewExport format."""
        # Extract ticker from filename or data
        ticker = old_data.get("ticker", "UNKNOWN")

        # Create session_id from execution_id if available
        session_id = old_data.get("execution_id", f"migrated-{ticker}")

        # Create risk assessment from old risk data
        risk_assessment = self._create_risk_assessment(old_data)

        # Create new format data
        new_data = {
            "crew_name": "deep_analysis_crew",
            "ticker": ticker,
            "asset_class": asset_class,
            "session_id": session_id,
            "analysis_date": old_data.get("analysis_timestamp", "2025-10-26T21:00:00Z"),
            # Analysis results
            "detailed_analysis": {
                "fundamental_score": old_data.get("fundamental_score", 0.0),
                "technical_score": old_data.get("technical_score", 0.0),
                "risk_score": old_data.get("risk_score", 0.0),
                "fundamental_details": old_data.get("fundamental_details", {}),
                "technical_details": old_data.get("technical_details", {}),
                "risk_details": old_data.get("risk_details", {}),
                "performance_metrics": old_data.get("performance_metrics", {}),
            },
            "risk_assessment": risk_assessment,
            # Scores and grades
            "composite_score": old_data.get("composite_score", 0.0),
            "grade": old_data.get("grade", "C"),
            # Recommendations
            "recommendation": old_data.get("recommendation", "HOLD"),
            "confidence": old_data.get("confidence", 0.5),
            "rationale": old_data.get("rationale", "Analysis completed with available data."),
            # Metadata
            "data_sources": old_data.get("data_sources", ["Yahoo Finance", "Alpha Vantage"]),
            "report_html_path": f"output/{asset_class}/{ticker}_report.html",
            "report_json_path": f"output/{asset_class}/{ticker}_default.json",
        }

        return new_data

    def _create_risk_assessment(self, old_data: dict[str, Any]) -> dict[str, Any]:
        """Create a RiskAssessmentStandardized object from old risk data."""
        risk_details = old_data.get("risk_details", {})

        # Extract risk metrics with defaults
        volatility = risk_details.get("volatility", 0.2)
        max_drawdown = risk_details.get("max_drawdown", -0.15)

        # Calculate risk score (0-5 scale for RiskAssessmentStandardized)
        risk_score_raw = old_data.get("risk_score", 0.7)
        risk_score = max(0.0, min(5.0, risk_score_raw * 5))  # Convert to 0-5 scale

        # Map score to risk level
        risk_level = self._get_risk_level(risk_score)

        # Create standardized risk assessment
        risk_assessment = {
            "scale": "0_5",
            "score": risk_score,
            "level": risk_level,
            "risk_factors": ["Market volatility", "Sector concentration", "Liquidity risk", "Economic uncertainty"],
        }

        return risk_assessment

    def _get_risk_level(self, risk_score: float) -> str:
        """Get risk level based on risk score (0-5 scale)."""
        if risk_score <= 1.0:
            return "Low"
        elif risk_score <= 2.5:
            return "Medium"
        elif risk_score <= 4.0:
            return "High"
        else:
            return "Very High"


def migrate_crew_outputs(output_dir: str = "output/") -> dict[str, int]:
    """
    Convenience function to migrate all crew outputs.

    Args:
        output_dir: Path to output directory

    Returns:
        Migration statistics

    """
    migrator = CrewExportMigrator()
    return migrator.migrate_all_outputs(output_dir)


if __name__ == "__main__":
    # Run migration if called directly
    stats = migrate_crew_outputs()
    print(f"Migration complete: {stats}")
