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
    from finwiz.infrastructure.resilience import crew_execution

    # Open the circuit breaker manually
    _crew_failures["recovered_crew"] = FAILURE_THRESHOLD
    # Pin the cooldown: production reads it from _get_recovery_timeout(), which
    # resolves FINWIZ_CIRCUIT_BREAKER_RECOVERY. Stamping against the local
    # RECOVERY_TIMEOUT constant alone means an environment setting it above 121
    # leaves the breaker still open, and this test sleeps or fails.
    mocker.patch.object(crew_execution, "_get_recovery_timeout", lambda: RECOVERY_TIMEOUT)
    _crew_circuit_open["recovered_crew"] = time.time() - RECOVERY_TIMEOUT - 1  # Past recovery

    crew = _make_crew(mocker, return_value="recovered_result")

    result = await execute_crew_with_timeout("recovered_crew", crew, {"ticker": "OK"}, timeout=10)

    assert result == "recovered_result"
    assert "recovered_crew" not in _crew_circuit_open
    assert _crew_failures["recovered_crew"] == 0


@pytest.mark.asyncio
async def test_circuit_breaker_still_open_before_recovery(mocker):
    """Circuit breaker waits out the remaining cooldown, then retries.

    Previously asserted an immediate breaker-open error with kickoff never
    called (that error type has since been deleted -- nothing raises it).
    Task 2 replaces that fail-fast with wait-then-retry: a holding pays for
    an open breaker in time, not by losing its in-flight analysis. This wait
    is NOT bounded by FINWIZ_HOLDING_TIMEOUT -- see the module docstring's
    Note for why. See test_open_breaker_waits_for_cooldown_then_retries for
    the isolated case.
    """
    from finwiz.infrastructure.resilience import crew_execution

    mocker.patch.object(crew_execution, "_get_recovery_timeout", lambda: 0.2)
    _crew_failures["still_open"] = FAILURE_THRESHOLD
    crew = _make_crew(mocker, return_value="recovered_after_wait")

    # Build the mock BEFORE stamping the breaker. _wait_out_open_breaker sleeps
    # until opened_at + recovery, so anchoring the stopwatch anywhere after the
    # stamp subtracts the setup time from the measurement -- a flaky assertion
    # whose whole margin is asyncio.sleep's ~1ms overshoot.
    opened_at = time.time()
    _crew_circuit_open["still_open"] = opened_at  # Just opened

    result = await execute_crew_with_timeout("still_open", crew, {"ticker": "X"}, timeout=10)

    assert result == "recovered_after_wait"
    crew.kickoff.assert_called_once()
    assert "still_open" not in _crew_circuit_open
    # The cooldown must actually be *waited out*, not merely popped. Without
    # this, an implementation that cleared the breaker and returned
    # immediately would satisfy every other assertion here.
    assert time.time() - opened_at >= 0.2


@pytest.mark.asyncio
async def test_open_breaker_waits_for_cooldown_then_retries(mocker):
    """An open breaker should cost a holding time, not its analysis."""
    from finwiz.infrastructure.resilience import crew_execution

    crew_execution.reset_circuit_breakers()
    mocker.patch.object(crew_execution, "_get_recovery_timeout", lambda: 0.2)

    good_crew = mocker.Mock()
    good_crew.kickoff = mocker.Mock(return_value="ok")

    # Mocks first, then stamp: the sleep target is opened_at + recovery, so the
    # stopwatch has to start at the stamp or the setup gap eats the margin.
    opened_at = time.time()
    crew_execution._crew_circuit_open["deep_analysis_stock"] = opened_at

    # NOTE: the task brief's snippet called execute_crew_with_timeout(good_crew,
    # "deep_analysis_stock", {}) — the real signature is
    # (crew_name, crew_instance, inputs, timeout=None). Using the real order below.
    result = await crew_execution.execute_crew_with_timeout("deep_analysis_stock", good_crew, {})

    assert result == "ok"
    good_crew.kickoff.assert_called_once()
    # "Costs a holding time, not its analysis" is half a timing claim. Without
    # this assertion the test passes against an implementation that pops the
    # cooldown without ever sleeping.
    assert time.time() - opened_at >= 0.2


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
    """A handful of timeouts is a per-holding event, not an upstream outage.

    Five slow holdings must not blind 31 healthy ones. ValidationError already
    bypasses the (non-timeout) failure counter for the same reason (the
    2026-04-28 ETF cascade); this pins the timeout half of that lesson. Six
    timeouts stay well under the separate, higher timeout threshold (default
    15) added for the hung-provider case below.
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
    assert crew_execution._crew_timeout_failures.get("deep_analysis_stock", 0) == 6
    assert "deep_analysis_stock" not in crew_execution._crew_circuit_open


def test_hung_provider_eventually_opens_breaker_via_timeout_counter(mocker):
    """A provider that hangs on every request must still trip the breaker.

    Bug: excluding timeouts from the failure counter entirely (the original
    Task 1 fix) means a fully hung upstream produces only TimeoutErrors and
    the breaker never opens -- every one of 64 holdings burns a full
    CREW_TIMEOUT before giving up. Fix: timeouts get their own counter with
    its own (higher) threshold, so a hung provider is still detected.
    """
    from finwiz.infrastructure.resilience import crew_execution

    crew_execution.reset_circuit_breakers()
    mocker.patch.object(crew_execution, "_get_timeout_failure_threshold", lambda: 3)
    mocker.patch.object(crew_execution, "CREW_TIMEOUT", 0.01)

    hung_crew = mocker.Mock()
    hung_crew.kickoff = lambda inputs: time.sleep(1.0)

    for _ in range(3):
        with pytest.raises(TimeoutError):
            asyncio.run(crew_execution.execute_crew_with_timeout("hung_crew", hung_crew, {}))

    assert crew_execution._crew_timeout_failures["hung_crew"] == 3
    assert "hung_crew" in crew_execution._crew_circuit_open
    # The non-timeout counter must stay untouched -- opening came from the
    # timeout counter, not a reinterpretation of timeouts as generic failures.
    assert crew_execution._crew_failures.get("hung_crew", 0) == 0


@pytest.mark.asyncio
async def test_one_slow_holding_does_not_open_breaker(mocker):
    """A single slow ticker among many healthy ones must never trip the breaker."""
    from finwiz.infrastructure.resilience import crew_execution

    mocker.patch.object(crew_execution, "_get_timeout_failure_threshold", lambda: 15)

    def slow_kickoff(inputs=None):
        time.sleep(2)

    crew = _make_crew(mocker, side_effect=slow_kickoff)

    with pytest.raises(TimeoutError):
        await execute_crew_with_timeout("one_slow", crew, {"ticker": "SLOW"}, timeout=0.1)

    assert crew_execution._crew_timeout_failures.get("one_slow", 0) == 1
    assert "one_slow" not in crew_execution._crew_circuit_open


@pytest.mark.asyncio
async def test_failure_counter_reset_on_half_open_prevents_instant_reopen(mocker):
    """After a cooldown elapses, a single subsequent failure must not immediately reopen it.

    Bug: the failure counter stayed at FAILURE_THRESHOLD after the cooldown
    expired, so the very next failure made it threshold+1 >= threshold and
    reopened the breaker instantly -- a live-but-flaky provider became a loop
    where every holding paid a full cooldown for one failure. Fix: reset the
    counter on the half-open transition.
    """
    from finwiz.infrastructure.resilience import crew_execution

    _crew_failures["flaky_reset"] = FAILURE_THRESHOLD
    mocker.patch.object(crew_execution, "_get_recovery_timeout", lambda: RECOVERY_TIMEOUT)
    _crew_circuit_open["flaky_reset"] = time.time() - RECOVERY_TIMEOUT - 1  # already past cooldown

    crew = _make_crew(mocker, side_effect=RuntimeError("still flaky"))

    with pytest.raises(RuntimeError, match="still flaky"):
        await execute_crew_with_timeout("flaky_reset", crew, {"ticker": "X"}, timeout=10)

    # One failure after half-open -> counter is 1, not 6, so the breaker must
    # NOT have reopened.
    assert crew_execution._crew_failures["flaky_reset"] == 1
    assert "flaky_reset" not in crew_execution._crew_circuit_open


@pytest.mark.asyncio
async def test_cooldown_reopened_during_wait_is_not_cleared_by_stale_waiter(mocker):
    """A cooldown re-opened by a concurrent holding during another's sleep must not be cleared.

    Bug: `remaining` was snapshotted before `await asyncio.sleep(remaining)`,
    but the `pop` after the sleep was unconditional. A breaker re-opened by a
    concurrent holding *during* the sleep got wiped by this coroutine,
    discarding that fresh cooldown.
    """
    from finwiz.infrastructure.resilience import crew_execution

    mocker.patch.object(crew_execution, "_get_recovery_timeout", lambda: 0.2)
    first_open_ts = time.time()
    crew_execution._crew_circuit_open["racy_crew"] = first_open_ts

    async def reopen_mid_wait() -> None:
        # Fires while the main waiter below is still asleep (its cooldown is
        # 0.2s; this reopens with a fresh timestamp partway through).
        await asyncio.sleep(0.05)
        with crew_execution._state_lock:
            crew_execution._crew_circuit_open["racy_crew"] = time.time()

    crew = _make_crew(mocker, return_value="ok")

    reopener = asyncio.create_task(reopen_mid_wait())
    result = await execute_crew_with_timeout("racy_crew", crew, {"ticker": "X"}, timeout=10)
    await reopener

    # The stale waiter (snapshotted first_open_ts) must not have popped the
    # fresher cooldown set by the concurrent reopen.
    assert result == "ok"
    assert "racy_crew" in crew_execution._crew_circuit_open
    assert crew_execution._crew_circuit_open["racy_crew"] != first_open_ts


@pytest.mark.asyncio
async def test_concurrent_waiters_on_same_crew_do_not_serialize_cooldown(mocker):
    """N concurrent holdings hitting the same open breaker must wait roughly
    one cooldown period in total, not N cooldown periods serialized.
    """
    from finwiz.infrastructure.resilience import crew_execution

    mocker.patch.object(crew_execution, "_get_recovery_timeout", lambda: 0.2)
    crew_execution._crew_circuit_open["parallel_crew"] = time.time()

    crew = _make_crew(mocker, return_value="ok")

    start = time.monotonic()
    results = await asyncio.gather(*(execute_crew_with_timeout("parallel_crew", crew, {"ticker": f"T{i}"}, timeout=10) for i in range(5)))
    elapsed = time.monotonic() - start

    assert results == ["ok"] * 5
    # Serialized would take ~5 * 0.2s = 1.0s; concurrent should stay well
    # under that -- generous bound to absorb scheduling jitter.
    assert elapsed < 0.6


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
