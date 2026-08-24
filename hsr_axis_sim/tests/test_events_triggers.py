import pytest

from hsr_axis_sim.sim import (
    Action,
    AddBuff,
    BattleState,
    DealDamage,
    DealToughnessDamage,
    GainEnergy,
    GrantExtraTurn,
    Trigger,
    Unit,
)


def test_deal_damage_emits_damage_dealt():
    attacker = Unit("dps", "DPS", "ally", 100)
    target = Unit("enemy", "Enemy", "enemy", 100, hp=1000, max_hp=1000)
    state = BattleState(units=[attacker, target])

    Action(
        id="hit",
        name="Hit",
        actor_id="dps",
        target_ids=["enemy"],
        effects=[DealDamage(amount=100, damage_type="generic")],
        ends_turn=False,
    ).execute(state)

    damage_events = [event for event in state.pending_events if event.type == "damage_dealt"]
    assert len(damage_events) == 1
    assert damage_events[0].data["source_id"] == "dps"
    assert damage_events[0].data["target_id"] == "enemy"
    assert damage_events[0].data["amount"] == pytest.approx(100, abs=1e-6)
    assert damage_events[0].data["damage_type"] == "generic"


def test_deal_damage_emits_unit_defeated_only_for_new_defeat():
    attacker = Unit("dps", "DPS", "ally", 100)
    target = Unit("enemy", "Enemy", "enemy", 100, hp=100, max_hp=100)
    state = BattleState(units=[attacker, target])
    action = Action(
        id="hit",
        name="Hit",
        actor_id="dps",
        target_ids=["enemy"],
        effects=[DealDamage(amount=100)],
        ends_turn=False,
    )

    action.execute(state)
    action.execute(state)

    defeated_events = [event for event in state.pending_events if event.type == "unit_defeated"]
    assert len(defeated_events) == 1
    assert defeated_events[0].data == {"killer_id": "dps", "target_id": "enemy"}


def test_event_killer_is_owner_trigger_fires_for_owner_kill():
    owner = Unit("owner", "Owner", "ally", 100)
    target = Unit("enemy", "Enemy", "enemy", 100, hp=100, max_hp=100)
    state = BattleState(
        units=[owner, target],
        triggers=[
            Trigger(
                id="on_kill_energy",
                owner_id="owner",
                event_type="unit_defeated",
                condition={"type": "event_killer_is_owner"},
                effects=[GainEnergy(amount=10)],
            )
        ],
    )

    Action(
        id="kill",
        name="Kill",
        actor_id="owner",
        target_ids=["enemy"],
        effects=[DealDamage(amount=100)],
        ends_turn=False,
    ).execute(state)

    assert owner.energy == pytest.approx(10, abs=1e-6)
    assert "trigger:on_kill_energy" in state.logs


def test_event_killer_is_owner_trigger_does_not_fire_for_other_kill():
    owner = Unit("owner", "Owner", "ally", 100)
    other = Unit("other", "Other", "ally", 100)
    target = Unit("enemy", "Enemy", "enemy", 100, hp=100, max_hp=100)
    state = BattleState(
        units=[owner, other, target],
        triggers=[
            Trigger(
                id="on_kill_energy",
                owner_id="owner",
                event_type="unit_defeated",
                condition={"type": "event_killer_is_owner"},
                effects=[GainEnergy(amount=10)],
            )
        ],
    )

    Action(
        id="kill",
        name="Kill",
        actor_id="other",
        target_ids=["enemy"],
        effects=[DealDamage(amount=100)],
        ends_turn=False,
    ).execute(state)

    assert owner.energy == pytest.approx(0, abs=1e-6)
    assert "trigger:on_kill_energy" not in state.logs


def test_trigger_can_execute_grant_extra_turn():
    owner = Unit("owner", "Owner", "ally", 100)
    target = Unit("enemy", "Enemy", "enemy", 100, hp=100, max_hp=100)
    state = BattleState(
        units=[owner, target],
        triggers=[
            Trigger(
                id="on_kill_extra_turn",
                owner_id="owner",
                event_type="unit_defeated",
                condition={"type": "event_killer_is_owner"},
                effects=[GrantExtraTurn()],
            )
        ],
    )

    Action(
        id="kill",
        name="Kill",
        actor_id="owner",
        target_ids=["enemy"],
        effects=[DealDamage(amount=100)],
        ends_turn=False,
    ).execute(state)

    assert state.extra_turn_stack == ["owner"]


def test_trigger_can_execute_gain_energy_and_add_buff():
    owner = Unit("owner", "Owner", "ally", 100)
    target = Unit("enemy", "Enemy", "enemy", 100, hp=100, max_hp=100)
    state = BattleState(
        units=[owner, target],
        triggers=[
            Trigger(
                id="on_damage",
                owner_id="owner",
                event_type="damage_dealt",
                condition={"type": "event_source_is_owner"},
                effects=[
                    GainEnergy(amount=5),
                    AddBuff(id="trigger_buff", name="Trigger Buff"),
                ],
            )
        ],
    )

    Action(
        id="hit",
        name="Hit",
        actor_id="owner",
        target_ids=["enemy"],
        effects=[DealDamage(amount=10)],
        ends_turn=False,
    ).execute(state)

    assert owner.energy == pytest.approx(5, abs=1e-6)
    assert owner.get_buff("trigger_buff") is not None


def test_weakness_break_emits_event_and_can_activate_trigger():
    owner = Unit("owner", "Owner", "ally", 100)
    target = Unit(
        "enemy",
        "Enemy",
        "enemy",
        100,
        weaknesses=["quantum"],
        max_toughness=60,
    )
    state = BattleState(
        units=[owner, target],
        triggers=[
            Trigger(
                id="on_break_energy",
                owner_id="owner",
                event_type="weakness_break",
                condition={"type": "event_source_is_owner"},
                effects=[GainEnergy(amount=15)],
            )
        ],
    )

    Action(
        id="break",
        name="Break",
        actor_id="owner",
        target_ids=["enemy"],
        effects=[DealToughnessDamage(amount=60, element="quantum")],
        ends_turn=False,
    ).execute(state)

    break_events = [event for event in state.pending_events if event.type == "weakness_break"]
    assert len(break_events) == 1
    assert break_events[0].data["source_id"] == "owner"
    assert owner.energy == pytest.approx(15, abs=1e-6)


def test_trigger_ordering_is_deterministic_by_id():
    owner = Unit("owner", "Owner", "ally", 100, energy=0)
    target = Unit("enemy", "Enemy", "enemy", 100, hp=100, max_hp=100)
    state = BattleState(
        units=[owner, target],
        triggers=[
            Trigger(
                id="b_second",
                owner_id="owner",
                event_type="damage_dealt",
                condition={"type": "always"},
                effects=[GainEnergy(amount=10)],
            ),
            Trigger(
                id="a_first",
                owner_id="owner",
                event_type="damage_dealt",
                condition={"type": "always"},
                effects=[GainEnergy(amount=1)],
            ),
        ],
    )

    Action(
        id="hit",
        name="Hit",
        actor_id="owner",
        target_ids=["enemy"],
        effects=[DealDamage(amount=10)],
        ends_turn=False,
    ).execute(state)

    trigger_logs = [log for log in state.logs if log.startswith("trigger:")]
    assert trigger_logs == ["trigger:a_first", "trigger:b_second"]
    assert owner.energy == pytest.approx(11, abs=1e-6)


def test_recursive_trigger_loop_protection_raises_clear_error():
    owner = Unit("owner", "Owner", "ally", 100)
    target = Unit("enemy", "Enemy", "enemy", 100, hp=1000, max_hp=1000)
    state = BattleState(
        units=[owner, target],
        event_dispatch_limit=5,
        triggers=[
            Trigger(
                id="loop",
                owner_id="owner",
                event_type="damage_dealt",
                condition={"type": "always"},
                effects=[DealDamage(amount=0, target_ids=["enemy"])],
                max_triggers_per_action=999,
            )
        ],
    )

    with pytest.raises(ValueError, match="Event dispatch limit exceeded"):
        Action(
            id="hit",
            name="Hit",
            actor_id="owner",
            target_ids=["enemy"],
            effects=[DealDamage(amount=1)],
            ends_turn=False,
        ).execute(state)
