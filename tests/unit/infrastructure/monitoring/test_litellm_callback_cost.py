"""Tests for LLM cost tracking in TokenMonitorCallback."""

import pytest

from finwiz.infrastructure.monitoring.litellm_callback import (
    TokenMonitorCallback,
    clear_crew_context,
    set_crew_context,
)


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
