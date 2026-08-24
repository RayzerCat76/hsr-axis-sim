import pytest

from hsr_axis_sim.sim import Action, BattleState, ChangeSpeed, Unit


def test_speed_increase_reduces_remaining_current_av():
    unit = Unit("ally", "Ally", "ally", 100, current_av=50)
    state = BattleState(units=[unit])
    action = Action(
        id="speed_up",
        name="Speed Up",
        actor_id="ally",
        effects=[ChangeSpeed(new_speed=200)],
        ends_turn=False,
    )

    action.execute(state)

    assert unit.current_av == pytest.approx(25, abs=1e-6)


def test_speed_decrease_increases_remaining_current_av():
    unit = Unit("ally", "Ally", "ally", 200, current_av=25)
    state = BattleState(units=[unit])
    action = Action(
        id="speed_down",
        name="Speed Down",
        actor_id="ally",
        effects=[ChangeSpeed(new_speed=100)],
        ends_turn=False,
    )

    action.execute(state)

    assert unit.current_av == pytest.approx(50, abs=1e-6)


def test_base_av_updates_after_speed_changes():
    unit = Unit("ally", "Ally", "ally", 100, current_av=50)
    state = BattleState(units=[unit])
    action = Action(
        id="speed_up",
        name="Speed Up",
        actor_id="ally",
        effects=[ChangeSpeed(new_speed=125)],
        ends_turn=False,
    )

    action.execute(state)

    assert unit.speed == pytest.approx(125, abs=1e-6)
    assert unit.base_av == pytest.approx(80, abs=1e-6)

