"""
Tests for Fix 2: discovery toggle via CrewAI-native mechanisms.

Covers:
- FinwizState.discovery_enabled field exists and defaults to False.
- app_initializer.kickoff() forwards INVESTMENT_DISCOVERY_ENABLED env var
  as a flow input (CrewAI canonical pattern), not via argparse.
"""

from __future__ import annotations

import pytest

from finwiz.flow_state_models import FinwizState


class TestDiscoveryStateField:
    """FinwizState must carry a discovery_enabled boolean for CrewAI flow inputs."""

    def test_default_is_false(self):
        state = FinwizState()
        assert state.discovery_enabled is False

    def test_can_be_set_via_constructor(self):
        state = FinwizState(discovery_enabled=True)
        assert state.discovery_enabled is True


class TestAppInitializerForwardsEnvVarAsFlowInput:
    """app_initializer.kickoff() must forward env var to flow.kickoff(inputs=...)."""

    @pytest.fixture
    def patched_kickoff(self, mocker):
        """Patch every expensive step in app_initializer.kickoff()."""
        mocker.patch("finwiz.validation.validate_template_variables_at_startup")
        mocker.patch("finwiz.core.app_initializer.initialize_configuration")
        mocker.patch("finwiz.core.app_initializer.initialize_environment")
        mocker.patch("finwiz.core.app_initializer.logging.shutdown")
        mocker.patch("finwiz.core.app_initializer.os._exit")
        flow_cls_mock = mocker.patch("finwiz.core.app_initializer.FinwizFlow")
        return flow_cls_mock.return_value

    def test_forwards_true_when_env_var_set(self, mocker, patched_kickoff):
        mocker.patch.dict("os.environ", {"INVESTMENT_DISCOVERY_ENABLED": "true"}, clear=False)
        from finwiz.core.app_initializer import kickoff

        kickoff()

        patched_kickoff.kickoff.assert_called_once_with(inputs={"discovery_enabled": True})

    def test_forwards_false_when_env_var_absent(self, mocker, patched_kickoff):
        mocker.patch.dict("os.environ", {}, clear=False)
        mocker.patch.dict("os.environ", {"INVESTMENT_DISCOVERY_ENABLED": ""}, clear=False)
        from finwiz.core.app_initializer import kickoff

        kickoff()

        patched_kickoff.kickoff.assert_called_once_with(inputs={"discovery_enabled": False})

    def test_env_var_is_case_insensitive(self, mocker, patched_kickoff):
        mocker.patch.dict("os.environ", {"INVESTMENT_DISCOVERY_ENABLED": "TRUE"}, clear=False)
        from finwiz.core.app_initializer import kickoff

        kickoff()

        patched_kickoff.kickoff.assert_called_once_with(inputs={"discovery_enabled": True})
