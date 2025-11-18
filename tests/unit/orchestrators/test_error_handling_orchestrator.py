"""
Unit tests for ErrorHandlingOrchestrator.

Tests error handling for crew failures, error aggregation, error report generation,
and successful result pass-through.
"""

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from finwiz.flow_state import FinwizState
from finwiz.orchestrators.error_handling_orchestrator import ErrorHandlingOrchestrator


class TestErrorHandlingOrchestrator:
    """Test suite for ErrorHandlingOrchestrator."""

    @pytest.fixture
    def state(self):
        """Create a FinwizState instance for testing."""
        return FinwizState()

    @pytest.fixture
    def orchestrator(self, state):
        """Create an ErrorHandlingOrchestrator instance for testing."""
        return ErrorHandlingOrchestrator(state)

    def test_execute_crew_with_error_handling_success(self, orchestrator, mocker):
        """Test successful crew execution returns result unmodified."""
        # Arrange
        expected_result = {"analysis": "complete", "score": 0.85}
        mock_crew = mocker.Mock(return_value=expected_result)

        # Act
        result = orchestrator.execute_crew_with_error_handling(mock_crew, "test_crew", ticker="AAPL")

        # Assert
        assert result["success"] is True
        assert result["data"] == expected_result
        assert result["error"] is None
        mock_crew.assert_called_once_with(ticker="AAPL")

    def test_execute_crew_with_error_handling_failure(self, orchestrator, mocker):
        """Test crew execution failure is handled gracefully."""
        # Arrange
        error_message = "Crew execution failed"
        mock_crew = mocker.Mock(side_effect=Exception(error_message))

        # Act
        result = orchestrator.execute_crew_with_error_handling(mock_crew, "test_crew", ticker="AAPL")

        # Assert
        assert result["success"] is False
        assert result["data"] is None
        assert result["error"] is not None
        assert error_message in result["error"]["message"]
        assert result["error"]["type"] == "Exception"
        assert "test_crew" in result["error"]["context"]["crew_name"]
        assert "timestamp" in result["error"]
        assert isinstance(result["error"]["retryable"], bool)

    def test_execute_crew_with_error_handling_tracks_error_in_state(self, orchestrator, mocker):
        """Test that errors are tracked in state."""
        # Arrange
        error_message = "Crew execution failed"
        mock_crew = mocker.Mock(side_effect=Exception(error_message))

        # Act
        orchestrator.execute_crew_with_error_handling(mock_crew, "test_crew")

        # Assert
        assert len(orchestrator.state.errors) == 1
        assert "test_crew" in orchestrator.state.errors[0]
        assert error_message in orchestrator.state.errors[0]
        assert "test_crew" in orchestrator.state.crew_execution_errors
        assert orchestrator.state.crew_execution_status["test_crew"] == "failed"

    def test_generate_error_summary_empty_list(self, orchestrator):
        """Test error summary generation with empty error list."""
        # Act
        summary = orchestrator.generate_error_summary([])

        # Assert
        assert summary["total_errors"] == 0
        assert summary["error_types"] == {}
        assert summary["retryable_count"] == 0
        assert summary["non_retryable_count"] == 0
        assert summary["errors"] == []
        assert "timestamp" in summary

    def test_generate_error_summary_single_error(self, orchestrator):
        """Test error summary generation with single error."""
        # Arrange
        error = ValueError("Invalid input")

        # Act
        summary = orchestrator.generate_error_summary([error])

        # Assert
        assert summary["total_errors"] == 1
        assert summary["error_types"]["ValueError"] == 1
        assert summary["non_retryable_count"] == 1
        assert len(summary["errors"]) == 1
        assert summary["errors"][0]["message"] == "Invalid input"
        assert summary["errors"][0]["type"] == "ValueError"
        assert summary["errors"][0]["retryable"] is False

    def test_generate_error_summary_multiple_errors(self, orchestrator):
        """Test error summary generation with multiple errors."""
        # Arrange
        errors = [
            ValueError("Invalid input"),
            TimeoutError("Request timeout"),
            ValueError("Another validation error"),
            ConnectionError("Network failure"),
        ]

        # Act
        summary = orchestrator.generate_error_summary(errors)

        # Assert
        assert summary["total_errors"] == 4
        assert summary["error_types"]["ValueError"] == 2
        assert summary["error_types"]["TimeoutError"] == 1
        assert summary["error_types"]["ConnectionError"] == 1
        assert summary["retryable_count"] == 2  # TimeoutError and ConnectionError
        assert summary["non_retryable_count"] == 2  # Both ValueErrors
        assert len(summary["errors"]) == 4

    def test_generate_error_report_basic(self, orchestrator):
        """Test error report generation with basic error summary."""
        # Arrange
        error_summary = {
            "timestamp": "2025-01-01T12:00:00",
            "total_errors": 2,
            "retryable_count": 1,
            "non_retryable_count": 1,
            "error_types": {"ValueError": 1, "TimeoutError": 1},
            "errors": [
                {"type": "ValueError", "message": "Invalid input", "retryable": False, "context": {}},
                {"type": "TimeoutError", "message": "Request timeout", "retryable": True, "context": {"timeout": 30}},
            ],
        }

        # Act
        report = orchestrator.generate_error_report(error_summary)

        # Assert
        assert "ERROR REPORT" in report
        assert "Total Errors: 2" in report
        assert "Retryable: 1" in report
        assert "Non-retryable: 1" in report
        assert "ValueError: 1" in report
        assert "TimeoutError: 1" in report
        assert "Invalid input" in report
        assert "Request timeout" in report

    def test_generate_error_report_with_context(self, orchestrator):
        """Test error report includes context information."""
        # Arrange
        error_summary = {
            "timestamp": "2025-01-01T12:00:00",
            "total_errors": 1,
            "retryable_count": 0,
            "non_retryable_count": 1,
            "error_types": {"ValueError": 1},
            "errors": [
                {
                    "type": "ValueError",
                    "message": "Invalid ticker",
                    "retryable": False,
                    "context": {"ticker": "INVALID", "asset_class": "stock"},
                }
            ],
        }

        # Act
        report = orchestrator.generate_error_report(error_summary)

        # Assert
        assert "Context:" in report
        assert "ticker: INVALID" in report
        assert "asset_class: stock" in report

    def test_is_retryable_error_timeout(self, orchestrator):
        """Test that timeout errors are identified as retryable."""
        # Arrange
        error = TimeoutError("Request timeout")

        # Act
        is_retryable = orchestrator._is_retryable_error(error)

        # Assert
        assert is_retryable is True

    def test_is_retryable_error_connection(self, orchestrator):
        """Test that connection errors are identified as retryable."""
        # Arrange
        error = ConnectionError("Network failure")

        # Act
        is_retryable = orchestrator._is_retryable_error(error)

        # Assert
        assert is_retryable is True

    def test_is_retryable_error_validation(self, orchestrator):
        """Test that validation errors are identified as non-retryable."""
        # Arrange
        error = ValueError("Invalid input")

        # Act
        is_retryable = orchestrator._is_retryable_error(error)

        # Assert
        assert is_retryable is False

    def test_is_retryable_error_by_message(self, orchestrator):
        """Test that errors are identified as retryable by message content."""
        # Arrange - use "service unavailable" which is in the retryable keywords list
        error = Exception("Service unavailable")

        # Act
        is_retryable = orchestrator._is_retryable_error(error)

        # Assert
        assert is_retryable is True

    def test_execute_crew_with_error_handling_preserves_kwargs(self, orchestrator, mocker):
        """Test that kwargs are passed through to crew function."""
        # Arrange
        mock_crew = mocker.Mock(return_value={"result": "success"})

        # Act
        orchestrator.execute_crew_with_error_handling(mock_crew, "test_crew", ticker="AAPL", asset_class="stock", period=365)

        # Assert
        mock_crew.assert_called_once_with(ticker="AAPL", asset_class="stock", period=365)

    def test_error_summary_includes_all_errors(self, orchestrator):
        """Test that error summary includes all provided errors."""
        # Arrange
        errors = [Exception(f"Error {i}") for i in range(5)]

        # Act
        summary = orchestrator.generate_error_summary(errors)

        # Assert
        assert summary["total_errors"] == 5
        assert len(summary["errors"]) == 5
        for i in range(5):
            assert any(f"Error {i}" in err["message"] for err in summary["errors"])


class TestErrorHandlingOrchestratorProperties:
    """Property-based tests for ErrorHandlingOrchestrator."""

    @given(error_message=st.text(min_size=1, max_size=100))
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_error_handling_graceful_degradation(self, mocker, error_message):
        """
        **Feature: flow-orchestrator-refactoring, Property 4: Error Handling Graceful Degradation**

        For any crew execution error, the ErrorHandlingOrchestrator should handle it
        without raising unhandled exceptions.

        Validates: Requirements 2.1
        """
        # Arrange
        state = FinwizState()
        orchestrator = ErrorHandlingOrchestrator(state)
        mock_crew = mocker.Mock(side_effect=Exception(error_message))

        # Act - should not raise exception
        result = orchestrator.execute_crew_with_error_handling(mock_crew, "test_crew")

        # Assert
        assert result is not None
        assert isinstance(result, dict)
        assert "success" in result
        assert "error" in result
        assert result["success"] is False
        assert result["error"] is not None

    @given(
        errors=st.lists(
            st.sampled_from(
                [
                    ValueError("Validation error"),
                    TimeoutError("Timeout"),
                    ConnectionError("Connection failed"),
                    Exception("Generic error"),
                ]
            ),
            min_size=1,
            max_size=20,
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_property_error_aggregation_completeness(self, errors):
        """
        **Feature: flow-orchestrator-refactoring, Property 5: Error Aggregation Completeness**

        For any set of multiple errors, the ErrorHandlingOrchestrator should include
        all errors in the aggregated summary.

        Validates: Requirements 2.2
        """
        # Arrange
        state = FinwizState()
        orchestrator = ErrorHandlingOrchestrator(state)

        # Act
        summary = orchestrator.generate_error_summary(errors)

        # Assert - all errors must be included
        assert summary["total_errors"] == len(errors)
        assert len(summary["errors"]) == len(errors)

        # Verify each error is represented
        error_messages = [str(e) for e in errors]
        summary_messages = [err["message"] for err in summary["errors"]]

        for error_msg in error_messages:
            assert error_msg in summary_messages

    @given(
        errors=st.lists(
            st.sampled_from(
                [
                    ValueError("Validation error"),
                    TimeoutError("Timeout"),
                    ConnectionError("Connection failed"),
                ]
            ),
            min_size=1,
            max_size=10,
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_property_error_summary_contains_required_fields(self, errors):
        """
        Test that error summary always contains required fields.

        Validates: Requirements 2.3 (Error Information Actionability)
        """
        # Arrange
        state = FinwizState()
        orchestrator = ErrorHandlingOrchestrator(state)

        # Act
        summary = orchestrator.generate_error_summary(errors)

        # Assert - required fields must be present
        assert "total_errors" in summary
        assert "error_types" in summary
        assert "retryable_count" in summary
        assert "non_retryable_count" in summary
        assert "errors" in summary
        assert "timestamp" in summary

        # Each error must have required fields
        for error in summary["errors"]:
            assert "message" in error
            assert "type" in error
            assert "retryable" in error
            assert "context" in error

    @given(
        crew_result=st.one_of(
            st.dictionaries(st.text(min_size=1, max_size=10), st.integers()),
            st.lists(st.integers()),
            st.text(),
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
        )
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_successful_result_pass_through(self, mocker, crew_result):
        """
        **Feature: flow-orchestrator-refactoring, Property 7: Successful Result Pass-Through**

        For any successful crew execution, the ErrorHandlingOrchestrator should return
        the result unmodified.

        Validates: Requirements 2.4
        """
        # Arrange
        state = FinwizState()
        orchestrator = ErrorHandlingOrchestrator(state)
        mock_crew = mocker.Mock(return_value=crew_result)

        # Act
        result = orchestrator.execute_crew_with_error_handling(mock_crew, "test_crew")

        # Assert
        assert result["success"] is True
        assert result["data"] == crew_result
        assert result["error"] is None
