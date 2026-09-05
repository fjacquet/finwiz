"""Tests for LLM cost tracking in TokenMonitorCallback."""

import logging
from types import SimpleNamespace

import pytest

from finwiz.infrastructure.monitoring.litellm_callback import (
    TokenMonitorCallback,
    clear_crew_context,
    set_crew_context,
)


def _usage(prompt: int = 100, completion: int = 50, requests: int = 1) -> SimpleNamespace:
    """Build a CrewAI-like UsageMetrics object."""
    return SimpleNamespace(prompt_tokens=prompt, completion_tokens=completion, successful_requests=requests)


class TestTokenMonitorCostTracking:
    def _make_response(self, mocker, prompt_tokens: int = 100, completion_tokens: int = 50):
        usage = mocker.MagicMock()
        usage.prompt_tokens = prompt_tokens
        usage.completion_tokens = completion_tokens
        resp = mocker.MagicMock()
        resp.usage = usage
        return resp

    def test_cost_accumulation(self, mocker):
        mocker.patch("litellm.completion_cost", return_value=0.005)
        cb = TokenMonitorCallback()
        cb.call_count = 1
        resp = self._make_response(mocker)
        cb.log_success_event({"model": "gpt-4"}, resp, 0.0, 1.0)
        assert cb.total_cost == pytest.approx(0.005)

    def test_crew_attribution(self, mocker):
        mocker.patch("litellm.completion_cost", return_value=0.01)
        cb = TokenMonitorCallback()
        cb.call_count = 1

        set_crew_context("stock_crew")
        cb.log_success_event({"model": "gpt-4"}, self._make_response(mocker), 0.0, 1.0)
        clear_crew_context()

        assert "stock_crew" in cb.crew_costs
        assert cb.crew_costs["stock_crew"] == pytest.approx(0.01)
        assert cb.crew_calls["stock_crew"] == 1

    def test_multiple_crews(self, mocker):
        mocker.patch("litellm.completion_cost", return_value=0.01)
        cb = TokenMonitorCallback()
        cb.call_count = 1

        set_crew_context("stock_crew")
        cb.log_success_event({"model": "gpt-4"}, self._make_response(mocker), 0.0, 1.0)

        set_crew_context("etf_crew")
        cb.call_count = 2
        cb.log_success_event({"model": "gpt-4"}, self._make_response(mocker), 0.0, 1.0)
        clear_crew_context()

        assert cb.total_cost == pytest.approx(0.02)
        assert len(cb.crew_costs) == 2

    def test_cost_summary_structure(self, mocker):
        mocker.patch("litellm.completion_cost", return_value=0.005)
        cb = TokenMonitorCallback()
        cb.call_count = 1
        set_crew_context("deep_analysis")
        cb.log_success_event({"model": "gpt-4"}, self._make_response(mocker, 200, 100), 0.0, 1.0)
        clear_crew_context()

        summary = cb.get_cost_summary()
        assert "total_cost" in summary
        assert "per_crew" in summary
        assert "call_count" in summary
        assert summary["per_crew"]["deep_analysis"]["tokens"]["prompt"] == 200
        assert summary["per_crew"]["deep_analysis"]["tokens"]["completion"] == 100

    def test_cost_fallback_on_error(self, mocker):
        mocker.patch("litellm.completion_cost", side_effect=Exception("no pricing"))
        cb = TokenMonitorCallback()
        cb.call_count = 1
        cb.log_success_event({"model": "gpt-4"}, self._make_response(mocker), 0.0, 1.0)
        # Cost should be 0 on error, not raise
        assert cb.total_cost == 0.0

    def test_log_cost_summary_no_error(self, mocker):
        mocker.patch("litellm.completion_cost", return_value=0.01)
        cb = TokenMonitorCallback()
        cb.call_count = 1
        cb.log_success_event({"model": "gpt-4"}, self._make_response(mocker), 0.0, 1.0)
        cb.log_cost_summary()  # Should not raise

    def test_log_cost_summary_empty(self):
        cb = TokenMonitorCallback()
        cb.log_cost_summary()  # Should not raise with no calls

    def test_call_count_increments_per_event(self, mocker):
        # Regression: call_count was never incremented, so get_cost_summary()
        # always reported 0 calls and the per-call log printed "#0".
        mocker.patch("litellm.completion_cost", return_value=0.005)
        cb = TokenMonitorCallback()
        assert cb.call_count == 0

        cb.log_success_event({"model": "gpt-4"}, self._make_response(mocker), 0.0, 1.0)
        cb.log_success_event({"model": "gpt-4"}, self._make_response(mocker), 0.0, 1.0)

        assert cb.call_count == 2
        assert cb.get_cost_summary()["call_count"] == 2

    def test_token_tracking_per_crew(self, mocker):
        mocker.patch("litellm.completion_cost", return_value=0.0)
        cb = TokenMonitorCallback()
        cb.call_count = 1

        set_crew_context("crew_a")
        cb.log_success_event({"model": "gpt-4"}, self._make_response(mocker, 100, 50), 0.0, 1.0)
        cb.call_count = 2
        cb.log_success_event({"model": "gpt-4"}, self._make_response(mocker, 200, 75), 0.0, 1.0)
        clear_crew_context()

        assert cb.crew_tokens["crew_a"]["prompt"] == 300
        assert cb.crew_tokens["crew_a"]["completion"] == 125


class TestRecordUsage:
    """The CrewAI-usage_metrics source of truth (record_usage)."""

    def test_accumulates_tokens_calls_and_cost(self, mocker):
        mocker.patch("litellm.cost_per_token", return_value=(0.001, 0.002))
        cb = TokenMonitorCallback()

        cb.record_usage("deep_analysis_stock", _usage(200, 100, requests=3), model="openai/gpt-4o-mini")

        assert cb.call_count == 3
        assert cb.crew_calls["deep_analysis_stock"] == 3
        assert cb.crew_tokens["deep_analysis_stock"] == {"prompt": 200, "completion": 100}
        assert cb.total_cost == pytest.approx(0.003)
        assert cb.crew_cost_known["deep_analysis_stock"] is True

    def test_calls_default_to_one_when_requests_missing(self, mocker):
        mocker.patch("litellm.cost_per_token", return_value=(0.0, 0.0))
        cb = TokenMonitorCallback()
        cb.record_usage("c", _usage(10, 5, requests=0), model="openai/gpt-4o-mini")
        assert cb.call_count == 1

    def test_empty_usage_is_noop(self, mocker):
        mocker.patch("litellm.cost_per_token", return_value=(0.0, 0.0))
        cb = TokenMonitorCallback()
        cb.record_usage("c", _usage(0, 0, requests=0), model="openai/gpt-4o-mini")
        assert cb.call_count == 0
        assert cb.crew_calls == {}

    def test_unpriced_model_counts_tokens_but_marks_cost_unknown(self, mocker):
        mocker.patch("litellm.cost_per_token", side_effect=Exception("no pricing for model"))
        cb = TokenMonitorCallback()

        cb.record_usage("weird_crew", _usage(100, 50, requests=1), model="vendor/unknown-model")

        assert cb.crew_tokens["weird_crew"] == {"prompt": 100, "completion": 50}
        assert cb.crew_calls["weird_crew"] == 1
        assert cb.total_cost == 0.0  # no fabricated cost
        assert cb.crew_cost_known["weird_crew"] is False

    def test_summary_exposes_cost_known(self, mocker):
        mocker.patch("litellm.cost_per_token", return_value=(0.001, 0.001))
        cb = TokenMonitorCallback()
        cb.record_usage("c", _usage(), model="openai/gpt-4o-mini")
        per_crew = cb.get_cost_summary()["per_crew"]
        assert per_crew["c"]["cost_known"] is True


class TestHonestSummary:
    """log_cost_summary must never claim 'No LLM calls made'."""

    def test_empty_run_does_not_assert_zero_calls(self, caplog):
        cb = TokenMonitorCallback()
        caplog.set_level(logging.INFO)
        cb.log_cost_summary()
        msgs = " ".join(r.message for r in caplog.records)
        assert "No LLM calls made" not in msgs
        assert "no crew LLM usage measured" in msgs

    def test_unpriced_crew_shows_na_not_zero(self, mocker, caplog):
        mocker.patch("litellm.cost_per_token", side_effect=Exception("no pricing"))
        cb = TokenMonitorCallback()
        cb.record_usage("weird_crew", _usage(100, 50, requests=1), model="vendor/unknown")
        caplog.set_level(logging.INFO)
        cb.log_cost_summary()
        msgs = " ".join(r.message for r in caplog.records)
        assert "cost n/a" in msgs
        assert "estimated" in msgs


class TestOpenRouterPricingFallback:
    """OpenRouter ids are unpriced in litellm; the vendor-native id usually is not.

    `openrouter/google/gemini-3.7-flash` has no litellm price while
    `gemini/gemini-3.7-flash` does. Pricing through the native id is a proxy —
    OpenRouter's rate is not necessarily the vendor's — so it must be logged as
    one, and it must never be tried for vendors without a known native twin.
    """

    @staticmethod
    def _gemini_only(model: str, prompt_tokens: int, completion_tokens: int):
        if model.startswith("openrouter/"):
            raise Exception("no pricing for model")
        assert model == "gemini/gemini-3.7-flash"
        return (0.001, 0.002)

    def test_openrouter_google_model_is_priced_through_the_gemini_id(self, mocker):
        spy = mocker.patch("litellm.cost_per_token", side_effect=self._gemini_only)
        cb = TokenMonitorCallback()

        cb.record_usage("deep_analysis_stock", _usage(100, 50), model="openrouter/google/gemini-3.7-flash")

        assert cb.crew_cost_known["deep_analysis_stock"] is True
        assert cb.total_cost == pytest.approx(0.003)
        assert [c.kwargs["model"] for c in spy.call_args_list] == ["openrouter/google/gemini-3.7-flash", "gemini/gemini-3.7-flash"]

    def test_proxy_pricing_is_logged_once_per_model(self, mocker, caplog):
        mocker.patch("litellm.cost_per_token", side_effect=self._gemini_only)
        cb = TokenMonitorCallback()

        with caplog.at_level(logging.INFO):
            cb.record_usage("a", _usage(), model="openrouter/google/gemini-3.7-flash")
            cb.record_usage("b", _usage(), model="openrouter/google/gemini-3.7-flash")

        proxy_lines = [r for r in caplog.records if "gemini/gemini-3.7-flash" in r.message and "estimate" in r.message]
        assert len(proxy_lines) == 1

    def test_no_fallback_for_vendors_without_a_native_twin(self, mocker):
        spy = mocker.patch("litellm.cost_per_token", side_effect=Exception("no pricing for model"))
        cb = TokenMonitorCallback()

        cb.record_usage("x", _usage(), model="openrouter/z-ai/glm-5.2")

        assert cb.crew_cost_known["x"] is False
        assert spy.call_count == 1
