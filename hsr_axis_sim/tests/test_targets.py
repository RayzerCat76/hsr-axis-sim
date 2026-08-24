from pathlib import Path

import pytest

from hsr_axis_sim.sim import (
    Action,
    AddBuff,
    BattleState,
    DealDamage,
    GainEnergy,
    Trigger,
    TurnContext,
    Unit,
)
from hsr_axis_sim.sim.data_loader import action_from_skill, instantiate_unit, load_character_spec
from hsr_axis_sim.sim.data_schema import UnitInstanceSpec


ROOT = Path(__file__).resolve().parents[1]
CHARACTERS_DIR = ROOT / "data" / "sample_characters"


def test_actor_target_ref_targets_instantiated_unit_id_not_character_id():
    character = load_character_spec(CHARACTERS_DIR / "seele_like.json")
    seele_a = instantiate_unit(
        character,
        UnitInstanceSpec(
            character_id="seele_like",
            unit_id="seele_a",
            team="ally",
            initial_energy=0,
        ),
    )
    enemy = Unit("enemy", "Enemy", "enemy", 100, hp=1000, max_hp=1000)
    state = BattleState(units=[seele_a, enemy])
    action = action_from_skill(
        character.get_skill("basic"),
        actor_id="seele_a",
        target_ids=["enemy"],
    )

    action.execute(state, TurnContext(actor_id="seele_a"))

    assert state.get_unit("seele_a").energy == pytest.approx(20, abs=1e-6)
    with pytest.raises(KeyError):
        state.get_unit("seele_like")


def test_action_targets_ref_uses_selected_targets():
    actor = Unit("actor", "Actor", "ally", 100)
    target = Unit("target", "Target", "enemy", 100, hp=100, max_hp=100)
    other = Unit("other", "Other", "enemy", 100, hp=100, max_hp=100)
    state = BattleState(units=[actor, target, other])

    Action(
        id="hit",
        name="Hit",
        actor_id="actor",
        target_ids=["target"],
        effects=[DealDamage(amount=25, target_ref="action_targets")],
        ends_turn=False,
    ).execute(state)

    assert target.hp == pytest.approx(75, abs=1e-6)
    assert other.hp == pytest.approx(100, abs=1e-6)


def test_all_allies_and_alive_allies_refs():
    actor = Unit("actor", "Actor", "ally", 100)
    alive_ally = Unit("alive_ally", "Alive Ally", "ally", 100)
    dead_ally = Unit("dead_ally", "Dead Ally", "ally", 100, is_alive=False)
    enemy = Unit("enemy", "Enemy", "enemy", 100)
    state = BattleState(units=[actor, alive_ally, dead_ally, enemy])

    Action(
        id="all_allies",
        name="All Allies",
        actor_id="actor",
        effects=[GainEnergy(amount=5, target_ref="all_allies")],
        ends_turn=False,
    ).execute(state)

    assert actor.energy == pytest.approx(5, abs=1e-6)
    assert alive_ally.energy == pytest.approx(5, abs=1e-6)
    assert dead_ally.energy == pytest.approx(5, abs=1e-6)
    assert enemy.energy == pytest.approx(0, abs=1e-6)

    Action(
        id="alive_allies",
        name="Alive Allies",
        actor_id="actor",
        effects=[GainEnergy(amount=5, target_ref="alive_allies")],
        ends_turn=False,
    ).execute(state)

    assert actor.energy == pytest.approx(10, abs=1e-6)
    assert alive_ally.energy == pytest.approx(10, abs=1e-6)
    assert dead_ally.energy == pytest.approx(5, abs=1e-6)


def test_all_enemies_and_alive_enemies_refs():
    actor = Unit("actor", "Actor", "ally", 100)
    enemy = Unit("enemy", "Enemy", "enemy", 100)
    dead_enemy = Unit("dead_enemy", "Dead Enemy", "enemy", 100, is_alive=False)
    ally = Unit("ally", "Ally", "ally", 100)
    state = BattleState(units=[actor, enemy, dead_enemy, ally])

    Action(
        id="all_enemies",
        name="All Enemies",
        actor_id="actor",
        effects=[GainEnergy(amount=5, target_ref="all_enemies")],
        ends_turn=False,
    ).execute(state)

    assert enemy.energy == pytest.approx(5, abs=1e-6)
    assert dead_enemy.energy == pytest.approx(5, abs=1e-6)
    assert ally.energy == pytest.approx(0, abs=1e-6)

    Action(
        id="alive_enemies",
        name="Alive Enemies",
        actor_id="actor",
        effects=[GainEnergy(amount=5, target_ref="alive_enemies")],
        ends_turn=False,
    ).execute(state)

    assert enemy.energy == pytest.approx(10, abs=1e-6)
    assert dead_enemy.energy == pytest.approx(5, abs=1e-6)


def test_unknown_target_ref_fails_clearly():
    actor = Unit("actor", "Actor", "ally", 100)
    state = BattleState(units=[actor])

    with pytest.raises(ValueError, match="Unknown target_ref"):
        Action(
            id="bad_ref",
            name="Bad Ref",
            actor_id="actor",
            effects=[GainEnergy(amount=5, target_ref="missing_ref")],
            ends_turn=False,
        ).execute(state)


def test_event_target_ref_can_apply_trigger_effect_to_event_target():
    actor = Unit("actor", "Actor", "ally", 100)
    enemy = Unit("enemy", "Enemy", "enemy", 100, hp=100, max_hp=100)
    state = BattleState(
        units=[actor, enemy],
        triggers=[
            Trigger(
                id="mark_target",
                owner_id="actor",
                event_type="damage_dealt",
                condition={"type": "event_source_is_owner"},
                effects=[
                    AddBuff(
                        id="marked",
                        name="Marked",
                        target_ref="event_target",
                    )
                ],
            )
        ],
    )

    Action(
        id="hit",
        name="Hit",
        actor_id="actor",
        target_ids=["enemy"],
        effects=[DealDamage(amount=1)],
        ends_turn=False,
    ).execute(state)

    assert enemy.get_buff("marked") is not None


def test_event_killer_ref_can_apply_trigger_effect_to_killer():
    owner = Unit("observer", "Observer", "ally", 100)
    killer = Unit("killer", "Killer", "ally", 100)
    enemy = Unit("enemy", "Enemy", "enemy", 100, hp=1, max_hp=1)
    state = BattleState(
        units=[owner, killer, enemy],
        triggers=[
            Trigger(
                id="reward_killer",
                owner_id="observer",
                event_type="unit_defeated",
                condition={"type": "always"},
                effects=[GainEnergy(amount=7, target_ref="event_killer")],
            )
        ],
    )

    Action(
        id="kill",
        name="Kill",
        actor_id="killer",
        target_ids=["enemy"],
        effects=[DealDamage(amount=1)],
        ends_turn=False,
    ).execute(state)

    assert killer.energy == pytest.approx(7, abs=1e-6)
    assert owner.energy == pytest.approx(0, abs=1e-6)
