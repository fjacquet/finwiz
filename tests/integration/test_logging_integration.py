"""
Integration tests for CrewLogger logging functionality.

This module verifies that structured logging is properly integrated
across all crews and that log entries contain the expected fields.
"""

import logging
import time

import pytest

from finwiz.crews.crypto_crew.crypto_crew import CryptoCrew
from finwiz.crews.etf_crew.etf_crew import EtfCrew
from finwiz.crews.report_crew.report_crew import ReportCrew
from finwiz.crews.stock_crew.stock_crew import StockCrew


class LogCapture:
    """Helper class to capture log records with extra fields."""

    def __init__(self) -> None:
        """Initialize the log record handler."""
        self.records = []

    def __call__(self, record):
        """Capture log record."""
        self.records.append(record)
        return True


@pytest.mark.integration
class TestLoggingIntegration:
    """Test suite for verifying logging integration across crews."""

    def test_should_log_start_event_when_stock_crew_kickoff_called(self, mocker):
        """Verify StockCrew logs start event with correct structured fields."""
        # Arrange
        log_capture = LogCapture()

        # Mock the crew kickoff to avoid actual execution
        mock_crew_instance = mocker.MagicMock()
        mock_crew_instance.kickoff.return_value = "test_result"
        mocker.patch.object(StockCrew, "crew", return_value=mock_crew_instance)

        # Capture logs
        logger = logging.getLogger("finwiz.crews.StockCrew")
        logger.addFilter(log_capture)
        logger.setLevel(logging.INFO)

        crew = StockCrew()
        inputs = {"ticker": "AAPL"}

        # Act
        crew.kickoff(inputs)

        # Assert
        start_logs = [r for r in log_capture.records if hasattr(r, "event") and r.event == "crew_start"]
        assert len(start_logs) > 0, "No crew_start event logged"

        start_log = start_logs[0]
        assert hasattr(start_log, "crew"), "Log missing 'crew' field"
        assert start_log.crew == "StockCrew", f"Expected crew='StockCrew', got '{start_log.crew}'"
        assert hasattr(start_log, "input_keys"), "Log missing 'input_keys' field"
        assert "ticker" in start_log.input_keys, "Log missing 'ticker' in input_keys"
        assert hasattr(start_log, "event"), "Log missing 'event' field"
        assert start_log.event == "crew_start", f"Expected event='crew_start', got '{start_log.event}'"

    def test_should_log_complete_event_when_crypto_crew_succeeds(self, mocker):
        """Verify CryptoCrew logs completion event with duration."""
        # Arrange
        log_capture = LogCapture()

        # Mock the crew kickoff
        mock_crew_instance = mocker.MagicMock()
        mock_crew_instance.kickoff.return_value = "test_result"
        mocker.patch.object(CryptoCrew, "crew", return_value=mock_crew_instance)

        # Capture logs
        logger = logging.getLogger("finwiz.crews.CryptoCrew")
        logger.addFilter(log_capture)
        logger.setLevel(logging.INFO)

        crew = CryptoCrew()
        inputs = {"crypto": "BTC"}

        # Act
        crew.kickoff(inputs)

        # Assert
        complete_logs = [r for r in log_capture.records if hasattr(r, "event") and r.event == "crew_complete"]
        assert len(complete_logs) > 0, "No crew_complete event logged"

        complete_log = complete_logs[0]
        assert hasattr(complete_log, "crew"), "Log missing 'crew' field"
        assert complete_log.crew == "CryptoCrew", f"Expected crew='CryptoCrew', got '{complete_log.crew}'"
        assert hasattr(complete_log, "duration"), "Log missing 'duration' field"
        assert isinstance(complete_log.duration, float), "Duration should be a float"
        assert complete_log.duration >= 0, "Duration should be non-negative"
        assert hasattr(complete_log, "event"), "Log missing 'event' field"
        assert complete_log.event == "crew_complete", f"Expected event='crew_complete', got '{complete_log.event}'"

    def test_should_log_error_event_when_etf_crew_fails(self, mocker):
        """Verify EtfCrew logs error event with exception details."""
        # Arrange
        log_capture = LogCapture()

        # Mock the crew kickoff to raise an exception
        mock_crew_instance = mocker.MagicMock()
        test_error = ValueError("Test error")
        mock_crew_instance.kickoff.side_effect = test_error
        mocker.patch.object(EtfCrew, "crew", return_value=mock_crew_instance)

        # Capture logs
        logger = logging.getLogger("finwiz.crews.EtfCrew")
        logger.addFilter(log_capture)
        logger.setLevel(logging.ERROR)

        crew = EtfCrew()
        inputs = {"etf": "SPY"}

        # Act & Assert
        with pytest.raises(ValueError, match="Test error"):
            crew.kickoff(inputs)

        # Assert error logging
        error_logs = [r for r in log_capture.records if hasattr(r, "event") and r.event == "crew_error"]
        assert len(error_logs) > 0, "No crew_error event logged"

        error_log = error_logs[0]
        assert hasattr(error_log, "crew"), "Log missing 'crew' field"
        assert error_log.crew == "EtfCrew", f"Expected crew='EtfCrew', got '{error_log.crew}'"
        assert hasattr(error_log, "error_type"), "Log missing 'error_type' field"
        assert error_log.error_type == "ValueError", f"Expected error_type='ValueError', got '{error_log.error_type}'"
        assert hasattr(error_log, "event"), "Log missing 'event' field"
        assert error_log.event == "crew_error", f"Expected event='crew_error', got '{error_log.event}'"
        assert error_log.exc_info is not None, "Log missing exception info"

    def test_should_log_all_events_when_report_crew_executes(self, mocker):
        """Verify ReportCrew logs start and complete events in sequence."""
        # Arrange
        log_capture = LogCapture()

        # Mock the crew kickoff
        mock_crew_instance = mocker.MagicMock()
        mock_crew_instance.kickoff.return_value = "test_result"
        mocker.patch.object(ReportCrew, "crew", return_value=mock_crew_instance)

        # Capture logs
        logger = logging.getLogger("finwiz.crews.ReportCrew")
        logger.addFilter(log_capture)
        logger.setLevel(logging.INFO)

        crew = ReportCrew()
        inputs = {"budget": 1000}

        # Act
        crew.kickoff(inputs)

        # Assert start event
        start_logs = [r for r in log_capture.records if hasattr(r, "event") and r.event == "crew_start"]
        assert len(start_logs) > 0, "No crew_start event logged"

        # Assert complete event
        complete_logs = [r for r in log_capture.records if hasattr(r, "event") and r.event == "crew_complete"]
        assert len(complete_logs) > 0, "No crew_complete event logged"

        # Verify event order (start should come before complete)
        start_idx = log_capture.records.index(start_logs[0])
        complete_idx = log_capture.records.index(complete_logs[0])
        assert start_idx < complete_idx, "crew_start should be logged before crew_complete"

    def test_should_include_empty_input_keys_when_no_inputs_provided(self, mocker):
        """Verify logging handles None/empty inputs correctly."""
        # Arrange
        log_capture = LogCapture()

        # Mock the crew kickoff
        mock_crew_instance = mocker.MagicMock()
        mock_crew_instance.kickoff.return_value = "test_result"
        mocker.patch.object(StockCrew, "crew", return_value=mock_crew_instance)

        # Capture logs
        logger = logging.getLogger("finwiz.crews.StockCrew")
        logger.addFilter(log_capture)
        logger.setLevel(logging.INFO)

        crew = StockCrew()

        # Act - call with None inputs
        crew.kickoff(None)

        # Assert
        start_logs = [r for r in log_capture.records if hasattr(r, "event") and r.event == "crew_start"]
        assert len(start_logs) > 0, "No crew_start event logged"

        start_log = start_logs[0]
        assert hasattr(start_log, "input_keys"), "Log missing 'input_keys' field"
        assert start_log.input_keys == [], "Expected empty input_keys for None inputs"

    def test_should_measure_duration_accurately_when_crew_executes(self, mocker):
        """Verify duration measurement is accurate."""
        # Arrange
        log_capture = LogCapture()

        # Mock the crew kickoff with a delay
        mock_crew_instance = mocker.MagicMock()

        def delayed_kickoff(*args, **kwargs):
            time.sleep(0.1)  # 100ms delay
            return "test_result"

        mock_crew_instance.kickoff.side_effect = delayed_kickoff
        mocker.patch.object(CryptoCrew, "crew", return_value=mock_crew_instance)

        # Capture logs
        logger = logging.getLogger("finwiz.crews.CryptoCrew")
        logger.addFilter(log_capture)
        logger.setLevel(logging.INFO)

        crew = CryptoCrew()

        # Act
        crew.kickoff({"crypto": "ETH"})

        # Assert
        complete_logs = [r for r in log_capture.records if hasattr(r, "event") and r.event == "crew_complete"]
        assert len(complete_logs) > 0, "No crew_complete event logged"

        complete_log = complete_logs[0]
        assert hasattr(complete_log, "duration"), "Log missing 'duration' field"
        # Duration should be at least 0.1 seconds (100ms)
        assert complete_log.duration >= 0.1, f"Expected duration >= 0.1s, got {complete_log.duration}s"
        # Duration should be reasonable (less than 1 second for this test)
        assert complete_log.duration < 1.0, f"Duration too long: {complete_log.duration}s"
