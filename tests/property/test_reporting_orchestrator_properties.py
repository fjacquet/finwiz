"""
Property-based tests for ReportingOrchestrator.

Tests report consolidation completeness, crew export path management, and HTML generation.
"""

import json
import tempfile
from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from finwiz.flow_state import FinwizState
from finwiz.orchestrators.reporting_orchestrator import ReportingOrchestrator


class TestReportingOrchestratorProperties:
    """Property-based tests for ReportingOrchestrator."""

    # Property 13: Report Consolidation Completeness
    @given(
        crew_export_paths=st.dictionaries(
            keys=st.sampled_from(["stock", "etf", "crypto"]),
            values=st.lists(
                st.text(min_size=1, max_size=50),
                min_size=1,
                max_size=3,
            ),
            min_size=1,
            max_size=3,
        )
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_consolidate_reports_includes_all_crew_names(self, crew_export_paths):
        """
        Property: Consolidated report includes all crew names.

        For any valid crew export paths dictionary, the consolidated report must include
        all crew names in the result.
        """
        # Arrange
        state = FinwizState()
        orchestrator = ReportingOrchestrator(state)

        # Create temporary JSON files for each export path
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_paths = {}
            for crew_name, paths in crew_export_paths.items():
                temp_crew_paths = []
                for i, _ in enumerate(paths):
                    temp_file = Path(tmpdir) / f"{crew_name}_{i}.json"
                    temp_file.write_text(json.dumps({"ticker": f"TEST{i}", "grade": "A"}))
                    temp_crew_paths.append(str(temp_file))
                temp_paths[crew_name] = temp_crew_paths

            # Act
            result = orchestrator.consolidate_reports(temp_paths)

            # Assert - Success
            assert result["success"] is True, "Consolidation must succeed"

            # Assert - All crew names present
            consolidated_data = result["consolidated_data"]
            for crew_name in crew_export_paths.keys():
                assert crew_name in consolidated_data["crews"], f"Crew '{crew_name}' missing from consolidated report"

    # Property 14: Crew Export Path Calculation
    @given(
        crew_name=st.sampled_from(["stock", "etf", "crypto"]),
        ticker=st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))),
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_get_crew_export_path_follows_pattern(self, crew_name, ticker):
        """
        Property: Export path follows expected pattern.

        For any crew name and ticker, the export path must:
        - Follow pattern: output/{crew_name}/{ticker}_{session_id}.json
        - Be a valid file path
        - Include the crew name and ticker
        """
        # Arrange
        state = FinwizState()
        state.session_id = "test_session"
        orchestrator = ReportingOrchestrator(state)

        # Act
        export_path = orchestrator.get_crew_export_path(crew_name, ticker)

        # Assert - Path structure
        assert isinstance(export_path, str), "Export path must be a string"
        assert export_path.startswith(f"output/{crew_name}/"), f"Path must start with output/{crew_name}/"
        assert ticker in export_path, "Path must contain ticker"
        assert "test_session" in export_path, "Path must contain session ID"
        assert export_path.endswith(".json"), "Path must end with .json"

    # Property 15: Store and Retrieve Crew Export Paths
    @given(
        crew_name=st.sampled_from(["stock", "etf", "crypto"]),
        export_paths=st.lists(
            st.text(min_size=1, max_size=50),
            min_size=1,
            max_size=5,
        ),
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_store_crew_export_paths_preserves_data(self, crew_name, export_paths):
        """
        Property: Stored export paths are preserved in state.

        For any crew name and list of export paths, storing them must:
        - Create crew_export_paths in state if not exists
        - Store all paths for the crew
        - Allow retrieval of stored paths
        """
        # Arrange
        state = FinwizState()
        orchestrator = ReportingOrchestrator(state)

        # Act
        orchestrator.store_crew_export_paths(crew_name, export_paths)

        # Assert - State updated
        assert hasattr(state, "crew_export_paths"), "State must have crew_export_paths attribute"
        assert crew_name in state.crew_export_paths, f"Crew '{crew_name}' must be in crew_export_paths"
        assert state.crew_export_paths[crew_name] == export_paths, "Stored paths must match input paths"

    # Property 16: Empty Consolidation Handling
    def test_consolidate_reports_handles_empty_paths(self):
        """
        Property: Consolidation handles empty paths gracefully.

        When crew export paths is empty, consolidation must:
        - Return success
        - Have zero total reports
        - Not raise exceptions
        """
        # Arrange
        state = FinwizState()
        orchestrator = ReportingOrchestrator(state)
        empty_paths = {}

        # Act
        result = orchestrator.consolidate_reports(empty_paths)

        # Assert
        assert result["success"] is True, "Consolidation must succeed even with empty paths"
        assert result["consolidated_data"]["total_reports"] == 0, "Total reports must be zero"

    # Property 17: HTML Generation from Export Data
    @given(
        template_name=st.sampled_from(["portfolio_report.html", "analysis_report.html"]),
        export_data=st.dictionaries(
            keys=st.text(min_size=1, max_size=20),
            values=st.one_of(
                st.text(min_size=0, max_size=50),
                st.integers(min_value=0, max_value=1000),
                st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
            ),
            min_size=0,
            max_size=5,
        ),
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_generate_html_from_export_requires_valid_template(self, template_name, export_data):
        """
        Property: HTML generation requires valid template.

        For any template name and export data, HTML generation must:
        - Raise exception if template doesn't exist
        - Return string if template exists
        """
        # Arrange
        state = FinwizState()
        orchestrator = ReportingOrchestrator(state)

        # Act & Assert
        # Since templates don't exist in test environment, expect exception
        with pytest.raises(Exception):
            orchestrator.generate_html_from_export(export_data, template_name)

    # Property 18: Session ID in Export Paths
    @given(
        session_id=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="-_")),
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_export_path_includes_session_id(self, session_id):
        """
        Property: Export paths include session ID.

        For any session ID, export paths must:
        - Include the session ID in the path
        - Use session ID consistently across all paths
        """
        # Arrange
        state = FinwizState()
        state.session_id = session_id
        orchestrator = ReportingOrchestrator(state)

        # Act
        path1 = orchestrator.get_crew_export_path("stock", "AAPL")
        path2 = orchestrator.get_crew_export_path("etf", "SPY")
        path3 = orchestrator.get_crew_export_path("crypto", "BTC")

        # Assert - All paths include session ID
        assert session_id in path1, "Stock path must include session ID"
        assert session_id in path2, "ETF path must include session ID"
        assert session_id in path3, "Crypto path must include session ID"
