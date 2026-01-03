"""
Unit tests for logging helpers.

Tests the CrewLogger class to ensure it correctly logs crew execution
events with structured fields for start, completion, and error scenarios.
"""

from pytest import approx

from finwiz.infrastructure.logging.helpers import CrewLogger


class TestCrewLogger:
    """Test suite for CrewLogger class."""

    def test_should_initialize_with_crew_name(self, mocker):
        """Test CrewLogger initialization with crew name."""
        # Arrange
        mock_get_logger = mocker.patch("finwiz.infrastructure.logging.helpers.get_logger")
        mock_logger = mocker.Mock()
        mock_get_logger.return_value = mock_logger

        # Act
        crew_logger = CrewLogger("TestCrew")

        # Assert
        assert crew_logger.crew_name == "TestCrew"
        assert crew_logger.logger == mock_logger
        mock_get_logger.assert_called_once_with("finwiz.crews.TestCrew")

    def test_should_log_start_with_structured_fields(self, mocker):
        """Test log_start includes correct structured fields (crew, input_keys, event)."""
        # Arrange
        mock_get_logger = mocker.patch("finwiz.infrastructure.logging.helpers.get_logger")
        mock_logger = mocker.Mock()
        mock_get_logger.return_value = mock_logger

        crew_logger = CrewLogger("StockCrew")
        inputs = {"ticker": "AAPL", "analysis_type": "fundamental"}

        # Act
        crew_logger.log_start(inputs)

        # Assert
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args

        # Verify log message
        assert "Starting StockCrew execution" in call_args[0][0]

        # Verify structured extra fields
        extra = call_args[1]["extra"]
        assert extra["crew"] == "StockCrew"
        assert extra["input_keys"] == ["ticker", "analysis_type"]
        assert extra["event"] == "crew_start"

    def test_should_log_start_with_empty_inputs(self, mocker):
        """Test log_start handles empty inputs correctly."""
        # Arrange
        mock_get_logger = mocker.patch("finwiz.infrastructure.logging.helpers.get_logger")
        mock_logger = mocker.Mock()
        mock_get_logger.return_value = mock_logger

        crew_logger = CrewLogger("CryptoCrew")

        # Act
        crew_logger.log_start({})

        # Assert
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args

        # Verify empty input_keys
        extra = call_args[1]["extra"]
        assert extra["input_keys"] == []
        assert extra["event"] == "crew_start"

    def test_should_log_start_with_none_inputs(self, mocker):
        """Test log_start handles None inputs correctly."""
        # Arrange
        mock_get_logger = mocker.patch("finwiz.infrastructure.logging.helpers.get_logger")
        mock_logger = mocker.Mock()
        mock_get_logger.return_value = mock_logger

        crew_logger = CrewLogger("ETFCrew")

        # Act
        crew_logger.log_start(None)

        # Assert
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args

        # Verify empty input_keys for None
        extra = call_args[1]["extra"]
        assert extra["input_keys"] == []
        assert extra["event"] == "crew_start"

    def test_should_log_complete_with_duration_and_event(self, mocker):
        """Test log_complete includes duration and event type."""
        # Arrange
        mock_get_logger = mocker.patch("finwiz.infrastructure.logging.helpers.get_logger")
        mock_logger = mocker.Mock()
        mock_get_logger.return_value = mock_logger

        crew_logger = CrewLogger("ReportCrew")
        duration = 45.67

        # Act
        crew_logger.log_complete(duration)

        # Assert
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args

        # Verify log message includes formatted duration
        assert "ReportCrew execution completed in 45.67s" in call_args[0][0]

        # Verify structured extra fields
        extra = call_args[1]["extra"]
        assert extra["crew"] == "ReportCrew"
        assert extra["duration"] == approx(45.67)
        assert extra["event"] == "crew_complete"

    def test_should_log_complete_with_short_duration(self, mocker):
        """Test log_complete formats short durations correctly."""
        # Arrange
        mock_get_logger = mocker.patch("finwiz.infrastructure.logging.helpers.get_logger")
        mock_logger = mocker.Mock()
        mock_get_logger.return_value = mock_logger

        crew_logger = CrewLogger("QuickCrew")
        duration = 0.123

        # Act
        crew_logger.log_complete(duration)

        # Assert
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args

        # Verify duration is formatted to 2 decimal places
        assert "0.12s" in call_args[0][0]

        # Verify exact duration value in extra fields
        extra = call_args[1]["extra"]
        assert extra["duration"] == approx(0.123)

    def test_should_log_error_with_exception_info(self, mocker):
        """Test log_error includes error type and exception info."""
        # Arrange
        mock_get_logger = mocker.patch("finwiz.infrastructure.logging.helpers.get_logger")
        mock_logger = mocker.Mock()
        mock_get_logger.return_value = mock_logger

        crew_logger = CrewLogger("FailingCrew")
        error = ValueError("Invalid ticker symbol")

        # Act
        crew_logger.log_error(error)

        # Assert
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args

        # Verify log message includes error type
        assert "FailingCrew execution failed: ValueError" in call_args[0][0]

        # Verify structured extra fields
        extra = call_args[1]["extra"]
        assert extra["crew"] == "FailingCrew"
        assert extra["error_type"] == "ValueError"
        assert extra["event"] == "crew_error"

        # Verify exc_info is True for full exception traceback
        assert call_args[1]["exc_info"] is True

    def test_should_log_error_with_custom_exception(self, mocker):
        """Test log_error handles custom exception types."""
        # Arrange
        mock_get_logger = mocker.patch("finwiz.infrastructure.logging.helpers.get_logger")
        mock_logger = mocker.Mock()
        mock_get_logger.return_value = mock_logger

        # Define custom exception
        class CustomFinWizError(Exception):
            """Custom FinWiz exception."""

            pass

        crew_logger = CrewLogger("CustomCrew")
        error = CustomFinWizError("Custom error occurred")

        # Act
        crew_logger.log_error(error)

        # Assert
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args

        # Verify custom exception type is captured
        assert "CustomFinWizError" in call_args[0][0]

        extra = call_args[1]["extra"]
        assert extra["error_type"] == "CustomFinWizError"
        assert extra["event"] == "crew_error"

    def test_should_log_error_with_runtime_error(self, mocker):
        """Test log_error handles RuntimeError correctly."""
        # Arrange
        mock_get_logger = mocker.patch("finwiz.infrastructure.logging.helpers.get_logger")
        mock_logger = mocker.Mock()
        mock_get_logger.return_value = mock_logger

        crew_logger = CrewLogger("RuntimeCrew")
        error = RuntimeError("Unexpected runtime error")

        # Act
        crew_logger.log_error(error)

        # Assert
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args

        # Verify RuntimeError is captured
        assert "RuntimeError" in call_args[0][0]

        extra = call_args[1]["extra"]
        assert extra["error_type"] == "RuntimeError"

    def test_should_use_correct_logger_name_format(self, mocker):
        """Test CrewLogger uses correct logger name format."""
        # Arrange
        mock_get_logger = mocker.patch("finwiz.infrastructure.logging.helpers.get_logger")

        # Act
        CrewLogger("InvestmentDiscoveryCrew")

        # Assert
        mock_get_logger.assert_called_once_with("finwiz.crews.InvestmentDiscoveryCrew")

    def test_should_handle_multiple_log_calls(self, mocker):
        """Test CrewLogger handles multiple sequential log calls."""
        # Arrange
        mock_get_logger = mocker.patch("finwiz.infrastructure.logging.helpers.get_logger")
        mock_logger = mocker.Mock()
        mock_get_logger.return_value = mock_logger

        crew_logger = CrewLogger("MultiLogCrew")

        # Act
        crew_logger.log_start({"ticker": "TSLA"})
        crew_logger.log_complete(30.5)

        # Assert
        assert mock_logger.info.call_count == 2

        # Verify first call (log_start)
        first_call = mock_logger.info.call_args_list[0]
        assert "Starting MultiLogCrew execution" in first_call[0][0]
        assert first_call[1]["extra"]["event"] == "crew_start"

        # Verify second call (log_complete)
        second_call = mock_logger.info.call_args_list[1]
        assert "MultiLogCrew execution completed" in second_call[0][0]
        assert second_call[1]["extra"]["event"] == "crew_complete"

    def test_should_preserve_input_keys_order(self, mocker):
        """Test log_start preserves input keys in list format."""
        # Arrange
        mock_get_logger = mocker.patch("finwiz.infrastructure.logging.helpers.get_logger")
        mock_logger = mocker.Mock()
        mock_get_logger.return_value = mock_logger

        crew_logger = CrewLogger("OrderCrew")
        inputs = {"ticker": "AAPL", "timeframe": "1Y", "analysis": "full"}

        # Act
        crew_logger.log_start(inputs)

        # Assert
        call_args = mock_logger.info.call_args
        extra = call_args[1]["extra"]

        # Verify input_keys is a list containing all keys
        assert isinstance(extra["input_keys"], list)
        assert len(extra["input_keys"]) == 3
        assert "ticker" in extra["input_keys"]
        assert "timeframe" in extra["input_keys"]
        assert "analysis" in extra["input_keys"]

    def test_should_log_with_different_crew_names(self, mocker):
        """Test CrewLogger works correctly with different crew names."""
        # Arrange
        mock_get_logger = mocker.patch("finwiz.infrastructure.logging.helpers.get_logger")
        mock_logger = mocker.Mock()
        mock_get_logger.return_value = mock_logger

        # Act & Assert for StockCrew
        stock_logger = CrewLogger("StockCrew")
        stock_logger.log_start({"ticker": "AAPL"})

        call_args = mock_logger.info.call_args
        assert call_args[1]["extra"]["crew"] == "StockCrew"
        assert "StockCrew" in call_args[0][0]

        # Reset mock
        mock_logger.reset_mock()

        # Act & Assert for CryptoCrew
        crypto_logger = CrewLogger("CryptoCrew")
        crypto_logger.log_start({"symbol": "BTC"})

        call_args = mock_logger.info.call_args
        assert call_args[1]["extra"]["crew"] == "CryptoCrew"
        assert "CryptoCrew" in call_args[0][0]

    def test_should_include_exc_info_in_error_logging(self, mocker):
        """Test log_error includes exc_info for full traceback."""
        # Arrange
        mock_get_logger = mocker.patch("finwiz.infrastructure.logging.helpers.get_logger")
        mock_logger = mocker.Mock()
        mock_get_logger.return_value = mock_logger

        crew_logger = CrewLogger("TraceCrew")
        error = Exception("Test exception with traceback")

        # Act
        crew_logger.log_error(error)

        # Assert
        call_args = mock_logger.error.call_args

        # Verify exc_info=True is passed for full exception traceback
        assert "exc_info" in call_args[1]
        assert call_args[1]["exc_info"] is True

    def test_should_format_duration_consistently(self, mocker):
        """Test log_complete formats duration to 2 decimal places consistently."""
        # Arrange
        mock_get_logger = mocker.patch("finwiz.infrastructure.logging.helpers.get_logger")
        mock_logger = mocker.Mock()
        mock_get_logger.return_value = mock_logger

        crew_logger = CrewLogger("DurationCrew")

        # Test various duration values
        test_cases = [
            (1.0, "1.00s"),
            (10.5, "10.50s"),
            (100.123, "100.12s"),
            (0.001, "0.00s"),
            (999.999, "1000.00s"),
        ]

        for duration, expected_format in test_cases:
            # Act
            mock_logger.reset_mock()
            crew_logger.log_complete(duration)

            # Assert
            call_args = mock_logger.info.call_args
            assert expected_format in call_args[0][0]
