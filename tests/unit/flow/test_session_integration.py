"""
Tests for session integration functionality.

This module tests the integration of session management with the main FinWiz workflow.
"""

import tempfile
from pathlib import Path

import pytest

from finwiz.schemas.session import FinancialPlan
from finwiz.utils.session_integration import (
    get_session_summary,
    initialize_session,
    save_session_with_analysis_results,
)
from finwiz.utils.session_manager import SessionParsingError


class TestSessionIntegration:
    """Test cases for session integration functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_report_path = str(Path(self.temp_dir) / "test_report.html")

    def test_should_initialize_new_session_when_no_existing_file(self):
        """Test that initialize_session creates new session when no file exists."""
        result = initialize_session(self.test_report_path)

        assert isinstance(result, FinancialPlan)
        assert result.plan_id is not None
        assert len(result.plan_id) > 0

    def test_should_load_existing_session_when_file_exists(self):
        """Test that initialize_session loads existing session when file exists."""
        # Create an existing session first
        initial_plan = initialize_session(self.test_report_path)
        initial_plan.client_profile.name = "Existing Client"

        # Save it
        save_session_with_analysis_results(initial_plan, {}, self.test_report_path)

        # Load it again
        loaded_plan = initialize_session(self.test_report_path)

        assert loaded_plan.plan_id == initial_plan.plan_id
        assert loaded_plan.client_profile.name == "Existing Client"

    def test_should_recover_from_corrupted_session(self):
        """Test that initialize_session recovers from corrupted files."""
        # Create corrupted file
        Path(self.test_report_path).write_text("Corrupted content", encoding="utf-8")

        # Should still return a valid plan (recovered or new)
        result = initialize_session(self.test_report_path)

        assert isinstance(result, FinancialPlan)
        assert result.plan_id is not None

    def test_should_save_session_with_analysis_results(self):
        """Test saving session with analysis results."""
        plan = initialize_session(self.test_report_path)

        analysis_results = {
            "portfolio_data": {
                "holdings": [{"name": "Test Stock", "ticker": "TEST", "decision": "KEEP", "composite_score": "0.75"}]
            },
            "recommendations": {"stocks": ["TEST - Test Stock"]},
        }

        # Should not raise exception
        save_session_with_analysis_results(plan, analysis_results, self.test_report_path)

        # Verify file was created
        assert Path(self.test_report_path).exists()

        # Verify data was saved (recommendations should be preserved)
        loaded_plan = initialize_session(self.test_report_path)
        assert "stocks" in loaded_plan.current_recommendations
        assert "TEST - Test Stock" in loaded_plan.current_recommendations["stocks"]

    def test_should_handle_save_failure_gracefully(self):
        """Test that save failures are handled gracefully."""
        plan = initialize_session(self.test_report_path)

        # Make directory read-only to cause save failure
        Path(self.test_report_path).parent.chmod(0o444)

        try:
            with pytest.raises(SessionParsingError):
                save_session_with_analysis_results(plan, {}, self.test_report_path)
        finally:
            # Restore permissions for cleanup
            Path(self.test_report_path).parent.chmod(0o755)

    def test_should_generate_comprehensive_session_summary(self):
        """Test that get_session_summary provides comprehensive information."""
        plan = initialize_session(self.test_report_path)
        plan.client_profile.name = "Summary Test Client"
        plan.client_profile.age = 42

        summary = get_session_summary(plan)

        assert "plan_id" in summary
        assert "created_at" in summary
        assert "last_updated" in summary
        assert summary["client_name"] == "Summary Test Client"
        assert summary["client_age"] == 42
        assert "analysis_count" in summary
        assert "has_portfolio_data" in summary
        assert "has_recommendations" in summary
        assert summary["report_language"] == "fr"
        assert summary["version"] == 1

    def test_should_update_existing_portfolio_data(self):
        """Test that analysis results are merged with existing data."""
        plan = initialize_session(self.test_report_path)

        # Add initial data
        plan.current_portfolio_data = {"existing": "data"}
        plan.current_recommendations = {"existing": ["recommendation"]}

        # Add new analysis results
        new_results = {"portfolio_data": {"new": "data"}, "recommendations": {"new": ["recommendation"]}}

        save_session_with_analysis_results(plan, new_results, self.test_report_path)

        # Verify both old and new data exist
        assert "existing" in plan.current_portfolio_data
        assert "new" in plan.current_portfolio_data
        assert "existing" in plan.current_recommendations
        assert "new" in plan.current_recommendations

    def test_should_log_session_initialization_events(self, mocker):
        """Test that session initialization events are properly logged."""
        # Arrange
        mock_logger = mocker.patch("finwiz.utils.session_integration.logger")

        # Act
        initialize_session(self.test_report_path)

        # Assert
        mock_logger.info.assert_called()

        # Check that appropriate log messages were called
        log_calls = [call.args[0] for call in mock_logger.info.call_args_list]
        assert any("creating new financial plan" in msg.lower() for msg in log_calls)

    def test_should_handle_empty_analysis_results(self):
        """Test that empty analysis results don't break the save process."""
        plan = initialize_session(self.test_report_path)

        # Save with empty results
        save_session_with_analysis_results(plan, {}, self.test_report_path)

        # Should not raise exception and file should exist
        assert Path(self.test_report_path).exists()

        # Verify plan can be loaded back
        loaded_plan = initialize_session(self.test_report_path)
        assert loaded_plan.plan_id == plan.plan_id
