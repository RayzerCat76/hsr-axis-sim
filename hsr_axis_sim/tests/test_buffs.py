import pytest

from hsr_axis_sim.sim import (
    Action,
    AddBuff,
    AddDebuff,
    BattleState,
    DoesNotEndTurn,
    GrantExtraTurn,
    RemoveBuff,
    RemoveDebuff,
    Timeline,
    Unit,
)


def test_add_buff_stores_target_source_duration_and_stacks():
    actor = Unit("actor", "Actor", "ally", 100)
    target = Unit("target", "Target", "ally", 100)
    state = BattleState(units=[actor, target])
    action = Action(
        id="add_buff",
        name="Add Buff",
        actor_id="actor",
        target_ids=["target"],
        effects=[
            AddBuff(
                id="damage_boost",
                name="Damage Boost",
                duration_type="target_normal_turns",
                remaining_turns=2,
                stacks=1,
                max_stacks=3,
                data={"multiplier": 1.2},
            )
        ],
        ends_turn=False,
    )

    action.execute(state)

    buff = target.get_buff("damage_boost")
    assert buff is not None
    assert buff.target_id == "target"
    assert buff.source_id == "actor"
    assert buff.duration_type == "target_normal_turns"
    assert buff.remaining_turns == 2
    assert buff.stacks == 1
    assert buff.max_stacks == 3
    assert buff.data == {"multiplier": 1.2}


def test_reapplying_same_buff_refreshes_duration_and_stacks_to_max():
    actor = Unit("actor", "Actor", "ally", 100)
    target = Unit("target", "Target", "ally", 100)
    state = BattleState(units=[actor, target])
    action = Action(
        id="add_buff",
        name="Add Buff",
        actor_id="actor",
        target_ids=["target"],
        effects=[
            AddBuff(
                id="damage_boost",
                name="Damage Boost",
                duration_type="target_normal_turns",
                remaining_turns=1,
                stacks=1,
                max_stacks=2,
            )
        ],
        ends_turn=False,
    )
    action.execute(state)
    target.buffs["damage_boost"].remaining_turns = 0

    action.execute(state)
    action.execute(state)

    buff = target.buffs["damage_boost"]
    assert buff.remaining_turns == 1
    assert buff.stacks == 2


def test_remove_buff_removes_buff():
    actor = Unit("actor", "Actor", "ally", 100)
    target = Unit("target", "Target", "ally", 100)
    state = BattleState(units=[actor, target])
    Action(
        id="add_buff",
        name="Add Buff",
        actor_id="actor",
        target_ids=["target"],
        effects=[AddBuff(id="damage_boost", name="Damage Boost")],
        ends_turn=False,
    ).execute(state)

    Action(
        id="remove_buff",
        name="Remove Buff",
        actor_id="actor",
        target_ids=["target"],
        effects=[RemoveBuff(id="damage_boost")],
        ends_turn=False,
    ).execute(state)

    assert target.get_buff("damage_boost") is None


def test_add_debuff_and_remove_debuff_work():
    actor = Unit("actor", "Actor", "ally", 100)
    target = Unit("target", "Target", "enemy", 100)
    state = BattleState(units=[actor, target])

    Action(
        id="add_debuff",
        name="Add Debuff",
        actor_id="actor",
        target_ids=["target"],
        effects=[
            AddDebuff(
                id="defense_down",
                name="Defense Down",
                duration_type="target_normal_turns",
                remaining_turns=2,
                stacks=1,
                max_stacks=2,
            )
        ],
        ends_turn=False,
    ).execute(state)

    debuff = target.get_debuff("defense_down")
    assert debuff is not None
    assert debuff.kind == "debuff"
    assert debuff.source_id == "actor"

    Action(
        id="remove_debuff",
        name="Remove Debuff",
        actor_id="actor",
        target_ids=["target"],
        effects=[RemoveDebuff(id="defense_down")],
        ends_turn=False,
    ).execute(state)

    assert target.get_debuff("defense_down") is None


def test_target_normal_turns_duration_ticks_after_holders_normal_turn():
    actor = Unit("actor", "Actor", "ally", 100, current_av=0)
    state = BattleState(units=[actor])
    Action(
        id="add_buff",
        name="Add Buff",
        actor_id="actor",
        target_ids=["actor"],
        effects=[AddBuff(id="damage_boost", name="Damage Boost", remaining_turns=1)],
        ends_turn=False,
    ).execute(state)
    turn = Timeline.next_turn(state)

    Timeline.end_turn(state, turn)

    assert actor.get_buff("damage_boost") is None


def test_target_normal_turns_duration_does_not_tick_on_extra_turn():
    actor = Unit("actor", "Actor", "ally", 100, current_av=50)
    state = BattleState(units=[actor], extra_turn_stack=["actor"])
    Action(
        id="add_buff",
        name="Add Buff",
        actor_id="actor",
        target_ids=["actor"],
        effects=[AddBuff(id="damage_boost", name="Damage Boost", remaining_turns=1)],
        ends_turn=False,
    ).execute(state)
    turn = Timeline.next_turn(state)

    Timeline.end_turn(state, turn)

    assert actor.get_buff("damage_boost") is not None
    assert actor.get_buff("damage_boost").remaining_turns == 1


def test_does_not_end_turn_prevents_current_turn_expiration_until_actual_end():
    actor = Unit("actor", "Actor", "ally", 100, current_av=0)
    state = BattleState(units=[actor])
    turn = Timeline.next_turn(state)
    Action(
        id="open_turn",
        name="Open Turn",
        actor_id="actor",
        target_ids=["actor"],
        effects=[
            AddBuff(
                id="during_turn",
                name="During Turn",
                duration_type="current_turn",
                remaining_turns=None,
            ),
            DoesNotEndTurn(),
        ],
    ).execute(state, turn)

    assert actor.get_buff("during_turn") is not None

    Action(
        id="close_turn",
        name="Close Turn",
        actor_id="actor",
        target_ids=["actor"],
        effects=[],
    ).execute(state, turn)

    assert actor.get_buff("during_turn") is None


def test_current_turn_buff_expires_at_actual_turn_end():
    actor = Unit("actor", "Actor", "ally", 100, current_av=0)
    state = BattleState(units=[actor])
    turn = Timeline.next_turn(state)

    Action(
        id="current_turn_buff",
        name="Current Turn Buff",
        actor_id="actor",
        target_ids=["actor"],
        effects=[
            AddBuff(
                id="during_turn",
                name="During Turn",
                duration_type="current_turn",
                remaining_turns=None,
            )
        ],
    ).execute(state, turn)

    assert actor.get_buff("during_turn") is None


def test_target_normal_turns_duration_ignores_granted_extra_turn_before_normal_turn():
    actor = Unit("actor", "Actor", "ally", 100, current_av=50)
    state = BattleState(units=[actor])
    Action(
        id="setup",
        name="Setup",
        actor_id="actor",
        target_ids=["actor"],
        effects=[
            AddBuff(id="damage_boost", name="Damage Boost", remaining_turns=1),
            GrantExtraTurn(),
        ],
        ends_turn=False,
    ).execute(state)

    extra_turn = Timeline.next_turn(state)
    Timeline.end_turn(state, extra_turn)

    assert actor.get_buff("damage_boost") is not None

    normal_turn = Timeline.next_turn(state)
    Timeline.end_turn(state, normal_turn)

    assert actor.get_buff("damage_boost") is None
