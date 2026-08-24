import pytest

from hsr_axis_sim.sim import Action, AdvanceAction, BattleState, DelayAction, Unit


def test_50_percent_advance_subtracts_half_base_av():
    unit = Unit("ally", "Ally", "ally", 100, current_av=80)
    state = BattleState(units=[unit])
    action = Action(
        id="advance",
        name="Advance",
        actor_id="ally",
        effects=[AdvanceAction(percent=0.5)],
        ends_turn=False,
    )

    action.execute(state)

    assert unit.current_av == pytest.approx(30, abs=1e-6)


def test_100_percent_advance_does_not_go_below_zero():
    unit = Unit("ally", "Ally", "ally", 100, current_av=40)
    state = BattleState(units=[unit])
    action = Action(
        id="advance",
        name="Advance",
        actor_id="ally",
        effects=[AdvanceAction(percent=1)],
        ends_turn=False,
    )

    action.execute(state)

    assert unit.current_av == pytest.approx(0, abs=1e-6)


def test_action_delay_adds_base_av_times_percent():
    unit = Unit("ally", "Ally", "ally", 100, current_av=40)
    state = BattleState(units=[unit])
    action = Action(
        id="delay",
        name="Delay",
        actor_id="ally",
        effects=[DelayAction(percent=0.25)],
        ends_turn=False,
    )

    action.execute(state)

    assert unit.current_av == pytest.approx(65, abs=1e-6)

