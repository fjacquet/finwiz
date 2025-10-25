"""
Unit tests for timeout management utilities.

Tests timeout enforcement, graceful fallback, successful execution,
and logging of timeout events.
"""

import asyncio

import pytest

from finwiz.utils.timeout_handler import with_timeout, with_timeout_graceful


class TestWithTimeout:
    """Test cases for strict timeout enforcement."""

    @pytest.mark.asyncio
    async def test_should_complete_within_timeout(self, mocker):
        """Test that function completes successfully within timeout."""
        # Arrange
        async def fast_operation(value: str) -> str:
            await asyncio.sleep(0.01)
            return f"Result: {value}"

        # Act
        result = await with_timeout(
            fast_operation,
            timeout_seconds=1,
            operation_name="Fast operation",
            value="test"
        )

        # Assert
        assert result == "Result: test"

    @pytest.mark.asyncio
    async def test_should_raise_timeout_error_when_exceeded(self, mocker):
        """Test that TimeoutError is raised when timeout is exceeded."""
        # Arrange
        async def slow_operation() -> str:
            await asyncio.sleep(2)
            return "Should not reach here"

        # Act & Assert
        with pytest.raises(TimeoutError):
            await with_timeout(
                slow_operation,
                timeout_seconds=0.1,
                operation_name="Slow operation"
            )

    @pytest.mark.asyncio
    async def test_should_pass_kwargs_to_coroutine(self, mocker):
        """Test that keyword arguments are passed to the coroutine."""
        # Arrange
        async def operation_with_args(ticker: str, price: float) -> dict:
            await asyncio.sleep(0.01)
            return {"ticker": ticker, "price": price}

        # Act
        result = await with_timeout(
            operation_with_args,
            timeout_seconds=1,
            operation_name="Operation with args",
            ticker="AAPL",
            price=150.0
        )

        # Assert
        assert result["ticker"] == "AAPL"
        assert result["price"] == 150.0

    @pytest.mark.asyncio
    async def test_should_log_start_and_completion(self, mocker):
        """Test that start and completion are logged."""
        # Arrange
        mock_logger = mocker.patch('finwiz.utils.timeout_handler.logger')

        async def simple_operation() -> str:
            await asyncio.sleep(0.01)
            return "done"

        # Act
        await with_timeout(
            simple_operation,
            timeout_seconds=1,
            operation_name="Test operation"
        )

        # Assert
        # Check debug logs for start and completion
        assert mock_logger.debug.call_count == 2
        start_call = mock_logger.debug.call_args_list[0][0][0]
        completion_call = mock_logger.debug.call_args_list[1][0][0]

        assert "Starting Test operation" in start_call
        assert "1s timeout" in start_call
        assert "Completed Test operation" in completion_call
        assert "within timeout" in completion_call

    @pytest.mark.asyncio
    async def test_should_log_timeout_error(self, mocker):
        """Test that timeout errors are logged."""
        # Arrange
        mock_logger = mocker.patch('finwiz.utils.timeout_handler.logger')

        async def slow_operation() -> str:
            await asyncio.sleep(2)
            return "Should not reach"

        # Act & Assert
        with pytest.raises(TimeoutError):
            await with_timeout(
                slow_operation,
                timeout_seconds=0.1,
                operation_name="Slow operation"
            )

        # Assert error log
        mock_logger.error.assert_called_once()
        error_message = mock_logger.error.call_args[0][0]
        assert "Timeout: Slow operation" in error_message
        assert "exceeded 0.1s timeout" in error_message

    @pytest.mark.asyncio
    async def test_should_use_asyncio_wait_for(self, mocker):
        """Test that asyncio.wait_for is used for timeout enforcement."""
        # Arrange
        mock_wait_for = mocker.patch('asyncio.wait_for')
        mock_wait_for.return_value = "mocked_result"

        async def test_operation() -> str:
            return "test"

        # Act
        result = await with_timeout(
            test_operation,
            timeout_seconds=5,
            operation_name="Test"
        )

        # Assert
        assert result == "mocked_result"
        mock_wait_for.assert_called_once()
        # Verify timeout parameter was passed
        call_kwargs = mock_wait_for.call_args[1]
        assert call_kwargs['timeout'] == 5

    @pytest.mark.asyncio
    async def test_should_handle_zero_timeout(self, mocker):
        """Test behavior with zero timeout."""
        # Arrange
        async def instant_operation() -> str:
            return "instant"

        # Act & Assert
        # Zero timeout should cause immediate timeout
        with pytest.raises(TimeoutError):
            await with_timeout(
                instant_operation,
                timeout_seconds=0,
                operation_name="Zero timeout"
            )

    @pytest.mark.asyncio
    async def test_should_propagate_exceptions_from_coroutine(self, mocker):
        """Test that exceptions from coroutine are propagated."""
        # Arrange
        async def failing_operation() -> str:
            await asyncio.sleep(0.01)
            raise ValueError("Operation failed")

        # Act & Assert
        with pytest.raises(ValueError, match="Operation failed"):
            await with_timeout(
                failing_operation,
                timeout_seconds=1,
                operation_name="Failing operation"
            )


class TestWithTimeoutGraceful:
    """Test cases for graceful timeout with fallback."""

    @pytest.mark.asyncio
    async def test_should_complete_within_timeout(self, mocker):
        """Test that function completes successfully within timeout."""
        # Arrange
        async def fast_operation(value: str) -> str:
            await asyncio.sleep(0.01)
            return f"Result: {value}"

        # Act
        result = await with_timeout_graceful(
            fast_operation,
            timeout_seconds=1,
            operation_name="Fast operation",
            fallback_value="fallback",
            value="test"
        )

        # Assert
        assert result == "Result: test"

    @pytest.mark.asyncio
    async def test_should_return_fallback_on_timeout(self, mocker):
        """Test that fallback value is returned on timeout."""
        # Arrange
        async def slow_operation() -> str:
            await asyncio.sleep(2)
            return "Should not reach here"

        fallback = {"status": "timeout"}

        # Act
        result = await with_timeout_graceful(
            slow_operation,
            timeout_seconds=0.1,
            operation_name="Slow operation",
            fallback_value=fallback
        )

        # Assert
        assert result == fallback
        assert result["status"] == "timeout"

    @pytest.mark.asyncio
    async def test_should_return_none_as_default_fallback(self, mocker):
        """Test that None is returned as default fallback on timeout."""
        # Arrange
        async def slow_operation() -> str:
            await asyncio.sleep(2)
            return "Should not reach"

        # Act
        result = await with_timeout_graceful(
            slow_operation,
            timeout_seconds=0.1,
            operation_name="Slow operation"
            # No fallback_value specified
        )

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_should_pass_kwargs_to_coroutine(self, mocker):
        """Test that keyword arguments are passed to the coroutine."""
        # Arrange
        async def operation_with_args(ticker: str, amount: int) -> dict:
            await asyncio.sleep(0.01)
            return {"ticker": ticker, "amount": amount}

        # Act
        result = await with_timeout_graceful(
            operation_with_args,
            timeout_seconds=1,
            operation_name="Operation with args",
            fallback_value={},
            ticker="TSLA",
            amount=100
        )

        # Assert
        assert result["ticker"] == "TSLA"
        assert result["amount"] == 100

    @pytest.mark.asyncio
    async def test_should_log_warning_on_timeout(self, mocker):
        """Test that warning is logged when timeout occurs."""
        # Arrange
        mock_logger = mocker.patch('finwiz.utils.timeout_handler.logger')

        async def slow_operation() -> str:
            await asyncio.sleep(2)
            return "Should not reach"

        # Act
        await with_timeout_graceful(
            slow_operation,
            timeout_seconds=0.1,
            operation_name="Slow operation",
            fallback_value="fallback"
        )

        # Assert
        mock_logger.warning.assert_called_once()
        warning_message = mock_logger.warning.call_args[0][0]
        assert "Timeout: Slow operation" in warning_message
        assert "returning fallback value" in warning_message

    @pytest.mark.asyncio
    async def test_should_not_raise_timeout_error(self, mocker):
        """Test that TimeoutError is caught and not raised."""
        # Arrange
        async def slow_operation() -> str:
            await asyncio.sleep(2)
            return "Should not reach"

        # Act
        # Should not raise TimeoutError
        result = await with_timeout_graceful(
            slow_operation,
            timeout_seconds=0.1,
            operation_name="Slow operation",
            fallback_value="safe_fallback"
        )

        # Assert
        assert result == "safe_fallback"

    @pytest.mark.asyncio
    async def test_should_use_with_timeout_internally(self, mocker):
        """Test that with_timeout_graceful uses with_timeout internally."""
        # Arrange
        mock_with_timeout = mocker.patch(
            'finwiz.utils.timeout_handler.with_timeout',
            side_effect=TimeoutError()
        )

        async def test_operation() -> str:
            return "test"

        # Act
        result = await with_timeout_graceful(
            test_operation,
            timeout_seconds=5,
            operation_name="Test",
            fallback_value="fallback"
        )

        # Assert
        assert result == "fallback"
        mock_with_timeout.assert_called_once()

    @pytest.mark.asyncio
    async def test_should_handle_different_fallback_types(self, mocker):
        """Test that different fallback value types are handled correctly."""
        # Arrange
        async def slow_operation() -> str:
            await asyncio.sleep(2)
            return "Should not reach"

        test_cases = [
            None,
            "",
            0,
            [],
            {},
            False,
            {"complex": "object", "with": ["nested", "data"]},
        ]

        # Act & Assert
        for fallback in test_cases:
            result = await with_timeout_graceful(
                slow_operation,
                timeout_seconds=0.1,
                operation_name="Test",
                fallback_value=fallback
            )
            assert result == fallback

    @pytest.mark.asyncio
    async def test_should_propagate_non_timeout_exceptions(self, mocker):
        """Test that non-timeout exceptions are propagated."""
        # Arrange
        async def failing_operation() -> str:
            await asyncio.sleep(0.01)
            raise ValueError("Operation failed")

        # Act & Assert
        with pytest.raises(ValueError, match="Operation failed"):
            await with_timeout_graceful(
                failing_operation,
                timeout_seconds=1,
                operation_name="Failing operation",
                fallback_value="fallback"
            )


class TestTimeoutHandlerIntegration:
    """Integration tests for timeout handler components."""

    @pytest.mark.asyncio
    async def test_should_handle_nested_timeouts(self, mocker):
        """Test behavior with nested timeout operations."""
        # Arrange
        async def inner_operation() -> str:
            await asyncio.sleep(0.05)
            return "inner_result"

        async def outer_operation() -> str:
            result = await with_timeout(
                inner_operation,
                timeout_seconds=1,
                operation_name="Inner operation"
            )
            return f"outer_{result}"

        # Act
        result = await with_timeout(
            outer_operation,
            timeout_seconds=2,
            operation_name="Outer operation"
        )

        # Assert
        assert result == "outer_inner_result"

    @pytest.mark.asyncio
    async def test_should_handle_parallel_operations_with_timeout(self, mocker):
        """Test timeout handling with parallel async operations."""
        # Arrange
        async def operation(delay: float, value: str) -> str:
            await asyncio.sleep(delay)
            return value

        # Act
        results = await asyncio.gather(
            with_timeout_graceful(
                operation,
                timeout_seconds=0.5,
                operation_name="Op1",
                fallback_value="timeout1",
                delay=0.01,
                value="result1"
            ),
            with_timeout_graceful(
                operation,
                timeout_seconds=0.5,
                operation_name="Op2",
                fallback_value="timeout2",
                delay=1.0,  # Will timeout
                value="result2"
            ),
            with_timeout_graceful(
                operation,
                timeout_seconds=0.5,
                operation_name="Op3",
                fallback_value="timeout3",
                delay=0.02,
                value="result3"
            ),
        )

        # Assert
        assert results[0] == "result1"  # Completed
        assert results[1] == "timeout2"  # Timed out
        assert results[2] == "result3"  # Completed

    @pytest.mark.asyncio
    async def test_should_measure_actual_timeout_duration(self, mocker):
        """Test that timeout occurs at approximately the specified duration."""
        # Arrange
        import time

        async def slow_operation() -> str:
            await asyncio.sleep(10)
            return "Should not reach"

        timeout_seconds = 0.2
        start_time = time.time()

        # Act
        result = await with_timeout_graceful(
            slow_operation,
            timeout_seconds=timeout_seconds,
            operation_name="Timed operation",
            fallback_value="timeout"
        )

        elapsed = time.time() - start_time

        # Assert
        assert result == "timeout"
        # Should timeout close to specified duration (with some tolerance)
        assert elapsed < timeout_seconds + 0.1
        assert elapsed >= timeout_seconds - 0.05

    @pytest.mark.asyncio
    async def test_should_handle_complex_return_types(self, mocker):
        """Test timeout handling with complex return types."""
        # Arrange
        async def complex_operation() -> dict:
            await asyncio.sleep(0.01)
            return {
                "ticker": "AAPL",
                "analysis": {
                    "grade": "A+",
                    "score": 0.95,
                    "metrics": [1, 2, 3]
                },
                "timestamp": "2025-01-11T12:00:00"
            }

        # Act
        result = await with_timeout(
            complex_operation,
            timeout_seconds=1,
            operation_name="Complex operation"
        )

        # Assert
        assert result["ticker"] == "AAPL"
        assert result["analysis"]["grade"] == "A+"
        assert len(result["analysis"]["metrics"]) == 3

    @pytest.mark.asyncio
    async def test_should_handle_exception_during_timeout(self, mocker):
        """Test that exceptions during timeout are handled correctly."""
        # Arrange
        async def operation_with_exception() -> str:
            await asyncio.sleep(0.05)
            raise RuntimeError("Unexpected error")

        # Act & Assert
        # Exception should be propagated, not caught as timeout
        with pytest.raises(RuntimeError, match="Unexpected error"):
            await with_timeout(
                operation_with_exception,
                timeout_seconds=1,
                operation_name="Exception operation"
            )

    @pytest.mark.asyncio
    async def test_should_compare_strict_vs_graceful_behavior(self, mocker):
        """Test difference between strict and graceful timeout handling."""
        # Arrange
        async def slow_operation() -> str:
            await asyncio.sleep(2)
            return "Should not reach"

        # Act & Assert - Strict version raises
        with pytest.raises(TimeoutError):
            await with_timeout(
                slow_operation,
                timeout_seconds=0.1,
                operation_name="Strict timeout"
            )

        # Act & Assert - Graceful version returns fallback
        result = await with_timeout_graceful(
            slow_operation,
            timeout_seconds=0.1,
            operation_name="Graceful timeout",
            fallback_value="fallback"
        )
        assert result == "fallback"


class TestTimeoutHandlerEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_should_handle_very_short_timeout(self, mocker):
        """Test behavior with very short timeout (milliseconds)."""
        # Arrange
        async def operation() -> str:
            await asyncio.sleep(0.001)
            return "fast"

        # Act
        result = await with_timeout_graceful(
            operation,
            timeout_seconds=0.01,  # 10ms
            operation_name="Very short timeout",
            fallback_value="timeout"
        )

        # Assert
        # May complete or timeout depending on system load
        assert result in ["fast", "timeout"]

    @pytest.mark.asyncio
    async def test_should_handle_very_long_timeout(self, mocker):
        """Test behavior with very long timeout."""
        # Arrange
        async def fast_operation() -> str:
            await asyncio.sleep(0.01)
            return "completed"

        # Act
        result = await with_timeout(
            fast_operation,
            timeout_seconds=3600,  # 1 hour
            operation_name="Very long timeout"
        )

        # Assert
        assert result == "completed"

    @pytest.mark.asyncio
    async def test_should_handle_operation_that_returns_none(self, mocker):
        """Test timeout handling when operation returns None."""
        # Arrange
        async def operation_returning_none() -> None:
            await asyncio.sleep(0.01)
            return None

        # Act
        result = await with_timeout(
            operation_returning_none,
            timeout_seconds=1,
            operation_name="None returning operation"
        )

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_should_handle_empty_kwargs(self, mocker):
        """Test timeout handling with no keyword arguments."""
        # Arrange
        async def operation_no_args() -> str:
            await asyncio.sleep(0.01)
            return "no_args"

        # Act
        result = await with_timeout(
            operation_no_args,
            timeout_seconds=1,
            operation_name="No args operation"
        )

        # Assert
        assert result == "no_args"

    @pytest.mark.asyncio
    async def test_should_handle_operation_name_with_special_chars(self, mocker):
        """Test logging with operation names containing special characters."""
        # Arrange
        mock_logger = mocker.patch('finwiz.utils.timeout_handler.logger')

        async def operation() -> str:
            await asyncio.sleep(0.01)
            return "done"

        special_name = "Deep analysis for AAPL (retry #2) - 50% complete"

        # Act
        await with_timeout(
            operation,
            timeout_seconds=1,
            operation_name=special_name
        )

        # Assert
        # Should log without errors
        assert mock_logger.debug.call_count == 2
        start_log = mock_logger.debug.call_args_list[0][0][0]
        assert special_name in start_log
