"""The process exit code is the gate's verdict, not a constant 0.

The flow here is a real ``crewai`` ``Flow[FinwizState]``, not a hand-written
stand-in. That matters more than it looks: ``Flow.__init__`` validates the state
argument into a *copy*, so the verdict the gate writes never appears on the
object the caller passed in. A fake that stores the caller's object by reference
passes these cases no matter which of the two ``kickoff()`` reads -- which is how
the exit code came to be read from the one nothing ever writes.
"""

from __future__ import annotations

import pytest
from crewai.flow.flow import Flow

from finwiz.core import app_initializer
from finwiz.flow_state import FinwizState


def _gate_flow(verdict: str | None) -> type[Flow[FinwizState]]:
    """A real Flow whose kickoff() leaves a verdict on state, like the real gate does.

    ``kickoff`` is overridden rather than driven through ``@start()`` so the test
    exercises crewai's state handling without its crew machinery.
    """

    class _GateFlow(Flow[FinwizState]):
        def kickoff(self, *args, **kwargs) -> None:
            self.state.gate_verdict = verdict

    return _GateFlow


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
        mocker.patch.object(app_initializer, "FinwizFlow", _gate_flow(verdict))

        app_initializer.kickoff()

        quiet_startup.assert_called_once_with(code)


class TestTheFlowCopiesItsState:
    def test_the_flow_does_not_share_the_state_object_it_was_given(self) -> None:
        """Pins the library behaviour the exit code depends on.

        If a future crewai starts sharing the object, this fails loudly and
        whoever reads it can decide -- rather than the exit code quietly going
        back to being read from the wrong place.
        """
        outer = FinwizState()
        flow = _gate_flow("PASS")(state=outer)

        assert flow.state is not outer
        flow.kickoff()
        assert flow.state.gate_verdict == "PASS"
        assert outer.gate_verdict is None, "the caller's object is never written to; the exit code must not be read from it"
