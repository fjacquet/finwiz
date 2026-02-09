"""Tests for crew execution wrapper with timeout and circuit breaker."""

import time

import pytest

from finwiz.infrastructure.resilience.crew_execution import (
    CircuitBreakerOpenError,
    _crew_circuit_open,
    _crew_failures,
    execute_crew_with_timeout,
    reset_circuit_breakers,
)

# Default values matching ResilienceConfig defaults
FAILURE_THRESHOLD = 5
RECOVERY_TIMEOUT = 120.0


@pytest.fixture(autouse=True)
def _clean_circuit_breakers():
    """Reset circuit breaker state before and after each test."""
    reset_circuit_breakers()
    yield
    reset_circuit_breakers()


def _make_crew(mocker, side_effect=None, return_value="crew_result"):
    """Create a mock crew with a kickoff method."""
    crew = mocker.MagicMock()
    if side_effect is not None:
        crew.kickoff.side_effect = side_effect
    else:
        crew.kickoff.return_value = return_value
    return crew


@pytest.mark.asyncio
async def test_execute_crew_with_timeout_success(mocker):
    """Successful crew execution returns result and resets failure counter."""
    crew = _make_crew(mocker, return_value="analysis_done")
    # Pre-set a failure to verify it gets reset on success
    _crew_failures["test_crew"] = 1

    result = await execute_crew_with_timeout("test_crew", crew, {"ticker": "AAPL"}, timeout=10)

    assert result == "analysis_done"
    crew.kickoff.assert_called_once_with(inputs={"ticker": "AAPL"})
    assert _crew_failures["test_crew"] == 0


@pytest.mark.asyncio
async def test_execute_crew_with_timeout_timeout(mocker):
    """Crew that exceeds timeout raises TimeoutError and increments failure count."""

    def slow_kickoff(inputs=None):
        time.sleep(2)
        return "should_not_reach"

    crew = _make_crew(mocker, side_effect=slow_kickoff)

    with pytest.raises(TimeoutError):
        await execute_crew_with_timeout("slow_crew", crew, {"ticker": "SLOW"}, timeout=0.1)

    assert _crew_failures["slow_crew"] == 1


@pytest.mark.asyncio
async def test_execute_crew_with_timeout_exception(mocker):
    """Crew that raises an exception increments failure count and re-raises."""
    crew = _make_crew(mocker, side_effect=RuntimeError("LLM API down"))

    with pytest.raises(RuntimeError, match="LLM API down"):
        await execute_crew_with_timeout("broken_crew", crew, {"ticker": "ERR"}, timeout=10)

    assert _crew_failures["broken_crew"] == 1


@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_threshold(mocker):
    """Circuit breaker opens after FAILURE_THRESHOLD consecutive failures."""
    crew = _make_crew(mocker, side_effect=RuntimeError("fail"))

    # Fail FAILURE_THRESHOLD times
    for _i in range(FAILURE_THRESHOLD):
        with pytest.raises(RuntimeError):
            await execute_crew_with_timeout("flaky_crew", crew, {"ticker": "FAIL"}, timeout=10)

    assert _crew_failures["flaky_crew"] == FAILURE_THRESHOLD
    assert "flaky_crew" in _crew_circuit_open

    # Next call should raise CircuitBreakerOpenError without even trying
    with pytest.raises(CircuitBreakerOpenError, match="Circuit breaker open for flaky_crew"):
        await execute_crew_with_timeout("flaky_crew", crew, {"ticker": "FAIL"}, timeout=10)


@pytest.mark.asyncio
async def test_circuit_breaker_half_open_after_recovery(mocker):
    """Circuit breaker allows retry after RECOVERY_TIMEOUT passes."""
    # Open the circuit breaker manually
    _crew_failures["recovered_crew"] = FAILURE_THRESHOLD
    _crew_circuit_open["recovered_crew"] = time.time() - RECOVERY_TIMEOUT - 1  # Past recovery

    crew = _make_crew(mocker, return_value="recovered_result")

    result = await execute_crew_with_timeout("recovered_crew", crew, {"ticker": "OK"}, timeout=10)

    assert result == "recovered_result"
    assert "recovered_crew" not in _crew_circuit_open
    assert _crew_failures["recovered_crew"] == 0


@pytest.mark.asyncio
async def test_circuit_breaker_still_open_before_recovery(mocker):
    """Circuit breaker stays open if recovery timeout has not passed."""
    _crew_failures["still_open"] = FAILURE_THRESHOLD
    _crew_circuit_open["still_open"] = time.time()  # Just opened

    crew = _make_crew(mocker, return_value="should_not_reach")

    with pytest.raises(CircuitBreakerOpenError):
        await execute_crew_with_timeout("still_open", crew, {"ticker": "X"}, timeout=10)

    # kickoff should NOT have been called
    crew.kickoff.assert_not_called()


@pytest.mark.asyncio
async def test_reset_circuit_breakers(mocker):
    """reset_circuit_breakers() clears all state, allowing retries."""
    # Open circuit for a crew
    _crew_failures["reset_test"] = FAILURE_THRESHOLD
    _crew_circuit_open["reset_test"] = time.time()

    reset_circuit_breakers()

    crew = _make_crew(mocker, return_value="fresh_start")
    result = await execute_crew_with_timeout("reset_test", crew, {"ticker": "RST"}, timeout=10)

    assert result == "fresh_start"
    assert _crew_failures["reset_test"] == 0
