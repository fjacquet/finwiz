"""
Tests guarding the always-runs invariant for Phase 4 (A+ Investment Discovery).

History:
- v0.2.x had an `INVESTMENT_DISCOVERY_ENABLED` env-var kill switch that gated
  Phase 4 behind an opt-in. Without discovery, alternatives matching produced
  the "no alternatives found" warning class for every holding — same shape as
  the v0.3.0 deep-analysis silent-success bug.
- The kill switch was removed: discovery now ALWAYS runs.
- The `discovery_enabled` field on `FinwizState` is preserved as legitimate
  CrewAI flow-input API (callers may pass `flow.kickoff(inputs={...})`); it is
  no longer consulted as a gate.

These tests pin the invariants:
1. The state field still exists for API stability.
2. `app_initializer.kickoff()` does NOT read any env-var toggle and forwards
   no kickoff inputs — discovery runs unconditionally.
"""

from __future__ import annotations

from finwiz.flow_state_models import FinwizState


class TestDiscoveryStateField:
    """`discovery_enabled` field exists on FinwizState for API stability."""

    def test_default_is_false(self) -> None:
        state = FinwizState()
        assert state.discovery_enabled is False

    def test_can_be_set_via_constructor(self) -> None:
        # The field accepts the kwarg even though it no longer gates behavior.
        state = FinwizState(discovery_enabled=True)
        assert state.discovery_enabled is True


class TestAppInitializerDoesNotForwardKillSwitch:
    """`app_initializer.kickoff()` runs discovery unconditionally — no inputs."""

    def test_kickoff_called_without_inputs(self, mocker) -> None:
        """The kill switch was removed, so flow.kickoff() takes no inputs."""
        mocker.patch("finwiz.validation.validate_template_variables_at_startup")
        mocker.patch("finwiz.core.app_initializer.initialize_configuration")
        mocker.patch("finwiz.core.app_initializer.initialize_environment")
        mocker.patch("finwiz.core.app_initializer.logging.shutdown")
        mocker.patch("finwiz.core.app_initializer.os._exit")
        flow_cls_mock = mocker.patch("finwiz.core.app_initializer.FinwizFlow")

        from finwiz.core.app_initializer import kickoff

        kickoff()

        # Asserts kickoff() was called with no positional args and no keyword args
        # (discovery is always-on, so no inputs are forwarded).
        flow_cls_mock.return_value.kickoff.assert_called_once_with()
