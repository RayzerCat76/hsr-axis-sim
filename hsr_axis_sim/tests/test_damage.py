import pytest

from hsr_axis_sim.sim import (
    Action,
    AddBuff,
    AddDebuff,
    BattleState,
    DealDamage,
    Timeline,
    TurnContext,
    Unit,
    effective_stats,
)


def test_fixed_damage_backward_compatibility():
    attacker = Unit("dps", "DPS", "ally", 100)
    target = Unit("enemy", "Enemy", "enemy", 100, hp=1000, max_hp=1000)
    state = BattleState(units=[attacker, target])

    Action(
        id="fixed_hit",
        name="Fixed Hit",
        actor_id="dps",
        target_ids=["enemy"],
        effects=[DealDamage(amount=123)],
        ends_turn=False,
    ).execute(state)

    assert target.hp == pytest.approx(877, abs=1e-6)


def test_calculated_no_crit_damage():
    attacker = Unit("dps", "DPS", "ally", 100, atk=1000)
    target = Unit("enemy", "Enemy", "enemy", 100, hp=5000, max_hp=5000)
    state = BattleState(units=[attacker, target])

    Action(
        id="skill",
        name="Skill",
        actor_id="dps",
        target_ids=["enemy"],
        effects=[DealDamage(multiplier=2.0)],
        ends_turn=False,
    ).execute(state, TurnContext(actor_id="dps", forced_rng={"crit": False}))

    assert target.hp == pytest.approx(3000, abs=1e-6)


def test_calculated_crit_damage():
    attacker = Unit("dps", "DPS", "ally", 100, atk=1000, crit_dmg=0.5)
    target = Unit("enemy", "Enemy", "enemy", 100, hp=5000, max_hp=5000)
    state = BattleState(units=[attacker, target])

    Action(
        id="skill",
        name="Skill",
        actor_id="dps",
        target_ids=["enemy"],
        effects=[DealDamage(multiplier=2.0)],
        ends_turn=False,
    ).execute(state, TurnContext(actor_id="dps", forced_rng={"crit": True}))

    assert target.hp == pytest.approx(2000, abs=1e-6)


def test_buff_stat_modifies_calculated_damage():
    attacker = Unit("dps", "DPS", "ally", 100, atk=1000)
    target = Unit("enemy", "Enemy", "enemy", 100, hp=5000, max_hp=5000)
    state = BattleState(units=[attacker, target])
    Action(
        id="buff",
        name="Buff",
        actor_id="dps",
        target_ids=["dps"],
        effects=[
            AddBuff(
                id="damage_boost",
                name="Damage Boost",
                data={"stat_mods": {"dmg_bonus": 0.5}},
            )
        ],
        ends_turn=False,
    ).execute(state)

    Action(
        id="skill",
        name="Skill",
        actor_id="dps",
        target_ids=["enemy"],
        effects=[DealDamage(multiplier=2.0)],
        ends_turn=False,
    ).execute(state, TurnContext(actor_id="dps", forced_rng={"crit": False}))

    assert effective_stats(attacker).dmg_bonus == pytest.approx(0.5, abs=1e-6)
    assert target.hp == pytest.approx(2000, abs=1e-6)


def test_atk_pct_buff_modifies_effective_attack():
    attacker = Unit("dps", "DPS", "ally", 100, atk=1000)
    state = BattleState(units=[attacker])
    Action(
        id="buff",
        name="Buff",
        actor_id="dps",
        target_ids=["dps"],
        effects=[
            AddBuff(
                id="attack_boost",
                name="Attack Boost",
                data={"stat_mods": {"atk_pct": 0.5, "atk_flat": 50}},
            )
        ],
        ends_turn=False,
    ).execute(state)

    assert effective_stats(attacker).atk == pytest.approx(1550, abs=1e-6)


def test_buff_duration_and_damage_interaction():
    attacker = Unit("dps", "DPS", "ally", 100, current_av=0, atk=1000)
    target = Unit("enemy", "Enemy", "enemy", 100, current_av=999, hp=10000, max_hp=10000)
    state = BattleState(units=[attacker, target])
    Action(
        id="buff",
        name="Buff",
        actor_id="dps",
        target_ids=["dps"],
        effects=[
            AddBuff(
                id="attack_boost",
                name="Attack Boost",
                remaining_turns=1,
                data={"stat_mods": {"atk_pct": 1.0}},
            )
        ],
        ends_turn=False,
    ).execute(state)

    first_turn = Timeline.next_turn(state)
    Action(
        id="buffed_hit",
        name="Buffed Hit",
        actor_id="dps",
        target_ids=["enemy"],
        effects=[DealDamage(multiplier=1.0)],
    ).execute(state, first_turn)

    assert target.hp == pytest.approx(8000, abs=1e-6)
    assert attacker.get_buff("attack_boost") is None

    second_turn = Timeline.next_turn(state)
    Action(
        id="unbuffed_hit",
        name="Unbuffed Hit",
        actor_id="dps",
        target_ids=["enemy"],
        effects=[DealDamage(multiplier=1.0)],
    ).execute(state, second_turn)

    assert target.hp == pytest.approx(7000, abs=1e-6)


def test_target_vulnerability_debuff_increases_damage():
    attacker = Unit("dps", "DPS", "ally", 100, atk=1000)
    target = Unit("enemy", "Enemy", "enemy", 100, hp=5000, max_hp=5000)
    state = BattleState(units=[attacker, target])
    Action(
        id="debuff",
        name="Debuff",
        actor_id="dps",
        target_ids=["enemy"],
        effects=[
            AddDebuff(
                id="vulnerable",
                name="Vulnerable",
                data={"stat_mods": {"vulnerability": 0.25}},
            )
        ],
        ends_turn=False,
    ).execute(state)

    Action(
        id="skill",
        name="Skill",
        actor_id="dps",
        target_ids=["enemy"],
        effects=[DealDamage(multiplier=1.0)],
        ends_turn=False,
    ).execute(state, TurnContext(actor_id="dps", forced_rng={"crit": False}))

    assert target.hp == pytest.approx(3750, abs=1e-6)


def test_defense_reduction_and_defense_ignore_reduce_effective_defense():
    attacker = Unit("dps", "DPS", "ally", 100, atk=1000, level=80)
    target = Unit(
        "enemy",
        "Enemy",
        "enemy",
        100,
        defense=1000,
        hp=5000,
        max_hp=5000,
    )
    state = BattleState(units=[attacker, target])
    Action(
        id="debuff",
        name="Debuff",
        actor_id="dps",
        target_ids=["enemy"],
        effects=[
            AddDebuff(
                id="def_down",
                name="Defense Down",
                data={"stat_mods": {"def_reduction": 0.5}},
            )
        ],
        ends_turn=False,
    ).execute(state)

    Action(
        id="skill",
        name="Skill",
        actor_id="dps",
        target_ids=["enemy"],
        effects=[DealDamage(multiplier=1.0, defense_ignore=0.2)],
        ends_turn=False,
    ).execute(state, TurnContext(actor_id="dps", forced_rng={"crit": False}))

    assert target.hp == pytest.approx(4285.714285714, abs=1e-6)


def test_elemental_resistance_and_resistance_penetration_modify_damage():
    attacker = Unit("dps", "DPS", "ally", 100, atk=1000)
    target = Unit(
        "enemy",
        "Enemy",
        "enemy",
        100,
        quantum_res=0.2,
        hp=5000,
        max_hp=5000,
    )
    state = BattleState(units=[attacker, target])
    Action(
        id="buff",
        name="Buff",
        actor_id="dps",
        target_ids=["dps"],
        effects=[
            AddBuff(
                id="pen",
                name="Resistance Pen",
                data={"stat_mods": {"all_res_pen": 0.1}},
            )
        ],
        ends_turn=False,
    ).execute(state)

    Action(
        id="skill",
        name="Skill",
        actor_id="dps",
        target_ids=["enemy"],
        effects=[
            DealDamage(
                multiplier=1.0,
                element="quantum",
                resistance_penetration=0.05,
            )
        ],
        ends_turn=False,
    ).execute(state, TurnContext(actor_id="dps", forced_rng={"crit": False}))

    assert target.hp == pytest.approx(4050, abs=1e-6)


def test_can_crit_false_ignores_forced_crit():
    attacker = Unit("dps", "DPS", "ally", 100, atk=1000, crit_dmg=2.0)
    target = Unit("enemy", "Enemy", "enemy", 100, hp=5000, max_hp=5000)
    state = BattleState(units=[attacker, target])

    Action(
        id="skill",
        name="Skill",
        actor_id="dps",
        target_ids=["enemy"],
        effects=[DealDamage(multiplier=1.0, can_crit=False)],
        ends_turn=False,
    ).execute(state, TurnContext(actor_id="dps", forced_rng={"crit": True}))

    assert target.hp == pytest.approx(4000, abs=1e-6)


def test_damage_event_contains_formula_v1_metadata():
    attacker = Unit("dps", "DPS", "ally", 100, atk=1000)
    target = Unit("enemy", "Enemy", "enemy", 100, hp=5000, max_hp=5000)
    state = BattleState(units=[attacker, target])

    Action(
        id="skill",
        name="Skill",
        actor_id="dps",
        target_ids=["enemy"],
        effects=[DealDamage(multiplier=1.0, damage_type="skill", element="quantum")],
        ends_turn=False,
    ).execute(state, TurnContext(actor_id="dps", forced_rng={"crit": False}))

    event = [event for event in state.pending_events if event.type == "damage_dealt"][0]
    assert event.data["element"] == "quantum"
    assert event.data["damage_type"] == "skill"
    assert event.data["formula_parts"]["base_damage"] == pytest.approx(1000, abs=1e-6)
