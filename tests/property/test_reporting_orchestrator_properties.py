"""
Property-based tests for ReportingOrchestrator.

Tests report consolidation completeness.
"""

import json
import tempfile
from pathlib import Path

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
