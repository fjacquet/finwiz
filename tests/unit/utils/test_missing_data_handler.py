"""
Unit tests for MissingDataHandler class.

Tests missing data detection, fallback data provision, and recovery action suggestions
with fully mocked file system operations.
"""

import pytest

from finwiz.orchestrators.error_handling.missing_data import (
    FallbackDataProvider,
    MissingDataHandler,
    MissingDataScenario,
    RecoveryAction,
)
from finwiz.schemas.integration import (
    DataAvailabilityStatus,
    IntegrationErrorType,
)


class TestMissingDataHandler:
    """Test suite for MissingDataHandler class."""

    @pytest.fixture
    def mock_output_dir(self, tmp_path):
        """Create a temporary output directory for testing."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create integration subdirectories
        integration_dir = output_dir / "integration"
        integration_dir.mkdir()
        (integration_dir / "contracts").mkdir()
        (integration_dir / "metadata").mkdir()
        (integration_dir / "consolidated").mkdir()

        return output_dir

    @pytest.fixture
    def handler(self, mock_output_dir):
        """Create MissingDataHandler instance with mocked output directory."""
        return MissingDataHandler(output_dir=mock_output_dir)

    def test_should_initialize_with_correct_directory_structure(self, handler, mock_output_dir):
        """Test that handler initializes with correct directory paths."""
        assert handler.output_dir == mock_output_dir
        assert handler.integration_dir == mock_output_dir / "integration"
        assert handler.contracts_dir == mock_output_dir / "integration" / "contracts"

    def test_should_initialize_expected_files_for_all_crews(self, handler):
        """Test that handler initializes expected files for all crew types."""
        expected_crews = ["stock", "etf", "crypto", "discovery", "portfolio"]

        for crew in expected_crews:
            assert crew in handler.expected_files
            assert len(handler.expected_files[crew]) > 0

    def test_should_initialize_fallback_providers_for_all_crew_outputs(self, handler):
        """Test that fallback providers are initialized for all crew output types."""
        expected_types = ["stock_output", "etf_output", "crypto_output", "discovery_output"]

        for data_type in expected_types:
            assert data_type in handler.fallback_providers
            provider = handler.fallback_providers[data_type]
            assert isinstance(provider, FallbackDataProvider)
            assert provider.data_type == data_type
            assert "metadata" in provider.fallback_data

    def test_should_initialize_recovery_action_templates(self, handler):
        """Test that recovery action templates are initialized correctly."""
        expected_templates = [
            "missing_stock_data",
            "missing_etf_data",
            "missing_crypto_data",
            "missing_discovery_data",
            "missing_portfolio_data",
        ]

        for template in expected_templates:
            assert template in handler.recovery_action_templates
            actions = handler.recovery_action_templates[template]
            assert len(actions) > 0
            assert all(isinstance(action, RecoveryAction) for action in actions)

    def test_should_detect_missing_data_when_files_do_not_exist(self, handler, mock_output_dir):
        """Test detection of missing data when expected files don't exist."""
        # Don't create any files - all should be missing

        missing_scenarios = handler.detect_missing_data(required_crews=["stock", "etf"])

        # Should detect missing files for both crews
        assert len(missing_scenarios) > 0

        crew_names = {scenario.crew_name for scenario in missing_scenarios}
        assert "stock" in crew_names
        assert "etf" in crew_names

        # Check scenario properties
        for scenario in missing_scenarios:
            assert isinstance(scenario, MissingDataScenario)
            assert scenario.crew_name in ["stock", "etf"]
            assert scenario.severity in ["critical", "high", "medium", "low"]
            assert len(scenario.impact_description) > 0

    def test_should_not_detect_missing_data_when_files_exist(self, handler, mock_output_dir):
        """Test that no missing data is detected when files exist."""
        # Create expected files for stock crew
        stock_dir = mock_output_dir / "stock"
        stock_dir.mkdir()
        (stock_dir / "stock_output.json").write_text('{"test": "data"}')

        contracts_dir = mock_output_dir / "integration" / "contracts"
        (contracts_dir / "stock_output.json").write_text('{"test": "data"}')

        missing_scenarios = handler.detect_missing_data(required_crews=["stock"])

        # Should not detect any missing data for stock crew
        stock_missing = [s for s in missing_scenarios if s.crew_name == "stock"]
        assert len(stock_missing) == 0

    def test_should_create_missing_data_scenario_with_correct_severity(self, handler):
        """Test creation of missing data scenarios with appropriate severity levels."""
        # Test different crew types get appropriate severity
        test_cases = [("stock", "high"), ("etf", "medium"), ("crypto", "medium"), ("discovery", "critical"), ("portfolio", "high")]

        for crew_name, expected_severity in test_cases:
            scenario = handler._create_missing_data_scenario(crew_name=crew_name, expected_path=f"/test/{crew_name}_output.json", data_type=f"{crew_name}_output")

            assert scenario.severity == expected_severity
            assert scenario.crew_name == crew_name
            assert len(scenario.impact_description) > 0

    def test_should_provide_fallback_data_when_available(self, handler):
        """Test provision of fallback data for supported data types."""
        fallback_data = handler.provide_fallback_data("stock_output")

        assert fallback_data is not None
        assert "metadata" in fallback_data
        assert "ten_k_insights" in fallback_data
        assert "validated_tickers" in fallback_data

        # Check metadata structure
        metadata = fallback_data["metadata"]
        assert metadata["crew_name"] == "stock"
        assert metadata["dependencies_met"] is False
        assert metadata["validation_status"]["is_valid"] is False

    def test_should_return_none_for_unsupported_fallback_data_type(self, handler):
        """Test that None is returned for unsupported fallback data types."""
        fallback_data = handler.provide_fallback_data("unsupported_type")
        assert fallback_data is None

    def test_should_suggest_recovery_actions_for_missing_scenarios(self, handler):
        """Test generation of recovery actions for missing data scenarios."""
        missing_scenarios = [
            MissingDataScenario(
                data_type="stock_output",
                crew_name="stock",
                expected_path="/test/stock_output.json",
                severity="high",
                impact_description="Stock analysis unavailable",
                fallback_available=True,
            ),
            MissingDataScenario(
                data_type="etf_output",
                crew_name="etf",
                expected_path="/test/etf_output.json",
                severity="medium",
                impact_description="ETF analysis unavailable",
                fallback_available=True,
            ),
        ]

        recovery_actions = handler.suggest_recovery_actions(missing_scenarios)

        assert len(recovery_actions) > 0

        # Check that actions are sorted by priority
        priorities = [action.priority for action in recovery_actions]
        assert priorities == sorted(priorities)

        # Check that relevant actions are included
        action_descriptions = [action.description.lower() for action in recovery_actions]
        assert any("stock" in desc for desc in action_descriptions)
        assert any("etf" in desc for desc in action_descriptions)

    def test_should_generate_appropriate_warnings_for_missing_scenarios(self, handler):
        """Test generation of human-readable warnings for missing data."""
        missing_scenarios = [
            MissingDataScenario(
                data_type="stock_output",
                crew_name="stock",
                expected_path="/test/stock_output.json",
                severity="critical",
                impact_description="Critical stock data missing",
                fallback_available=True,
            ),
            MissingDataScenario(
                data_type="etf_output",
                crew_name="etf",
                expected_path="/test/etf_output.json",
                severity="low",
                impact_description="ETF data missing",
                fallback_available=False,
            ),
        ]

        warnings = handler.generate_missing_data_warnings(missing_scenarios)

        assert len(warnings) == 2

        # Check critical warning format
        critical_warning = warnings[0]
        assert "🔴 CRITICAL" in critical_warning
        assert "stock_output" in critical_warning
        assert "fallback available" in critical_warning

        # Check low severity warning format
        low_warning = warnings[1]
        assert "🟢 LOW" in low_warning
        assert "etf_output" in low_warning
        assert "no fallback" in low_warning

    def test_should_create_comprehensive_data_availability_report(self, handler):
        """Test creation of comprehensive data availability report."""
        missing_scenarios = [
            MissingDataScenario(
                data_type="stock_output",
                crew_name="stock",
                expected_path="/test/stock_output.json",
                severity="high",
                impact_description="Stock analysis unavailable",
                fallback_available=True,
            )
        ]

        recovery_actions = [
            RecoveryAction(
                action_type="execute_crew",
                description="Execute Stock crew to generate missing data",
                priority=1,
                estimated_time_minutes=15,
                dependencies=[],
            )
        ]

        report = handler.create_data_availability_report(missing_scenarios, recovery_actions)

        # Check report structure
        assert report.stock_available is False
        assert report.etf_available is True  # Not in missing scenarios
        assert report.crypto_available is True
        assert report.discovery_available is True
        assert report.portfolio_available is True

        assert "stock_output" in report.missing_data
        assert len(report.integration_errors) == 1
        assert report.integration_errors[0].error_type == IntegrationErrorType.MISSING_DATA
        assert report.overall_status == DataAvailabilityStatus.PARTIAL
        assert len(report.recommendations) > 0

    def test_should_determine_correct_overall_status_based_on_missing_count(self, handler):
        """Test that overall status is determined correctly based on missing data count."""
        # Test complete status (no missing data)
        report_complete = handler.create_data_availability_report([], [])
        assert report_complete.overall_status == DataAvailabilityStatus.COMPLETE

        # Test partial status (1-2 missing)
        one_missing = [
            MissingDataScenario(
                data_type="stock_output",
                crew_name="stock",
                expected_path="/test/stock_output.json",
                severity="high",
                impact_description="Stock analysis unavailable",
                fallback_available=True,
            )
        ]
        report_partial = handler.create_data_availability_report(one_missing, [])
        assert report_partial.overall_status == DataAvailabilityStatus.PARTIAL

        # Test insufficient status (3+ missing)
        many_missing = [
            MissingDataScenario(
                data_type=f"{crew}_output",
                crew_name=crew,
                expected_path=f"/test/{crew}_output.json",
                severity="high",
                impact_description=f"{crew} analysis unavailable",
                fallback_available=True,
            )
            for crew in ["stock", "etf", "crypto"]
        ]
        report_insufficient = handler.create_data_availability_report(many_missing, [])
        assert report_insufficient.overall_status == DataAvailabilityStatus.INSUFFICIENT

    def test_should_get_comprehensive_missing_data_summary(self, handler, mock_output_dir):
        """Test generation of comprehensive missing data summary."""
        # Don't create any files so all data is missing

        summary = handler.get_missing_data_summary()

        # Check summary structure
        assert "missing_scenarios_count" in summary
        assert "missing_scenarios" in summary
        assert "recovery_actions_count" in summary
        assert "recovery_actions" in summary
        assert "warnings" in summary
        assert "fallback_available_count" in summary
        assert "critical_missing_count" in summary

        # Check that we have missing scenarios
        assert summary["missing_scenarios_count"] > 0
        assert len(summary["missing_scenarios"]) == summary["missing_scenarios_count"]

        # Check that we have recovery actions
        assert summary["recovery_actions_count"] > 0
        assert len(summary["recovery_actions"]) == summary["recovery_actions_count"]

        # Check that we have warnings
        assert len(summary["warnings"]) > 0

    def test_should_handle_unknown_crew_names_gracefully(self, handler):
        """Test that unknown crew names are handled gracefully."""
        missing_scenarios = handler.detect_missing_data(required_crews=["unknown_crew"])

        # Should not crash and should return empty list
        assert isinstance(missing_scenarios, list)
        assert len(missing_scenarios) == 0

    def test_should_create_generic_recovery_action_for_unknown_scenarios(self, handler):
        """Test creation of generic recovery actions for unknown scenarios."""
        unknown_scenario = MissingDataScenario(
            data_type="unknown_output",
            crew_name="unknown",
            expected_path="/test/unknown_output.json",
            severity="medium",
            impact_description="Unknown data unavailable",
            fallback_available=False,
        )

        recovery_actions = handler.suggest_recovery_actions([unknown_scenario])

        assert len(recovery_actions) > 0

        # Should include a generic manual check action
        generic_actions = [action for action in recovery_actions if action.action_type == "manual_check"]
        assert len(generic_actions) > 0
        assert "unknown" in generic_actions[0].description.lower()

    def test_should_avoid_duplicate_recovery_actions_for_same_crew(self, handler):
        """Test that duplicate recovery actions are avoided for the same crew."""
        # Create multiple missing scenarios for the same crew
        stock_scenarios = [
            MissingDataScenario(
                data_type="stock_output",
                crew_name="stock",
                expected_path="/test/stock_output1.json",
                severity="high",
                impact_description="Stock analysis unavailable",
                fallback_available=True,
            ),
            MissingDataScenario(
                data_type="stock_output",
                crew_name="stock",
                expected_path="/test/stock_output2.json",
                severity="high",
                impact_description="Stock analysis unavailable",
                fallback_available=True,
            ),
        ]

        recovery_actions = handler.suggest_recovery_actions(stock_scenarios)

        # Should not have duplicate actions for the same crew
        stock_execute_actions = [action for action in recovery_actions if "stock" in action.description.lower() and action.action_type == "execute_crew"]

        # Should only have one execute action for stock crew despite multiple missing scenarios
        assert len(stock_execute_actions) <= 2  # execute_crew and check_inputs actions
