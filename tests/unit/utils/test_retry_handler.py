"""
Unit tests for retry logic with exponential backoff.

Tests error classification, ValidationError creation, remediation suggestions,
and retry decorator configuration.
"""

import pytest

from finwiz.config.resilience_config import ResilienceConfig
from finwiz.infrastructure.resilience.retry import (
    RETRYABLE_EXCEPTIONS,
    classify_error,
    create_retry_decorator,
    create_validation_error_from_exception,
    get_remediation_suggestion,
)
from finwiz.validation.result import ValidationError


class TestClassifyError:
    """Test cases for error classification."""

    def test_should_classify_connection_error_as_retryable(self):
        """Test that ConnectionError is classified as retryable network error."""
        # Arrange
        error = ConnectionError("Network unreachable")

        # Act
        error_type, is_retryable = classify_error(error)

        # Assert
        assert error_type == "network"
        assert is_retryable is True

    def test_should_classify_timeout_error_as_retryable(self):
        """Test that TimeoutError is classified as retryable timeout error."""
        # Arrange
        error = TimeoutError("Operation timed out")

        # Act
        error_type, is_retryable = classify_error(error)

        # Assert
        assert error_type == "timeout"
        assert is_retryable is True

    def test_should_classify_rate_limit_error_as_retryable(self):
        """Test that rate limit errors are classified as retryable."""
        # Arrange
        error = Exception("Rate limit exceeded")

        # Act
        error_type, is_retryable = classify_error(error)

        # Assert
        assert error_type == "rate_limit"
        assert is_retryable is True

    def test_should_classify_too_many_requests_as_retryable(self):
        """Test that 'too many requests' errors are classified as retryable."""
        # Arrange
        error = Exception("429 Too Many Requests")

        # Act
        error_type, is_retryable = classify_error(error)

        # Assert
        assert error_type == "rate_limit"
        assert is_retryable is True

    def test_should_classify_authentication_error_as_non_retryable(self):
        """Test that authentication errors are classified as non-retryable."""
        # Arrange
        error = Exception("Authentication failed")

        # Act
        error_type, is_retryable = classify_error(error)

        # Assert
        assert error_type == "authentication"
        assert is_retryable is False

    def test_should_classify_unauthorized_error_as_non_retryable(self):
        """Test that unauthorized errors are classified as non-retryable."""
        # Arrange
        error = Exception("401 Unauthorized")

        # Act
        error_type, is_retryable = classify_error(error)

        # Assert
        assert error_type == "authentication"
        assert is_retryable is False

    def test_should_classify_api_key_error_as_non_retryable(self):
        """Test that API key errors are classified as non-retryable."""
        # Arrange
        error = Exception("Invalid API key")

        # Act
        error_type, is_retryable = classify_error(error)

        # Assert
        assert error_type == "authentication"
        assert is_retryable is False

    def test_should_classify_validation_error_as_non_retryable(self):
        """Test that validation errors are classified as non-retryable."""
        # Arrange
        error = Exception("Validation failed: invalid ticker")

        # Act
        error_type, is_retryable = classify_error(error)

        # Assert
        assert error_type == "validation"
        assert is_retryable is False

    def test_should_classify_invalid_error_as_non_retryable(self):
        """Test that 'invalid' errors are classified as non-retryable."""
        # Arrange
        error = Exception("Invalid input format")

        # Act
        error_type, is_retryable = classify_error(error)

        # Assert
        assert error_type == "validation"
        assert is_retryable is False

    def test_should_classify_unknown_error_as_non_retryable(self):
        """Test that unknown errors are classified as non-retryable."""
        # Arrange
        error = Exception("Something went wrong")

        # Act
        error_type, is_retryable = classify_error(error)

        # Assert
        assert error_type == "unknown"
        assert is_retryable is False


class TestCreateValidationErrorFromException:
    """Test cases for ValidationError creation from exceptions."""

    def test_should_create_validation_error_with_network_error(self):
        """Test ValidationError creation from network error."""
        # Arrange
        error = ConnectionError("Network unreachable")
        ticker = "AAPL"
        attempt = 2

        # Act
        validation_error = create_validation_error_from_exception(error, ticker, attempt)

        # Assert
        assert isinstance(validation_error, ValidationError)
        assert validation_error.field_path == "holding.AAPL"
        assert validation_error.error_type == "network"
        assert validation_error.message == "Network unreachable"
        assert validation_error.input_value == "AAPL"
        assert validation_error.context["ticker"] == "AAPL"
        assert validation_error.context["attempt"] == 2
        assert validation_error.context["is_retryable"] is True
        assert "timestamp" in validation_error.context
        assert "remediation" in validation_error.context

    def test_should_create_validation_error_with_timeout_error(self):
        """Test ValidationError creation from timeout error."""
        # Arrange
        error = TimeoutError("Operation timed out after 300s")
        ticker = "TSLA"
        attempt = 1

        # Act
        validation_error = create_validation_error_from_exception(error, ticker, attempt)

        # Assert
        assert validation_error.field_path == "holding.TSLA"
        assert validation_error.error_type == "timeout"
        assert validation_error.message == "Operation timed out after 300s"
        assert validation_error.context["is_retryable"] is True

    def test_should_create_validation_error_with_authentication_error(self):
        """Test ValidationError creation from authentication error."""
        # Arrange
        error = Exception("Invalid API key")
        ticker = "MSFT"
        attempt = 1

        # Act
        validation_error = create_validation_error_from_exception(error, ticker, attempt)

        # Assert
        assert validation_error.field_path == "holding.MSFT"
        assert validation_error.error_type == "authentication"
        assert validation_error.context["is_retryable"] is False

    def test_should_include_remediation_in_context(self):
        """Test that remediation suggestion is included in context."""
        # Arrange
        error = ConnectionError("Network error")
        ticker = "GOOGL"
        attempt = 1

        # Act
        validation_error = create_validation_error_from_exception(error, ticker, attempt)

        # Assert
        assert "remediation" in validation_error.context
        assert "connectivity" in validation_error.context["remediation"].lower()

    def test_should_include_timestamp_in_context(self):
        """Test that timestamp is included in context."""
        # Arrange
        error = TimeoutError("Timeout")
        ticker = "AMZN"
        attempt = 3

        # Act
        validation_error = create_validation_error_from_exception(error, ticker, attempt)

        # Assert
        assert "timestamp" in validation_error.context
        # Timestamp should be in ISO format
        assert "T" in validation_error.context["timestamp"]


class TestGetRemediationSuggestion:
    """Test cases for remediation suggestions."""

    def test_should_provide_network_remediation(self):
        """Test remediation suggestion for network errors."""
        # Act
        suggestion = get_remediation_suggestion("network")

        # Assert
        assert "connectivity" in suggestion.lower()
        assert "api status" in suggestion.lower()

    def test_should_provide_rate_limit_remediation(self):
        """Test remediation suggestion for rate limit errors."""
        # Act
        suggestion = get_remediation_suggestion("rate_limit")

        # Assert
        assert "parallelism" in suggestion.lower() or "delay" in suggestion.lower()

    def test_should_provide_timeout_remediation(self):
        """Test remediation suggestion for timeout errors."""
        # Act
        suggestion = get_remediation_suggestion("timeout")

        # Assert
        assert "timeout" in suggestion.lower()

    def test_should_provide_authentication_remediation(self):
        """Test remediation suggestion for authentication errors."""
        # Act
        suggestion = get_remediation_suggestion("authentication")

        # Assert
        assert "api key" in suggestion.lower()

    def test_should_provide_validation_remediation(self):
        """Test remediation suggestion for validation errors."""
        # Act
        suggestion = get_remediation_suggestion("validation")

        # Assert
        assert "ticker" in suggestion.lower() or "data" in suggestion.lower()

    def test_should_provide_unknown_remediation(self):
        """Test remediation suggestion for unknown errors."""
        # Act
        suggestion = get_remediation_suggestion("unknown")

        # Assert
        assert "review" in suggestion.lower() or "log" in suggestion.lower()

    def test_should_provide_default_for_unrecognized_type(self):
        """Test that unrecognized error types get default remediation."""
        # Act
        suggestion = get_remediation_suggestion("unrecognized_type")

        # Assert
        assert "review" in suggestion.lower() or "log" in suggestion.lower()


class TestCreateRetryDecorator:
    """Test cases for retry decorator creation."""

    def test_should_create_decorator_with_default_config(self):
        """Test retry decorator creation with default configuration."""
        # Act
        decorator = create_retry_decorator()

        # Assert
        assert decorator is not None
        # Decorator should be callable
        assert callable(decorator)

    def test_should_create_decorator_with_custom_config(self):
        """Test retry decorator creation with custom configuration."""
        # Arrange
        config = ResilienceConfig(
            max_retries=5,
            retry_base_delay=1.0,
            retry_max_delay=30.0,
            holding_timeout=300,
            flow_timeout=7200,
            auto_resume=False,
            state_max_age_hours=24,
            parallel_limit=10,
            deep_analysis_parallel_limit=3,
            cleanup_state_on_success=False,
            state_cleanup_max_age_days=7,
        )

        # Act
        decorator = create_retry_decorator(config)

        # Assert
        assert decorator is not None
        assert callable(decorator)

    def test_should_configure_retryable_exceptions(self):
        """Test that RETRYABLE_EXCEPTIONS tuple is properly defined."""
        # Assert
        assert ConnectionError in RETRYABLE_EXCEPTIONS
        assert TimeoutError in RETRYABLE_EXCEPTIONS
        assert len(RETRYABLE_EXCEPTIONS) == 2

    @pytest.mark.asyncio
    async def test_should_retry_on_connection_error(self, mocker):
        """Test that decorator retries on ConnectionError."""
        # Arrange
        config = ResilienceConfig(
            max_retries=3,
            retry_base_delay=0.01,  # Fast for testing
            retry_max_delay=0.1,
            holding_timeout=300,
            flow_timeout=7200,
            auto_resume=False,
            state_max_age_hours=24,
            parallel_limit=10,
            deep_analysis_parallel_limit=3,
            cleanup_state_on_success=False,
            state_cleanup_max_age_days=7,
        )
        decorator = create_retry_decorator(config)

        call_count = 0

        @decorator
        async def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Network error")
            return "success"

        # Act
        result = await failing_function()

        # Assert
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_should_not_retry_on_non_retryable_error(self, mocker):
        """Test that decorator does not retry on non-retryable errors."""
        # Arrange
        config = ResilienceConfig(
            max_retries=3,
            retry_base_delay=0.01,
            retry_max_delay=0.1,
            holding_timeout=300,
            flow_timeout=7200,
            auto_resume=False,
            state_max_age_hours=24,
            parallel_limit=10,
            deep_analysis_parallel_limit=3,
            cleanup_state_on_success=False,
            state_cleanup_max_age_days=7,
        )
        decorator = create_retry_decorator(config)

        call_count = 0

        @decorator
        async def failing_function():
            nonlocal call_count
            call_count += 1
            raise ValueError("Invalid input")

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid input"):
            await failing_function()

        # Should only be called once (no retries)
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_should_exhaust_retries_and_reraise(self, mocker):
        """Test that decorator exhausts retries and reraises exception."""
        # Arrange
        config = ResilienceConfig(
            max_retries=2,
            retry_base_delay=0.01,
            retry_max_delay=0.1,
            holding_timeout=300,
            flow_timeout=7200,
            auto_resume=False,
            state_max_age_hours=24,
            parallel_limit=10,
            deep_analysis_parallel_limit=3,
            cleanup_state_on_success=False,
            state_cleanup_max_age_days=7,
        )
        decorator = create_retry_decorator(config)

        call_count = 0

        @decorator
        async def always_failing_function():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Persistent network error")

        # Act & Assert
        with pytest.raises(ConnectionError, match="Persistent network error"):
            await always_failing_function()

        # Should be called max_retries times
        assert call_count == 2


class TestRetryHandlerIntegration:
    """Integration tests for retry handler components."""

    @pytest.mark.asyncio
    async def test_should_handle_complete_retry_flow(self, mocker):
        """Test complete flow: error classification, retry, and ValidationError creation."""
        # Arrange
        config = ResilienceConfig(
            max_retries=3,
            retry_base_delay=0.01,
            retry_max_delay=0.1,
            holding_timeout=300,
            flow_timeout=7200,
            auto_resume=False,
            state_max_age_hours=24,
            parallel_limit=10,
            deep_analysis_parallel_limit=3,
            cleanup_state_on_success=False,
            state_cleanup_max_age_days=7,
        )
        decorator = create_retry_decorator(config)

        call_count = 0
        ticker = "AAPL"

        @decorator
        async def analyze_holding():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Network unreachable")
            return {"ticker": ticker, "grade": "A+"}

        # Act
        try:
            result = await analyze_holding()
            validation_error = None
        except Exception as e:
            result = None
            validation_error = create_validation_error_from_exception(e, ticker, call_count)

        # Assert
        assert result is not None
        assert result["ticker"] == ticker
        assert call_count == 2
        assert validation_error is None  # No error because it succeeded

    def test_should_provide_consistent_error_classification(self):
        """Test that error classification is consistent across multiple calls."""
        # Arrange
        errors = [
            ConnectionError("Network error"),
            TimeoutError("Timeout"),
            Exception("Rate limit exceeded"),
            Exception("Authentication failed"),
        ]

        # Act & Assert
        for error in errors:
            error_type1, is_retryable1 = classify_error(error)
            error_type2, is_retryable2 = classify_error(error)

            assert error_type1 == error_type2
            assert is_retryable1 == is_retryable2
