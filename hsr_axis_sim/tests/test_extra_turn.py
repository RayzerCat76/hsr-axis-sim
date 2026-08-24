import pytest

from hsr_axis_sim.sim import (
    Action,
    AdvanceAction,
    BattleState,
    DoesNotEndTurn,
    GrantExtraTurn,
    ImmediateAction,
    Timeline,
    Unit,
)


def test_extra_turns_are_taken_before_normal_timeline_actors():
    actor = Unit("ally", "Ally", "ally", 100, current_av=80)
    enemy = Unit("enemy", "Enemy", "enemy", 100, current_av=10)
    state = BattleState(units=[actor, enemy], extra_turn_stack=["ally"])

    turn = Timeline.next_turn(state)

    assert turn.actor_id == "ally"
    assert turn.is_extra_turn is True


def test_extra_turns_do_not_advance_global_av():
    actor = Unit("ally", "Ally", "ally", 100, current_av=80)
    enemy = Unit("enemy", "Enemy", "enemy", 100, current_av=10)
    state = BattleState(units=[actor, enemy], extra_turn_stack=["ally"])

    Timeline.next_turn(state)

    assert state.global_av == pytest.approx(0, abs=1e-6)


def test_extra_turns_do_not_alter_original_normal_timeline_current_av():
    actor = Unit("ally", "Ally", "ally", 100, current_av=80)
    enemy = Unit("enemy", "Enemy", "enemy", 100, current_av=10)
    state = BattleState(units=[actor, enemy], extra_turn_stack=["ally"])

    turn = Timeline.next_turn(state)
    Timeline.end_turn(state, turn)

    assert actor.current_av == pytest.approx(80, abs=1e-6)
    assert enemy.current_av == pytest.approx(10, abs=1e-6)


def test_normal_turn_reset_still_works_after_extra_turn_stack_is_empty():
    actor = Unit("ally", "Ally", "ally", 100, current_av=80)
    enemy = Unit("enemy", "Enemy", "enemy", 100, current_av=10)
    state = BattleState(units=[actor, enemy], extra_turn_stack=["ally"])
    extra_turn = Timeline.next_turn(state)
    Timeline.end_turn(state, extra_turn)

    normal_turn = Timeline.next_turn(state)
    Timeline.end_turn(state, normal_turn)

    assert normal_turn.actor_id == "enemy"
    assert state.global_av == pytest.approx(10, abs=1e-6)
    assert enemy.current_av == pytest.approx(100, abs=1e-6)
    assert actor.current_av == pytest.approx(70, abs=1e-6)


def test_grant_extra_turn_uses_stack_without_moving_normal_timeline():
    actor = Unit("ally", "Ally", "ally", 100, current_av=80)
    state = BattleState(units=[actor])
    action = Action(
        id="grant_extra",
        name="Grant Extra",
        actor_id="ally",
        effects=[GrantExtraTurn()],
        ends_turn=False,
    )

    action.execute(state)
    turn = Timeline.next_turn(state)

    assert turn.actor_id == "ally"
    assert turn.is_extra_turn is True
    assert actor.current_av == pytest.approx(80, abs=1e-6)


def test_multiple_extra_turns_resolve_in_lifo_order():
    first = Unit("first", "First", "ally", 100, current_av=80)
    second = Unit("second", "Second", "ally", 100, current_av=70)
    third = Unit("third", "Third", "ally", 100, current_av=60)
    state = BattleState(
        units=[first, second, third],
        extra_turn_stack=["first", "second", "third"],
    )

    turns = [Timeline.next_turn(state).actor_id for _ in range(3)]

    assert turns == ["third", "second", "first"]
    assert state.global_av == pytest.approx(0, abs=1e-6)


def test_does_not_end_turn_keeps_context_open_and_does_not_reset_av():
    actor = Unit("ally", "Ally", "ally", 100, current_av=0)
    state = BattleState(units=[actor])
    turn = Timeline.next_turn(state)
    action = Action(
        id="continue_turn",
        name="Continue Turn",
        actor_id="ally",
        effects=[DoesNotEndTurn()],
    )

    context = action.execute(state, turn)

    assert context.should_end_turn is False
    assert context.actions_taken == ["continue_turn"]
    assert actor.current_av == pytest.approx(0, abs=1e-6)


def test_self_immediate_action_during_normal_turn_resets_after_turn_end():
    actor = Unit("ally", "Ally", "ally", 100, current_av=20)
    enemy = Unit("enemy", "Enemy", "enemy", 100, current_av=50)
    state = BattleState(units=[actor, enemy])
    turn = Timeline.next_turn(state)
    action = Action(
        id="self_immediate",
        name="Self Immediate",
        actor_id="ally",
        effects=[ImmediateAction()],
    )

    action.execute(state, turn)

    assert actor.current_av == pytest.approx(100, abs=1e-6)
    assert enemy.current_av == pytest.approx(30, abs=1e-6)


def test_self_advance_action_during_normal_turn_resets_after_turn_end():
    actor = Unit("ally", "Ally", "ally", 100, current_av=20)
    enemy = Unit("enemy", "Enemy", "enemy", 100, current_av=50)
    state = BattleState(units=[actor, enemy])
    turn = Timeline.next_turn(state)
    action = Action(
        id="self_advance",
        name="Self Advance",
        actor_id="ally",
        effects=[AdvanceAction(percent=0.5)],
    )

    action.execute(state, turn)

    assert actor.current_av == pytest.approx(100, abs=1e-6)
    assert enemy.current_av == pytest.approx(30, abs=1e-6)
