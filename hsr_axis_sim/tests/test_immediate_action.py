import pytest

from hsr_axis_sim.sim import Action, AdvanceAction, BattleState, ImmediateAction, Unit


def test_immediate_action_sets_current_av_to_zero():
    unit = Unit("ally", "Ally", "ally", 100, current_av=140)
    state = BattleState(units=[unit])
    action = Action(
        id="immediate",
        name="Immediate",
        actor_id="ally",
        effects=[ImmediateAction()],
        ends_turn=False,
    )

    action.execute(state)

    assert unit.current_av == pytest.approx(0, abs=1e-6)


def test_immediate_action_is_not_same_as_100_percent_advance_above_base_av():
    immediate_unit = Unit("immediate", "Immediate", "ally", 100, current_av=140)
    advance_unit = Unit("advance", "Advance", "ally", 100, current_av=140)
    immediate_state = BattleState(units=[immediate_unit])
    advance_state = BattleState(units=[advance_unit])

    Action(
        id="immediate",
        name="Immediate",
        actor_id="immediate",
        effects=[ImmediateAction()],
        ends_turn=False,
    ).execute(immediate_state)
    Action(
        id="advance",
        name="Advance",
        actor_id="advance",
        effects=[AdvanceAction(percent=1)],
        ends_turn=False,
    ).execute(advance_state)

    assert immediate_unit.current_av == pytest.approx(0, abs=1e-6)
    assert advance_unit.current_av == pytest.approx(40, abs=1e-6)

