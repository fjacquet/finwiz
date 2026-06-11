"""The per-holding timeout must always exceed the crew budget by the retry headroom.

Root cause 2026-06-11: inner crew timeout and outer holding timeout read the same
env var, so the @stage retry after a hung LLM call could never complete — holdings
were discarded with their quantitative scores already computed.
"""

import importlib

import finwiz.infrastructure.resilience.crew_execution as crew_execution_mod
import finwiz.orchestrators.deep_analysis_orchestrator as dao_mod


def _get_effective_holding_timeout(monkeypatch, holding_timeout_val: str | None = None) -> int:
    """Helper: derive the effective per-holding timeout exactly as the orchestrator does.

    Delegates to the module-level helper added for testability.
    """
    if holding_timeout_val is not None:
        monkeypatch.setenv("FINWIZ_HOLDING_TIMEOUT", holding_timeout_val)
    else:
        monkeypatch.delenv("FINWIZ_HOLDING_TIMEOUT", raising=False)

    # Reload so CREW_TIMEOUT picks up the (possibly patched) FINWIZ_CREW_TIMEOUT.
    importlib.reload(crew_execution_mod)

    return dao_mod._effective_holding_timeout()


class TestTimeoutHeadroom:
    """The per-holding timeout must provide at least RETRY_HEADROOM_S above CREW_TIMEOUT."""

    def test_holding_timeout_exceeds_crew_budget_when_env_collides(self, monkeypatch):
        """When FINWIZ_HOLDING_TIMEOUT is set too low (≤ CREW_TIMEOUT), the orchestrator
        must auto-raise the effective per-holding timeout so the @stage retry has room."""
        # Simulate the pre-fix bug: operator sets both timeouts to the same value.
        monkeypatch.setenv("FINWIZ_HOLDING_TIMEOUT", "600")
        monkeypatch.setenv("FINWIZ_CREW_TIMEOUT", "600")

        importlib.reload(crew_execution_mod)
        effective = dao_mod._effective_holding_timeout()

        assert effective >= crew_execution_mod.CREW_TIMEOUT + dao_mod.RETRY_HEADROOM_S, (
            f"effective={effective} must be >= CREW_TIMEOUT ({crew_execution_mod.CREW_TIMEOUT}) + RETRY_HEADROOM_S ({dao_mod.RETRY_HEADROOM_S})"
        )

    def test_crew_timeout_reads_its_own_var(self, monkeypatch):
        """FINWIZ_CREW_TIMEOUT controls the inner crew attempt budget independently."""
        monkeypatch.setenv("FINWIZ_CREW_TIMEOUT", "123")
        importlib.reload(crew_execution_mod)
        assert crew_execution_mod.CREW_TIMEOUT == 123

    def test_defaults_give_headroom(self, monkeypatch):
        """With neither timeout var set the defaults must provide retry headroom.

        Default FINWIZ_HOLDING_TIMEOUT=900, default FINWIZ_CREW_TIMEOUT=600.
        900 >= 600 + 300 is exactly met; any change that breaks this will fail.
        """
        monkeypatch.delenv("FINWIZ_HOLDING_TIMEOUT", raising=False)
        monkeypatch.delenv("FINWIZ_CREW_TIMEOUT", raising=False)

        importlib.reload(crew_execution_mod)
        effective = dao_mod._effective_holding_timeout()

        assert effective >= crew_execution_mod.CREW_TIMEOUT + dao_mod.RETRY_HEADROOM_S, (
            f"Default effective={effective} must be >= default CREW_TIMEOUT ({crew_execution_mod.CREW_TIMEOUT}) + RETRY_HEADROOM_S ({dao_mod.RETRY_HEADROOM_S})"
        )
