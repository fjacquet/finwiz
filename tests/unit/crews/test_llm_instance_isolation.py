"""Each crew must own its LLM object, or CrewAI's per-LLM token counter bleeds across crews.

CrewAI accumulates token usage on the LLM instance (``BaseLLM._token_usage``,
``+=`` on every request, never reset by ``kickoff``) and reports it through
``Crew.calculate_usage_metrics`` as if it were this crew's usage. When two crews
share one LLM object, each kickoff reports the running total of every crew that
used the object before it. The 2026-09-05 run summed those running totals into
2 080 "calls" for ~65 real requests — a 32x overstatement that made crypto look
3.4x more expensive than stocks. It was an artifact of record ordering.
"""

from __future__ import annotations

import pytest

from finwiz.crews.deep_analysis.deep_analysis import DeepAnalysisCrew


@pytest.fixture(autouse=True)
def _keys(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-placeholder")
    monkeypatch.setenv("SERPER_API_KEY", "x")


class TestLLMInstanceIsolation:
    def test_two_crews_do_not_share_an_llm_object(self) -> None:
        a = DeepAnalysisCrew().asset_analyst().llm
        b = DeepAnalysisCrew().asset_analyst().llm
        assert a is not b, "two crews share one LLM object; CrewAI's token counter will bleed across them"

    def test_usage_recorded_on_one_crew_is_invisible_to_another(self) -> None:
        first, second = DeepAnalysisCrew(), DeepAnalysisCrew()
        llm_first = first.asset_analyst().llm

        # Simulate one request landing on the first crew's LLM, the way CrewAI does.
        llm_first._track_token_usage_internal({"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120})

        assert second.crew().calculate_usage_metrics().successful_requests == 0
        assert first.crew().calculate_usage_metrics().successful_requests == 1
