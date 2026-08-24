import pytest

from hsr_axis_sim.sim import (
    Action,
    BattleState,
    ConsumeEnergy,
    ConsumeSkillPoint,
    GainEnergy,
    GainSkillPoint,
    Timeline,
    TurnContext,
    Unit,
)


def test_speed_100_gives_base_av_100():
    unit = Unit(id="ally", name="Ally", team="ally", base_speed=100)

    assert unit.base_av == pytest.approx(100, abs=1e-6)


def test_speed_134_gives_base_av_about_74_6269():
    unit = Unit(id="ally", name="Ally", team="ally", base_speed=134)

    assert unit.base_av == pytest.approx(74.6269, abs=1e-4)


def test_lowest_current_av_actor_acts_first():
    ally_fast = Unit("ally_fast", "Ally Fast", "ally", 100, current_av=30)
    ally_slow = Unit("ally_slow", "Ally Slow", "ally", 100, current_av=80)
    enemy = Unit("enemy", "Enemy", "enemy", 100, current_av=60)
    state = BattleState(units=[ally_slow, enemy, ally_fast])

    turn = Timeline.next_turn(state)

    assert turn.actor_id == "ally_fast"


def test_global_av_advances_and_all_units_are_reduced_by_elapsed_av():
    ally_fast = Unit("ally_fast", "Ally Fast", "ally", 100, current_av=30)
    ally_slow = Unit("ally_slow", "Ally Slow", "ally", 100, current_av=80)
    enemy = Unit("enemy", "Enemy", "enemy", 100, current_av=60)
    state = BattleState(units=[ally_fast, ally_slow, enemy])

    Timeline.next_turn(state)

    assert state.global_av == pytest.approx(30, abs=1e-6)
    assert ally_fast.current_av == pytest.approx(0, abs=1e-6)
    assert ally_slow.current_av == pytest.approx(50, abs=1e-6)
    assert enemy.current_av == pytest.approx(30, abs=1e-6)


def test_actor_current_av_is_reset_after_normal_turn_end():
    ally_fast = Unit("ally_fast", "Ally Fast", "ally", 100, current_av=30)
    enemy = Unit("enemy", "Enemy", "enemy", 100, current_av=60)
    state = BattleState(units=[ally_fast, enemy])
    turn = Timeline.next_turn(state)

    Timeline.end_turn(state, turn)

    assert ally_fast.current_av == pytest.approx(100, abs=1e-6)


def test_resource_gains_clamp_and_consumption_deducts_available_resources():
    actor = Unit("ally", "Ally", "ally", 100, energy=90, max_energy=100)
    state = BattleState(units=[actor], skill_points=1, max_skill_points=3)
    action = Action(
        id="resource_action",
        name="Resource Action",
        actor_id="ally",
        effects=[
            GainEnergy(amount=20),
            ConsumeEnergy(amount=35),
            GainSkillPoint(amount=5),
            ConsumeSkillPoint(amount=2),
        ],
        ends_turn=False,
    )

    action.execute(state)

    assert actor.energy == pytest.approx(65, abs=1e-6)
    assert state.skill_points == 1


def test_action_actor_must_match_provided_turn_context():
    actor = Unit("ally", "Ally", "ally", 100)
    other = Unit("other", "Other", "ally", 100)
    state = BattleState(units=[actor, other])
    action = Action(id="wrong_actor", name="Wrong Actor", actor_id="other")
    turn_context = TurnContext(actor_id="ally")

    with pytest.raises(ValueError, match="actor_id must match"):
        action.execute(state, turn_context)


def test_consume_skill_point_raises_when_insufficient():
    actor = Unit("ally", "Ally", "ally", 100)
    state = BattleState(units=[actor], skill_points=0)
    action = Action(
        id="spend_sp",
        name="Spend SP",
        actor_id="ally",
        effects=[ConsumeSkillPoint(amount=1)],
        ends_turn=False,
    )

    with pytest.raises(ValueError, match="Insufficient skill points"):
        action.execute(state)

    assert state.skill_points == 0


def test_consume_energy_raises_when_insufficient():
    actor = Unit("ally", "Ally", "ally", 100, energy=10)
    state = BattleState(units=[actor])
    action = Action(
        id="spend_energy",
        name="Spend Energy",
        actor_id="ally",
        effects=[ConsumeEnergy(amount=20)],
        ends_turn=False,
    )

    with pytest.raises(ValueError, match="insufficient energy"):
        action.execute(state)

    assert actor.energy == pytest.approx(10, abs=1e-6)
