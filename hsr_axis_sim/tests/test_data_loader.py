from pathlib import Path

import pytest

from hsr_axis_sim.sim import Action, BattleState, Timeline, TurnContext
from hsr_axis_sim.sim.data_loader import (
    action_from_skill,
    build_battle_state_from_files,
    build_battle_state_from_team,
    instantiate_unit,
    load_character_spec,
    load_character_specs_from_dir,
    load_team_spec,
)
from hsr_axis_sim.sim.data_schema import TeamSpec, UnitInstanceSpec


ROOT = Path(__file__).resolve().parents[1]
CHARACTERS_DIR = ROOT / "data" / "sample_characters"
TEAM_PATH = ROOT / "data" / "sample_teams" / "bronya_seele_team.json"


def test_unit_created_with_correct_stats():
    character = load_character_spec(CHARACTERS_DIR / "seele_like.json")
    unit_ref = UnitInstanceSpec(
        character_id="seele_like",
        unit_id="seele_like",
        team="ally",
        initial_energy=60,
        initial_current_av=0,
    )

    unit = instantiate_unit(character, unit_ref)

    assert unit.id == "seele_like"
    assert unit.atk == 1000
    assert unit.base_speed == 143
    assert unit.energy == 60
    assert unit.current_av == 0


def test_stat_overrides_work():
    character = load_character_spec(CHARACTERS_DIR / "generic_enemy.json")
    unit_ref = UnitInstanceSpec(
        character_id="generic_enemy",
        unit_id="enemy",
        team="enemy",
        stat_overrides={"atk": 500, "base_speed": 120, "weaknesses": ["ice"]},
    )

    unit = instantiate_unit(character, unit_ref)

    assert unit.atk == 500
    assert unit.base_speed == 120
    assert unit.weaknesses == ["ice"]


def test_unit_ref_level_overrides_character_base_level():
    character = load_character_spec(CHARACTERS_DIR / "seele_like.json")
    unit_ref = UnitInstanceSpec(
        character_id="seele_like",
        unit_id="seele_like",
        team="ally",
        level=70,
        stat_overrides={"level": 60},
    )

    unit = instantiate_unit(character, unit_ref)

    assert unit.level == 70


def test_unknown_stat_override_fails_clearly():
    character = load_character_spec(CHARACTERS_DIR / "generic_enemy.json")
    unit_ref = UnitInstanceSpec(
        character_id="generic_enemy",
        unit_id="enemy",
        team="enemy",
        stat_overrides={"unknown_stat": 1},
    )

    with pytest.raises(ValueError, match="Unknown stat override"):
        instantiate_unit(character, unit_ref)


def test_character_owned_trigger_attaches_to_instantiated_unit():
    state, _ = build_battle_state_from_files(TEAM_PATH, CHARACTERS_DIR)

    assert any(
        trigger.id == "seele_like_on_kill_extra_turn"
        and trigger.owner_id == "seele_like"
        for trigger in state.triggers
    )


def test_duplicate_unit_ids_fail_clearly():
    team = load_team_spec(TEAM_PATH)
    team.unit_refs[1] = UnitInstanceSpec(
        character_id="bronya_like",
        unit_id="seele_like",
        team="ally",
    )
    characters = load_character_specs_from_dir(CHARACTERS_DIR)

    with pytest.raises(ValueError, match="Duplicate unit id"):
        build_battle_state_from_team(team, characters)


def test_unknown_character_id_fails_clearly():
    team = TeamSpec(
        id="bad_team",
        name="Bad Team",
        unit_refs=[
            UnitInstanceSpec(
                character_id="missing",
                unit_id="missing_unit",
                team="ally",
            )
        ],
        initial_skill_points=3,
        max_skill_points=5,
    )
    characters = load_character_specs_from_dir(CHARACTERS_DIR)

    with pytest.raises(ValueError, match="Unknown character id"):
        build_battle_state_from_team(team, characters)


def test_skill_spec_becomes_executable_action_and_applies_targets():
    state, skill_lookup = build_battle_state_from_files(TEAM_PATH, CHARACTERS_DIR)
    skill = skill_lookup["seele_like"]["basic"]
    action = action_from_skill(skill, actor_id="seele_like", target_ids=["enemy_1"])

    assert isinstance(action, Action)
    assert action.actor_id == "seele_like"
    assert action.target_ids == ["enemy_1"]

    turn = Timeline.next_turn(state)
    action.execute(state, turn)

    enemy = state.get_unit("enemy_1")
    seele = state.get_unit("seele_like")
    assert enemy.hp == 0
    assert seele.energy == 80
    assert state.skill_points == 4
    assert state.extra_turn_stack == ["seele_like"]


def test_generic_loaded_effects_still_work():
    state, skill_lookup = build_battle_state_from_files(TEAM_PATH, CHARACTERS_DIR)
    bronya_skill = skill_lookup["bronya_like"]["skill"]
    action = action_from_skill(
        bronya_skill,
        actor_id="bronya_like",
        target_ids=["seele_like"],
        state=state,
        validate_targets=True,
    )

    action.execute(state, TurnContext(actor_id="bronya_like"))

    assert state.skill_points == 2
    assert state.get_unit("bronya_like").energy == 110
    assert state.get_unit("seele_like").current_av == 0


def test_action_from_skill_with_validation_normalizes_self_target():
    state, skill_lookup = build_battle_state_from_files(TEAM_PATH, CHARACTERS_DIR)
    wait_skill = skill_lookup["enemy_1"]["wait"]

    action = action_from_skill(
        wait_skill,
        actor_id="enemy_1",
        target_ids=None,
        state=state,
        validate_targets=True,
    )

    assert action.target_ids == ["enemy_1"]
