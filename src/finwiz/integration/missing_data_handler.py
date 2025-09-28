"""
Missing data handler for crew data integration system.

This module provides comprehensive missing data detection, fallback data provision,
and recovery action suggestions for the crew data integration system.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

from finwiz.schemas.integration import (
    DataAvailabilityReport,
    DataAvailabilityStatus,
    IntegrationError,
    IntegrationErrorType,
)

logger = logging.getLogger(__name__)


class MissingDataScenario(BaseModel):
    """Represents a missing data scenario with context."""

    data_type: str = Field(description="Type of missing data (e.g., 'stock_output', 'sec_citations')")
    crew_name: str = Field(description="Name of the crew that should have provided the data")
    expected_path: str = Field(description="Expected file path for the data")
    severity: str = Field(description="Severity level: 'critical', 'high', 'medium', 'low'")
    impact_description: str = Field(description="Description of the impact of missing this data")
    fallback_available: bool = Field(description="Whether fallback data is available")


class FallbackDataProvider(BaseModel):
    """Provides fallback data for common missing scenarios."""

    data_type: str = Field(description="Type of data this fallback provides")
    fallback_data: dict = Field(description="The fallback data structure")
    quality_note: str = Field(description="Note about the quality/limitations of fallback data")
    last_updated: datetime = Field(description="When this fallback data was last updated")


class RecoveryAction(BaseModel):
    """Represents a recovery action for missing data."""

    action_type: str = Field(description="Type of recovery action")
    description: str = Field(description="Human-readable description of the action")
    command: str | None = Field(default=None, description="Command to execute (if applicable)")
    priority: int = Field(description="Priority level (1=highest, 5=lowest)")
    estimated_time_minutes: int | None = Field(default=None, description="Estimated time to complete this action")
    dependencies: list[str] = Field(default_factory=list, description="Other actions that must be completed first")


class MissingDataHandler:
    """
    Handles missing data detection, fallback provision, and recovery suggestions.

    This class provides comprehensive missing data handling for the crew data
    integration system, including detection of missing files, provision of
    fallback data, and generation of recovery action plans.
    """

    def __init__(self, output_dir: Path = Path("output")) -> None:
        """
        Initialize the missing data handler.

        Args:
            output_dir: Base output directory for crew data

        """
        self.output_dir = output_dir
        self.integration_dir = output_dir / "integration"
        self.contracts_dir = self.integration_dir / "contracts"

        # Define expected data files for each crew
        self.expected_files = {
            "stock": ["stock/stock_output.json", "integration/contracts/stock_output.json"],
            "etf": ["etf/etf_output.json", "integration/contracts/etf_output.json"],
            "crypto": ["crypto/crypto_output.json", "integration/contracts/crypto_output.json"],
            "discovery": ["discovery/discovery_output.json", "integration/contracts/discovery_output.json"],
            "portfolio": ["portfolio/portfolio_output.json"],
        }

        # Define fallback data providers
        self._initialize_fallback_providers()

        # Define recovery action templates
        self._initialize_recovery_actions()

    def _initialize_fallback_providers(self) -> None:
        """Initialize fallback data providers for common missing scenarios."""
        self.fallback_providers = {
            "stock_output": FallbackDataProvider(
                data_type="stock_output",
                fallback_data={
                    "metadata": {
                        "crew_name": "stock",
                        "execution_timestamp": datetime.now().isoformat(),
                        "schema_version": 1,
                        "validation_status": {
                            "is_valid": False,
                            "validation_timestamp": datetime.now().isoformat(),
                            "validation_errors": ["Using fallback data - no actual analysis performed"],
                            "validation_warnings": [],
                            "schema_version": 1,
                        },
                        "data_sources": [],
                        "dependencies_met": False,
                        "freshness_status": {
                            "is_fresh": False,
                            "age_hours": 999.0,
                            "max_age_hours": 24,
                            "refresh_recommended": True,
                            "last_updated": datetime.now().isoformat(),
                        },
                    },
                    "ten_k_insights": [],
                    "validated_tickers": [],
                    "market_sentiments": [],
                    "risk_assessments": [],
                    "sec_citations": [],
                },
                quality_note="Fallback data with empty analysis - requires actual crew execution",
                last_updated=datetime.now(),
            ),
            "etf_output": FallbackDataProvider(
                data_type="etf_output",
                fallback_data={
                    "metadata": {
                        "crew_name": "etf",
                        "execution_timestamp": datetime.now().isoformat(),
                        "schema_version": 1,
                        "validation_status": {
                            "is_valid": False,
                            "validation_timestamp": datetime.now().isoformat(),
                            "validation_errors": ["Using fallback data - no actual analysis performed"],
                            "validation_warnings": [],
                            "schema_version": 1,
                        },
                        "data_sources": [],
                        "dependencies_met": False,
                        "freshness_status": {
                            "is_fresh": False,
                            "age_hours": 999.0,
                            "max_age_hours": 24,
                            "refresh_recommended": True,
                            "last_updated": datetime.now().isoformat(),
                        },
                    },
                    "validated_etfs": [],
                    "factsheets": [],
                    "holdings_analysis": [],
                    "risk_assessments": [],
                },
                quality_note="Fallback data with empty analysis - requires actual crew execution",
                last_updated=datetime.now(),
            ),
            "crypto_output": FallbackDataProvider(
                data_type="crypto_output",
                fallback_data={
                    "metadata": {
                        "crew_name": "crypto",
                        "execution_timestamp": datetime.now().isoformat(),
                        "schema_version": 1,
                        "validation_status": {
                            "is_valid": False,
                            "validation_timestamp": datetime.now().isoformat(),
                            "validation_errors": ["Using fallback data - no actual analysis performed"],
                            "validation_warnings": [],
                            "schema_version": 1,
                        },
                        "data_sources": [],
                        "dependencies_met": False,
                        "freshness_status": {
                            "is_fresh": False,
                            "age_hours": 999.0,
                            "max_age_hours": 24,
                            "refresh_recommended": True,
                            "last_updated": datetime.now().isoformat(),
                        },
                    },
                    "validated_symbols": [],
                    "crypto_theses": [],
                    "risk_assessments": [],
                    "market_analysis": [],
                },
                quality_note="Fallback data with empty analysis - requires actual crew execution",
                last_updated=datetime.now(),
            ),
            "discovery_output": FallbackDataProvider(
                data_type="discovery_output",
                fallback_data={
                    "metadata": {
                        "crew_name": "discovery",
                        "execution_timestamp": datetime.now().isoformat(),
                        "schema_version": 1,
                        "validation_status": {
                            "is_valid": False,
                            "validation_timestamp": datetime.now().isoformat(),
                            "validation_errors": ["Using fallback data - no actual analysis performed"],
                            "validation_warnings": [],
                            "schema_version": 1,
                        },
                        "data_sources": [],
                        "dependencies_met": False,
                        "freshness_status": {
                            "is_fresh": False,
                            "age_hours": 999.0,
                            "max_age_hours": 24,
                            "refresh_recommended": True,
                            "last_updated": datetime.now().isoformat(),
                        },
                    },
                    "a_plus_opportunities": {
                        "etf_opportunities": [],
                        "stock_opportunities": [],
                        "crypto_opportunities": [],
                        "discovery_summary": "No discovery analysis available - using fallback data",
                        "confidence_score": 0.0,
                        "validation_timestamp": datetime.now().isoformat(),
                        "allocation_recommendations": [],
                        "replacement_notes": [],
                    },
                    "portfolio_improvements": [],
                    "optimization_results": [],
                    "validation_results": [],
                    "market_analysis": {},
                },
                quality_note="Fallback data with empty analysis - requires actual crew execution",
                last_updated=datetime.now(),
            ),
        }

    def _initialize_recovery_actions(self) -> None:
        """Initialize recovery action templates."""
        self.recovery_action_templates = {
            "missing_stock_data": [
                RecoveryAction(
                    action_type="execute_crew",
                    description="Execute Stock crew to generate missing stock analysis data",
                    command="uv run python src/finwiz/main.py --crew stock",
                    priority=1,
                    estimated_time_minutes=15,
                    dependencies=[],
                ),
                RecoveryAction(
                    action_type="check_inputs",
                    description="Verify that required input tickers are provided and valid",
                    priority=2,
                    estimated_time_minutes=2,
                    dependencies=[],
                ),
            ],
            "missing_etf_data": [
                RecoveryAction(
                    action_type="execute_crew",
                    description="Execute ETF crew to generate missing ETF analysis data",
                    command="uv run python src/finwiz/main.py --crew etf",
                    priority=1,
                    estimated_time_minutes=10,
                    dependencies=[],
                ),
                RecoveryAction(
                    action_type="check_inputs",
                    description="Verify that required ETF symbols are provided and valid",
                    priority=2,
                    estimated_time_minutes=2,
                    dependencies=[],
                ),
            ],
            "missing_crypto_data": [
                RecoveryAction(
                    action_type="execute_crew",
                    description="Execute Crypto crew to generate missing crypto analysis data",
                    command="uv run python src/finwiz/main.py --crew crypto",
                    priority=1,
                    estimated_time_minutes=12,
                    dependencies=[],
                ),
                RecoveryAction(
                    action_type="check_inputs",
                    description="Verify that required crypto symbols are provided and valid",
                    priority=2,
                    estimated_time_minutes=2,
                    dependencies=[],
                ),
            ],
            "missing_discovery_data": [
                RecoveryAction(
                    action_type="execute_crew",
                    description="Execute Discovery crew to generate missing investment discovery data",
                    command="uv run python src/finwiz/main.py --crew discovery",
                    priority=1,
                    estimated_time_minutes=20,
                    dependencies=["missing_stock_data", "missing_etf_data", "missing_crypto_data"],
                ),
                RecoveryAction(
                    action_type="check_dependencies",
                    description="Ensure Stock, ETF, and Crypto crew outputs are available",
                    priority=1,
                    estimated_time_minutes=3,
                    dependencies=[],
                ),
            ],
            "missing_portfolio_data": [
                RecoveryAction(
                    action_type="check_portfolio_file",
                    description="Check if portfolio.json file exists in the input directory",
                    priority=1,
                    estimated_time_minutes=1,
                    dependencies=[],
                ),
                RecoveryAction(
                    action_type="create_sample_portfolio",
                    description="Create a sample portfolio file if none exists",
                    priority=2,
                    estimated_time_minutes=5,
                    dependencies=["check_portfolio_file"],
                ),
            ],
        }

    def detect_missing_data(self, required_crews: list[str] | None = None) -> list[MissingDataScenario]:
        """
        Detect missing data across all crew outputs.

        Args:
            required_crews: List of crew names to check. If None, checks all crews.

        Returns:
            List of missing data scenarios found

        """
        if required_crews is None:
            required_crews = ["stock", "etf", "crypto", "discovery", "portfolio"]

        missing_scenarios = []

        for crew_name in required_crews:
            if crew_name not in self.expected_files:
                logger.warning(f"Unknown crew name: {crew_name}")
                continue

            for expected_file in self.expected_files[crew_name]:
                file_path = self.output_dir / expected_file

                if not file_path.exists():
                    scenario = self._create_missing_data_scenario(
                        crew_name=crew_name, expected_path=str(file_path), data_type=f"{crew_name}_output"
                    )
                    missing_scenarios.append(scenario)

                    logger.info(f"Missing data detected: {crew_name} - {expected_file}")

        return missing_scenarios

    def _create_missing_data_scenario(self, crew_name: str, expected_path: str, data_type: str) -> MissingDataScenario:
        """Create a missing data scenario with appropriate severity and impact."""
        # Determine severity based on crew importance
        severity_map = {
            "stock": "high",
            "etf": "medium",
            "crypto": "medium",
            "discovery": "critical",  # Discovery depends on other crews
            "portfolio": "high",
        }

        impact_map = {
            "stock": "Stock analysis and SEC citations will be unavailable in reports",
            "etf": "ETF analysis and expense ratio data will be unavailable in reports",
            "crypto": "Cryptocurrency analysis will be unavailable in reports",
            "discovery": "A+ opportunities and portfolio optimization will be unavailable",
            "portfolio": "Current portfolio analysis and rebalancing suggestions will be unavailable",
        }

        return MissingDataScenario(
            data_type=data_type,
            crew_name=crew_name,
            expected_path=expected_path,
            severity=severity_map.get(crew_name, "medium"),
            impact_description=impact_map.get(crew_name, f"{crew_name} data will be unavailable"),
            fallback_available=data_type in self.fallback_providers,
        )

    def provide_fallback_data(self, data_type: str) -> dict | None:
        """
        Provide fallback data for a missing data type.

        Args:
            data_type: Type of missing data (e.g., 'stock_output', 'etf_output')

        Returns:
            Fallback data dictionary if available, None otherwise

        """
        if data_type not in self.fallback_providers:
            logger.warning(f"No fallback data available for type: {data_type}")
            return None

        provider = self.fallback_providers[data_type]

        logger.info(f"Providing fallback data for {data_type}. Quality note: {provider.quality_note}")

        return provider.fallback_data

    def suggest_recovery_actions(self, missing_scenarios: list[MissingDataScenario]) -> list[RecoveryAction]:
        """
        Generate recovery action suggestions for missing data scenarios.

        Args:
            missing_scenarios: List of missing data scenarios

        Returns:
            List of recovery actions, sorted by priority

        """
        recovery_actions = []
        processed_types = set()

        for scenario in missing_scenarios:
            # Map scenario to recovery action type
            action_key = f"missing_{scenario.crew_name}_data"

            if action_key in processed_types:
                continue

            if action_key in self.recovery_action_templates:
                actions = self.recovery_action_templates[action_key]
                recovery_actions.extend(actions)
                processed_types.add(action_key)
            else:
                # Create generic recovery action
                generic_action = RecoveryAction(
                    action_type="manual_check",
                    description=f"Manually check and resolve missing {scenario.crew_name} data",
                    priority=3,
                    estimated_time_minutes=10,
                    dependencies=[],
                )
                recovery_actions.append(generic_action)

        # Sort by priority (lower number = higher priority)
        recovery_actions.sort(key=lambda x: x.priority)

        return recovery_actions

    def generate_missing_data_warnings(self, missing_scenarios: list[MissingDataScenario]) -> list[str]:
        """
        Generate human-readable warnings for missing data scenarios.

        Args:
            missing_scenarios: List of missing data scenarios

        Returns:
            List of warning messages

        """
        warnings = []

        for scenario in missing_scenarios:
            severity_prefix = {"critical": "🔴 CRITICAL", "high": "🟠 HIGH", "medium": "🟡 MEDIUM", "low": "🟢 LOW"}.get(
                scenario.severity, "⚪ UNKNOWN"
            )

            fallback_note = " (fallback available)" if scenario.fallback_available else " (no fallback)"

            warning = (
                f"{severity_prefix}: Missing {scenario.data_type} from {scenario.crew_name} crew. "
                f"Expected at: {scenario.expected_path}. "
                f"Impact: {scenario.impact_description}{fallback_note}"
            )

            warnings.append(warning)

        return warnings

    def create_data_availability_report(
        self, missing_scenarios: list[MissingDataScenario], recovery_actions: list[RecoveryAction]
    ) -> DataAvailabilityReport:
        """
        Create a comprehensive data availability report.

        Args:
            missing_scenarios: List of missing data scenarios
            recovery_actions: List of recovery actions

        Returns:
            Data availability report

        """
        # Check availability for each crew type
        crew_availability = {}
        missing_data_list = []
        integration_errors = []

        for crew in ["stock", "etf", "crypto", "discovery", "portfolio"]:
            crew_missing = any(s.crew_name == crew for s in missing_scenarios)
            crew_availability[f"{crew}_available"] = not crew_missing

            if crew_missing:
                missing_data_list.append(f"{crew}_output")

                # Create integration error for missing data
                error = IntegrationError(
                    error_type=IntegrationErrorType.MISSING_DATA,
                    crew_name=crew,
                    error_message=f"Missing {crew} crew output data",
                    expected_path=str(self.output_dir / f"{crew}/{crew}_output.json"),
                    recovery_suggestions=[action.description for action in recovery_actions if crew in action.description.lower()][
                        :3
                    ],  # Limit to top 3 suggestions
                    timestamp=datetime.now(),
                )
                integration_errors.append(error)

        # Determine overall status
        missing_count = len(missing_data_list)
        if missing_count == 0:
            overall_status = DataAvailabilityStatus.COMPLETE
        elif missing_count <= 2:
            overall_status = DataAvailabilityStatus.PARTIAL
        else:
            overall_status = DataAvailabilityStatus.INSUFFICIENT

        # Generate recommendations
        recommendations = []
        if missing_count > 0:
            recommendations.append(f"Execute missing crews to generate {missing_count} missing data components")
            recommendations.append("Check input parameters and API keys before crew execution")
            recommendations.append("Consider using fallback data for non-critical missing components")

        return DataAvailabilityReport(
            **crew_availability,
            missing_data=missing_data_list,
            stale_data=[],  # Will be populated by freshness checker
            integration_errors=integration_errors,
            overall_status=overall_status,
            report_timestamp=datetime.now(),
            data_freshness_summary={},  # Will be populated by freshness checker
            recommendations=recommendations,
        )

    def get_missing_data_summary(self) -> dict[str, any]:
        """
        Get a summary of missing data across all crews.

        Returns:
            Dictionary with missing data summary information

        """
        missing_scenarios = self.detect_missing_data()
        recovery_actions = self.suggest_recovery_actions(missing_scenarios)
        warnings = self.generate_missing_data_warnings(missing_scenarios)

        return {
            "missing_scenarios_count": len(missing_scenarios),
            "missing_scenarios": [scenario.model_dump() for scenario in missing_scenarios],
            "recovery_actions_count": len(recovery_actions),
            "recovery_actions": [action.model_dump() for action in recovery_actions],
            "warnings": warnings,
            "fallback_available_count": sum(1 for s in missing_scenarios if s.fallback_available),
            "critical_missing_count": sum(1 for s in missing_scenarios if s.severity == "critical"),
        }
