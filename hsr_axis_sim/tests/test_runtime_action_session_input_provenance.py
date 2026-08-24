import pytest

from hsr_axis_sim.runtime_action_sessions import (
    ExplicitActionCaptureStep,
    RuntimeActionSessionInputError,
)
from hsr_axis_sim.sim.action import Action


def test_action_id_and_actor_id_must_be_nonempty_before_session_execution():
    with pytest.raises(RuntimeActionSessionInputError, match="action.id"):
        ExplicitActionCaptureStep(Action("", "Unnamed", "actor", ends_turn=False))
    with pytest.raises(RuntimeActionSessionInputError, match="action.actor_id"):
        ExplicitActionCaptureStep(Action("action", "Action", "", ends_turn=False))
