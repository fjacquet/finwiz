"""The process exit code is the gate's verdict, not a constant 0."""

from __future__ import annotations

import pytest

from finwiz.core import app_initializer


class _FakeFlow:
    """Stands in for FinwizFlow: kickoff() leaves a verdict on state, like the real gate does."""

    verdict: str | None = "FAIL"

    def __init__(self, state) -> None:
        self.state = state

    def kickoff(self) -> None:
        self.state.gate_verdict = self.verdict


@pytest.fixture()
def quiet_startup(mocker):
    mocker.patch("finwiz.validation.validate_template_variables_at_startup")
    mocker.patch.object(app_initializer, "initialize_configuration")
    mocker.patch.object(app_initializer, "initialize_environment")
    mocker.patch.object(app_initializer.logging, "shutdown")
    return mocker.patch.object(app_initializer.os, "_exit")


class TestExitCodeFollowsTheVerdict:
    @pytest.mark.parametrize(("verdict", "code"), [("PASS", 0), ("WARN", 0), ("FAIL", 1), ("ERROR", 2), (None, 2)])
    def test_exit_code(self, mocker, quiet_startup, verdict, code) -> None:
        _FakeFlow.verdict = verdict
        mocker.patch.object(app_initializer, "FinwizFlow", _FakeFlow)

        app_initializer.kickoff()

        quiet_startup.assert_called_once_with(code)
