"""The gate reads three new state fields; the freshness summary must be one of them."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

from finwiz.flow_state_models import FinwizState


class TestRunGateStateFields:
    def test_fields_exist_and_default_to_none(self) -> None:
        s = FinwizState()
        assert s.fact_pack_freshness is None
        assert s.run_summary is None
        assert s.gate_verdict is None


class TestFreshnessIsPersistedNotJustLogged:
    def test_summary_lands_on_state_as_a_plain_dict(self) -> None:
        from finwiz.orchestrators.deep_analysis_orchestrator import DeepAnalysisOrchestrator

        state = FinwizState()
        orch = DeepAnalysisOrchestrator(state=state)
        fact_pack = SimpleNamespace(freshness="stale", fetched_at=datetime(2026, 8, 17, tzinfo=UTC))
        orch._enriched_analyses = {"E": SimpleNamespace(qualitative=SimpleNamespace(fact_pack=fact_pack))}

        orch._record_fact_pack_freshness()

        assert state.fact_pack_freshness == {
            "total": 1,
            "fresh": 0,
            "recent": 0,
            "stale": 1,
            "missing": 0,
            "oldest_stale_fetched_at": datetime(2026, 8, 17, tzinfo=UTC),
        }
