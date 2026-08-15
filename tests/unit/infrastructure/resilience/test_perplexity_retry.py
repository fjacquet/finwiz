"""Tests for the Perplexity retry wrapper."""

import asyncio

import pytest
from pydantic import BaseModel

from finwiz.infrastructure.resilience.perplexity_retry import (
    get_perplexity_semaphore,
    perplexity_with_retry,
)


class _Payload(BaseModel):
    value: str


@pytest.mark.asyncio
async def test_returns_payload_on_first_success(mocker):
    inner = mocker.patch(
        "finwiz.infrastructure.resilience.perplexity_retry.perplexity_structured",
        new=mocker.AsyncMock(return_value=_Payload(value="ok")),
    )
    sleep = mocker.patch("finwiz.infrastructure.resilience.perplexity_retry.asyncio.sleep", new=mocker.AsyncMock())

    result = await perplexity_with_retry(prompt="p", schema=_Payload, system="s")

    assert result == _Payload(value="ok")
    assert inner.await_count == 1
    assert sleep.await_count == 0


@pytest.mark.asyncio
async def test_retries_until_success_and_backs_off(mocker):
    # The wrapper delegates backoff math to PerplexityFallbackManager.calculate_backoff_delay
    # (src/finwiz/tools/perplexity_errors.py), which jitters via `random.random()` inside its
    # own local `import random` -- not `random.uniform`. Patching the real `random.random` to
    # 0.5 zeros the +/-25% jitter term (2 * 0.5 - 1 == 0), leaving pure base_delay * 2**attempt.
    inner = mocker.patch(
        "finwiz.infrastructure.resilience.perplexity_retry.perplexity_structured",
        new=mocker.AsyncMock(side_effect=[None, None, _Payload(value="late")]),
    )
    sleep = mocker.patch("finwiz.infrastructure.resilience.perplexity_retry.asyncio.sleep", new=mocker.AsyncMock())
    mocker.patch("random.random", return_value=0.5)

    result = await perplexity_with_retry(prompt="p", schema=_Payload, system="s", base_delay=2.0)

    assert result == _Payload(value="late")
    assert inner.await_count == 3
    assert [c.args[0] for c in sleep.await_args_list] == [2.0, 4.0]


@pytest.mark.asyncio
async def test_gives_up_after_max_attempts(mocker):
    inner = mocker.patch(
        "finwiz.infrastructure.resilience.perplexity_retry.perplexity_structured",
        new=mocker.AsyncMock(return_value=None),
    )
    mocker.patch("finwiz.infrastructure.resilience.perplexity_retry.asyncio.sleep", new=mocker.AsyncMock())

    result = await perplexity_with_retry(prompt="p", schema=_Payload, system="s", max_attempts=3)

    assert result is None
    assert inner.await_count == 3


@pytest.mark.asyncio
async def test_missing_api_key_fails_fast_without_retrying(mocker, monkeypatch):
    monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
    monkeypatch.delenv("PPLX_API_KEY", raising=False)
    inner = mocker.patch(
        "finwiz.infrastructure.resilience.perplexity_retry.perplexity_structured",
        new=mocker.AsyncMock(return_value=None),
    )

    result = await perplexity_with_retry(prompt="p", schema=_Payload, system="s")

    assert result is None
    assert inner.await_count == 0


def test_semaphore_is_a_process_singleton():
    assert get_perplexity_semaphore() is get_perplexity_semaphore()
    assert isinstance(get_perplexity_semaphore(), asyncio.Semaphore)
