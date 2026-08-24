import pytest

from hsr_axis_sim.sim import (
    Action,
    AddBuff,
    AddDebuff,
    BattleState,
    DealToughnessDamage,
    GrantExtraTurn,
    Timeline,
    Unit,
)


def test_toughness_damage_reduces_toughness_when_element_matches_weakness():
    attacker = Unit("ally", "Ally", "ally", 100)
    target = Unit(
        "enemy",
        "Enemy",
        "enemy",
        100,
        weaknesses=["quantum"],
        max_toughness=60,
    )
    state = BattleState(units=[attacker, target])

    Action(
        id="toughness_hit",
        name="Toughness Hit",
        actor_id="ally",
        target_ids=["enemy"],
        effects=[DealToughnessDamage(amount=20, element="quantum")],
        ends_turn=False,
    ).execute(state)

    assert target.current_toughness == pytest.approx(40, abs=1e-6)
    assert target.is_broken is False


def test_toughness_damage_does_not_reduce_without_matching_weakness():
    attacker = Unit("ally", "Ally", "ally", 100)
    target = Unit(
        "enemy",
        "Enemy",
        "enemy",
        100,
        weaknesses=["fire"],
        max_toughness=60,
    )
    state = BattleState(units=[attacker, target])

    Action(
        id="toughness_hit",
        name="Toughness Hit",
        actor_id="ally",
        target_ids=["enemy"],
        effects=[DealToughnessDamage(amount=20, element="quantum")],
        ends_turn=False,
    ).execute(state)

    assert target.current_toughness == pytest.approx(60, abs=1e-6)


def test_ignore_weakness_allows_toughness_damage():
    attacker = Unit("ally", "Ally", "ally", 100)
    target = Unit("enemy", "Enemy", "enemy", 100, weaknesses=[], max_toughness=60)
    state = BattleState(units=[attacker, target])

    Action(
        id="toughness_hit",
        name="Toughness Hit",
        actor_id="ally",
        target_ids=["enemy"],
        effects=[
            DealToughnessDamage(amount=20, element="quantum", ignore_weakness=True)
        ],
        ends_turn=False,
    ).execute(state)

    assert target.current_toughness == pytest.approx(40, abs=1e-6)


def test_toughness_is_clamped_at_zero_and_breaks_unit():
    attacker = Unit("ally", "Ally", "ally", 100)
    target = Unit(
        "enemy",
        "Enemy",
        "enemy",
        100,
        weaknesses=["quantum"],
        max_toughness=60,
        current_toughness=10,
    )
    state = BattleState(units=[attacker, target])

    Action(
        id="break_hit",
        name="Break Hit",
        actor_id="ally",
        target_ids=["enemy"],
        effects=[DealToughnessDamage(amount=50, element="quantum")],
        ends_turn=False,
    ).execute(state)

    assert target.current_toughness == pytest.approx(0, abs=1e-6)
    assert target.is_broken is True


def test_breaking_unit_delays_current_av():
    attacker = Unit("ally", "Ally", "ally", 100)
    target = Unit(
        "enemy",
        "Enemy",
        "enemy",
        100,
        current_av=20,
        weaknesses=["quantum"],
        max_toughness=60,
    )
    state = BattleState(units=[attacker, target])

    Action(
        id="break_hit",
        name="Break Hit",
        actor_id="ally",
        target_ids=["enemy"],
        effects=[
            DealToughnessDamage(
                amount=60,
                element="quantum",
                break_delay_percent=0.25,
            )
        ],
        ends_turn=False,
    ).execute(state)

    assert target.current_av == pytest.approx(45, abs=1e-6)
    assert state.logs == ["break:enemy"]


def test_already_broken_units_do_not_take_more_toughness_damage():
    attacker = Unit("ally", "Ally", "ally", 100)
    target = Unit(
        "enemy",
        "Enemy",
        "enemy",
        100,
        weaknesses=["quantum"],
        max_toughness=60,
        current_toughness=0,
        is_broken=True,
    )
    state = BattleState(units=[attacker, target])

    Action(
        id="toughness_hit",
        name="Toughness Hit",
        actor_id="ally",
        target_ids=["enemy"],
        effects=[DealToughnessDamage(amount=20, element="quantum")],
        ends_turn=False,
    ).execute(state)

    assert target.current_toughness == pytest.approx(0, abs=1e-6)
    assert target.is_broken is True


def test_broken_unit_recovers_toughness_at_end_of_next_normal_turn():
    unit = Unit(
        "enemy",
        "Enemy",
        "enemy",
        100,
        current_av=0,
        max_toughness=60,
        current_toughness=0,
        is_broken=True,
    )
    state = BattleState(units=[unit])
    turn = Timeline.next_turn(state)

    Timeline.end_turn(state, turn)

    assert unit.is_broken is False
    assert unit.current_toughness == pytest.approx(60, abs=1e-6)


def test_extra_turn_does_not_recover_broken_unit():
    unit = Unit(
        "enemy",
        "Enemy",
        "enemy",
        100,
        current_av=50,
        max_toughness=60,
        current_toughness=0,
        is_broken=True,
    )
    state = BattleState(units=[unit], extra_turn_stack=["enemy"])
    turn = Timeline.next_turn(state)

    Timeline.end_turn(state, turn)

    assert unit.is_broken is True
    assert unit.current_toughness == pytest.approx(0, abs=1e-6)


def test_granted_extra_turn_before_normal_turn_does_not_recover_broken_unit():
    unit = Unit(
        "enemy",
        "Enemy",
        "enemy",
        100,
        current_av=50,
        max_toughness=60,
        current_toughness=0,
        is_broken=True,
    )
    state = BattleState(units=[unit])
    Action(
        id="grant_extra",
        name="Grant Extra",
        actor_id="enemy",
        target_ids=["enemy"],
        effects=[GrantExtraTurn()],
        ends_turn=False,
    ).execute(state)

    extra_turn = Timeline.next_turn(state)
    Timeline.end_turn(state, extra_turn)

    assert unit.is_broken is True

    normal_turn = Timeline.next_turn(state)
    Timeline.end_turn(state, normal_turn)

    assert unit.is_broken is False
    assert unit.current_toughness == pytest.approx(60, abs=1e-6)


def test_break_damage_only_happens_on_actual_break():
    attacker = Unit("ally", "Ally", "ally", 100, level=80)
    target = Unit(
        "enemy",
        "Enemy",
        "enemy",
        100,
        weaknesses=["fire"],
        max_toughness=60,
        current_toughness=60,
        hp=1000,
        max_hp=1000,
    )
    state = BattleState(units=[attacker, target])

    Action(
        id="non_break_hit",
        name="Non Break Hit",
        actor_id="ally",
        target_ids=["enemy"],
        effects=[
            DealToughnessDamage(
                amount=30,
                element="fire",
                deal_break_damage=True,
                break_damage_base_override=100,
            )
        ],
        ends_turn=False,
    ).execute(state)

    assert target.current_toughness == pytest.approx(30, abs=1e-6)
    assert target.hp == pytest.approx(1000, abs=1e-6)

    Action(
        id="break_hit",
        name="Break Hit",
        actor_id="ally",
        target_ids=["enemy"],
        effects=[
            DealToughnessDamage(
                amount=30,
                element="fire",
                deal_break_damage=True,
                break_damage_base_override=100,
            )
        ],
        ends_turn=False,
    ).execute(state)

    assert target.is_broken is True
    assert target.hp == pytest.approx(800, abs=1e-6)


def test_no_break_damage_when_weakness_does_not_match():
    attacker = Unit("ally", "Ally", "ally", 100)
    target = Unit(
        "enemy",
        "Enemy",
        "enemy",
        100,
        weaknesses=["ice"],
        max_toughness=60,
        hp=1000,
        max_hp=1000,
    )
    state = BattleState(units=[attacker, target])

    Action(
        id="wrong_element",
        name="Wrong Element",
        actor_id="ally",
        target_ids=["enemy"],
        effects=[
            DealToughnessDamage(
                amount=60,
                element="fire",
                deal_break_damage=True,
                break_damage_base_override=100,
            )
        ],
        ends_turn=False,
    ).execute(state)

    assert target.current_toughness == pytest.approx(60, abs=1e-6)
    assert target.is_broken is False
    assert target.hp == pytest.approx(1000, abs=1e-6)


def test_no_break_damage_when_target_already_broken():
    attacker = Unit("ally", "Ally", "ally", 100)
    target = Unit(
        "enemy",
        "Enemy",
        "enemy",
        100,
        weaknesses=["fire"],
        max_toughness=60,
        current_toughness=0,
        is_broken=True,
        hp=1000,
        max_hp=1000,
    )
    state = BattleState(units=[attacker, target])

    Action(
        id="already_broken",
        name="Already Broken",
        actor_id="ally",
        target_ids=["enemy"],
        effects=[
            DealToughnessDamage(
                amount=60,
                element="fire",
                deal_break_damage=True,
                break_damage_base_override=100,
            )
        ],
        ends_turn=False,
    ).execute(state)

    assert target.hp == pytest.approx(1000, abs=1e-6)


def test_break_effect_and_break_damage_bonus_increase_break_damage():
    attacker = Unit("ally", "Ally", "ally", 100, break_effect=0.5)
    target = Unit(
        "enemy",
        "Enemy",
        "enemy",
        100,
        weaknesses=["fire"],
        max_toughness=60,
        hp=1000,
        max_hp=1000,
    )
    state = BattleState(units=[attacker, target])
    Action(
        id="buff",
        name="Buff",
        actor_id="ally",
        target_ids=["ally"],
        effects=[
            AddBuff(
                id="break_bonus",
                name="Break Bonus",
                data={"stat_mods": {"break_damage_bonus": 0.25}},
            )
        ],
        ends_turn=False,
    ).execute(state)

    Action(
        id="break_hit",
        name="Break Hit",
        actor_id="ally",
        target_ids=["enemy"],
        effects=[
            DealToughnessDamage(
                amount=60,
                element="fire",
                deal_break_damage=True,
                break_damage_base_override=100,
            )
        ],
        ends_turn=False,
    ).execute(state)

    assert target.hp == pytest.approx(625, abs=1e-6)


def test_defense_resistance_and_vulnerability_affect_break_damage():
    attacker = Unit("ally", "Ally", "ally", 100, level=80)
    target = Unit(
        "enemy",
        "Enemy",
        "enemy",
        100,
        defense=1000,
        fire_res=0.2,
        weaknesses=["fire"],
        max_toughness=60,
        hp=1000,
        max_hp=1000,
    )
    state = BattleState(units=[attacker, target])
    Action(
        id="debuff",
        name="Debuff",
        actor_id="ally",
        target_ids=["enemy"],
        effects=[
            AddDebuff(
                id="break_amp",
                name="Break Amp",
                data={"stat_mods": {"def_reduction": 0.5, "vulnerability": 0.25}},
            )
        ],
        ends_turn=False,
    ).execute(state)

    Action(
        id="break_hit",
        name="Break Hit",
        actor_id="ally",
        target_ids=["enemy"],
        effects=[
            DealToughnessDamage(
                amount=60,
                element="fire",
                deal_break_damage=True,
                break_damage_base_override=100,
                break_damage_resistance_penetration=0.1,
            )
        ],
        ends_turn=False,
    ).execute(state)

    assert target.hp == pytest.approx(850, abs=1e-6)


def test_elemental_break_debuff_is_applied_with_metadata():
    attacker = Unit("ally", "Ally", "ally", 100)
    target = Unit(
        "enemy",
        "Enemy",
        "enemy",
        100,
        weaknesses=["quantum"],
        max_toughness=60,
    )
    state = BattleState(units=[attacker, target])

    Action(
        id="break_hit",
        name="Break Hit",
        actor_id="ally",
        target_ids=["enemy"],
        effects=[
            DealToughnessDamage(
                amount=60,
                element="quantum",
                apply_elemental_break_effect=True,
            )
        ],
        ends_turn=False,
    ).execute(state)

    debuff = target.get_debuff("quantum_break_entanglement")
    assert debuff is not None
    assert debuff.kind == "debuff"
    assert debuff.duration_type == "target_normal_turns"
    assert debuff.remaining_turns == 1
    assert debuff.source_id == "ally"
    assert debuff.data == {
        "source": "elemental_break_effect_mvp",
        "element": "quantum",
        "mvp_no_dot_tick": True,
    }


def test_weakness_break_event_includes_break_damage_metadata():
    attacker = Unit("ally", "Ally", "ally", 100)
    target = Unit(
        "enemy",
        "Enemy",
        "enemy",
        100,
        weaknesses=["fire"],
        max_toughness=60,
        hp=1000,
        max_hp=1000,
    )
    state = BattleState(units=[attacker, target])

    Action(
        id="break_hit",
        name="Break Hit",
        actor_id="ally",
        target_ids=["enemy"],
        effects=[
            DealToughnessDamage(
                amount=60,
                element="fire",
                deal_break_damage=True,
                break_damage_base_override=100,
                apply_elemental_break_effect=True,
            )
        ],
        ends_turn=False,
    ).execute(state)

    break_event = [event for event in state.pending_events if event.type == "weakness_break"][0]
    assert break_event.data["break_damage_amount"] == pytest.approx(200, abs=1e-6)
    assert break_event.data["elemental_break_effect_id"] == "fire_break_burn"
    assert break_event.data["formula_parts"]["final_break_damage"] == pytest.approx(
        200,
        abs=1e-6,
    )
