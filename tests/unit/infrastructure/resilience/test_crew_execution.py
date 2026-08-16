"""Tests for crew execution wrapper with timeout and circuit breaker."""

import asyncio
import time

import pytest

from finwiz.infrastructure.resilience.crew_execution import (
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
    """Crew that exceeds timeout raises TimeoutError WITHOUT incrementing the
    breaker counter.

    A timeout is a per-holding event, not an upstream outage — see
    test_timeout_does_not_increment_breaker_counter below for the full
    rationale (2026-08-16 cascade).
    """

    def slow_kickoff(inputs=None):
        time.sleep(2)
        return "should_not_reach"

    crew = _make_crew(mocker, side_effect=slow_kickoff)

    with pytest.raises(TimeoutError):
        await execute_crew_with_timeout("slow_crew", crew, {"ticker": "SLOW"}, timeout=0.1)

    assert _crew_failures.get("slow_crew", 0) == 0
    assert "slow_crew" not in _crew_circuit_open


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
    from finwiz.infrastructure.resilience import crew_execution

    mocker.patch.object(crew_execution, "_get_recovery_timeout", lambda: 0.05)
    crew = _make_crew(mocker, side_effect=RuntimeError("fail"))

    # Fail FAILURE_THRESHOLD times
    for _i in range(FAILURE_THRESHOLD):
        with pytest.raises(RuntimeError):
            await execute_crew_with_timeout("flaky_crew", crew, {"ticker": "FAIL"}, timeout=10)

    assert _crew_failures["flaky_crew"] == FAILURE_THRESHOLD
    assert "flaky_crew" in _crew_circuit_open

    # Next call waits out the (mocked, near-zero) cooldown and retries — the
    # crew still fails, so the caller sees the crew's own error rather than an
    # instant CircuitBreakerOpenError. Task 2: the breaker now costs a holding
    # time, not its analysis attempt.
    with pytest.raises(RuntimeError, match="fail"):
        await execute_crew_with_timeout("flaky_crew", crew, {"ticker": "FAIL"}, timeout=10)

    assert crew.kickoff.call_count == FAILURE_THRESHOLD + 1


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
    """Circuit breaker waits out the remaining cooldown, then retries.

    Previously asserted an immediate CircuitBreakerOpenError with kickoff
    never called. Task 2 replaces that fail-fast with wait-then-retry: a
    holding pays for an open breaker in time (bounded by the outer
    FINWIZ_HOLDING_TIMEOUT), not by losing its in-flight analysis. See
    test_open_breaker_waits_for_cooldown_then_retries for the isolated case.
    """
    from finwiz.infrastructure.resilience import crew_execution

    mocker.patch.object(crew_execution, "_get_recovery_timeout", lambda: 0.05)
    _crew_failures["still_open"] = FAILURE_THRESHOLD
    _crew_circuit_open["still_open"] = time.time()  # Just opened

    crew = _make_crew(mocker, return_value="recovered_after_wait")

    result = await execute_crew_with_timeout("still_open", crew, {"ticker": "X"}, timeout=10)

    assert result == "recovered_after_wait"
    crew.kickoff.assert_called_once()
    assert "still_open" not in _crew_circuit_open


@pytest.mark.asyncio
async def test_open_breaker_waits_for_cooldown_then_retries(mocker):
    """An open breaker should cost a holding time, not its analysis."""
    from finwiz.infrastructure.resilience import crew_execution

    crew_execution.reset_circuit_breakers()
    mocker.patch.object(crew_execution, "_get_recovery_timeout", lambda: 0.2)
    crew_execution._crew_circuit_open["deep_analysis_stock"] = time.time()

    good_crew = mocker.Mock()
    good_crew.kickoff = mocker.Mock(return_value="ok")

    # NOTE: the task brief's snippet called execute_crew_with_timeout(good_crew,
    # "deep_analysis_stock", {}) — the real signature is
    # (crew_name, crew_instance, inputs, timeout=None). Using the real order below.
    result = await crew_execution.execute_crew_with_timeout("deep_analysis_stock", good_crew, {})

    assert result == "ok"
    good_crew.kickoff.assert_called_once()


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


@pytest.mark.asyncio
async def test_validation_error_does_not_increment_breaker(mocker):
    """Pydantic ValidationError must NOT trip the circuit breaker.

    Regression for the 2026-04-28 ETF cascade: the LLM kept producing payloads
    that failed FactPack's freshness model_validator, CrewAI retried, and the
    breaker tripped on what was really a deterministic schema mismatch. Backoff
    cannot fix a schema mismatch — exclude these from the failure counter.
    """
    from pydantic import BaseModel, ValidationError

    class _Schema(BaseModel):
        x: int

    def kickoff_raises(inputs=None):
        # Force a real ValidationError (not a synthesized subclass).
        _Schema(x="not-an-int")  # type: ignore[arg-type]

    crew = _make_crew(mocker, side_effect=kickoff_raises)

    with pytest.raises(ValidationError):
        await execute_crew_with_timeout("schema_thrash", crew, {"ticker": "X"}, timeout=10)

    # No counter increment, no breaker entry.
    assert _crew_failures.get("schema_thrash", 0) == 0
    assert "schema_thrash" not in _crew_circuit_open


def test_timeout_does_not_increment_breaker_counter(mocker):
    """A timeout is a per-holding event, not an upstream outage.

    Five slow holdings must not blind 31 healthy ones. ValidationError already
    bypasses the counter for the same reason (the 2026-04-28 ETF cascade); this
    pins the timeout half of that lesson.
    """
    from finwiz.infrastructure.resilience import crew_execution

    crew_execution.reset_circuit_breakers()
    mocker.patch.object(crew_execution, "CREW_TIMEOUT", 0.01)

    slow_crew = mocker.Mock()
    slow_crew.kickoff = lambda inputs: time.sleep(1.0)

    for _ in range(6):
        with pytest.raises(TimeoutError):
            asyncio.run(crew_execution.execute_crew_with_timeout("deep_analysis_stock", slow_crew, {}))

    assert crew_execution._crew_failures.get("deep_analysis_stock", 0) == 0
    assert "deep_analysis_stock" not in crew_execution._crew_circuit_open


def test_emit_pending_distinguishes_breaker_open_reason() -> None:
    """_emit_pending must produce a distinctive French rationale when the
    upstream reason names the circuit breaker, so users can tell a breaker-
    induced skip apart from a generic pending row.
    """
    from pathlib import Path

    from finwiz.analysis.stages._ledger import RunLedger
    from finwiz.analysis.stages._resilience import StageContext
    from finwiz.analysis.stages.emit import _emit_pending

    ledger = RunLedger(run_id="r-test", artifact_dir=Path("/tmp/finwiz-test-ledger"))
    ctx = StageContext(ticker="EXSA.DE", run_id="r-test", ledger=ledger, extras={})

    breaker_reason = "Circuit breaker open for deep_analysis_etf"
    pending = _emit_pending(ctx, reason=breaker_reason)
    assert "circuit breaker ouvert" in pending.rationale
    assert "réessayer" in pending.rationale

    # Generic pending stays distinct.
    other = _emit_pending(ctx, reason="qualify timed out")
    assert "circuit breaker" not in other.rationale.lower()


@pytest.mark.asyncio
async def test_records_crew_usage_when_result_has_token_usage(mocker):
    """Honest cost tracking: usage is recorded from CrewOutput.token_usage at the chokepoint."""
    from types import SimpleNamespace

    token_usage = SimpleNamespace(prompt_tokens=10, completion_tokens=5, successful_requests=1)
    result = SimpleNamespace(token_usage=token_usage)
    crew = mocker.MagicMock()
    crew.kickoff.return_value = result

    monitor = mocker.MagicMock()
    mocker.patch(
        "finwiz.infrastructure.monitoring.litellm_callback.get_token_monitor",
        return_value=monitor,
    )
    mocker.patch(
        "finwiz.crews.helpers.llm_config.get_crew_model_string",
        return_value="openai/gpt-4o-mini",
    )

    out = await execute_crew_with_timeout("deep_analysis_stock", crew, {"ticker": "AAPL"}, timeout=10)

    assert out is result
    monitor.record_usage.assert_called_once()
    args, kwargs = monitor.record_usage.call_args
    assert args[0] == "deep_analysis_stock"
    assert args[1] is token_usage
    assert kwargs.get("model") == "openai/gpt-4o-mini"


@pytest.mark.asyncio
async def test_usage_recording_failure_does_not_break_execution(mocker):
    """Cost tracking is best-effort: a monitor error must not fail the crew run."""
    from types import SimpleNamespace

    result = SimpleNamespace(token_usage=SimpleNamespace(prompt_tokens=1, completion_tokens=1, successful_requests=1))
    crew = mocker.MagicMock()
    crew.kickoff.return_value = result

    monitor = mocker.MagicMock()
    monitor.record_usage.side_effect = RuntimeError("boom")
    mocker.patch(
        "finwiz.infrastructure.monitoring.litellm_callback.get_token_monitor",
        return_value=monitor,
    )

    out = await execute_crew_with_timeout("deep_analysis_etf", crew, {}, timeout=10)
    assert out is result  # execution still succeeds despite tracking error
