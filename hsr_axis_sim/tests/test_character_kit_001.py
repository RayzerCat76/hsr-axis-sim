from pathlib import Path

import pytest

from hsr_axis_sim.sim import ReplayValidator, TargetValidationError, TurnContext
from hsr_axis_sim.sim.data_loader import (
    action_from_skill,
    build_battle_state_from_team,
    load_character_specs_from_dir,
)
from hsr_axis_sim.sim.data_schema import TeamSpec, UnitInstanceSpec


ROOT = Path(__file__).resolve().parents[1]
KIT_DIR = ROOT / "data" / "character_kits" / "kit_001_mechanic_representatives"
KIT_REPLAY_PATH = ROOT / "data" / "golden_replays" / "character_kit_001_mvp.json"


SUPPORTED_TARGET_TYPES = {
    "all_allies",
    "all_enemies",
    "none",
    "self",
    "single_ally",
    "single_any",
    "single_enemy",
    "single_other_ally",
}


def load_kit_state(unit_refs, skill_points=3):
    characters = load_character_specs_from_dir(KIT_DIR)
    team = TeamSpec(
        id="test_team",
        name="Test Team",
        unit_refs=unit_refs,
        initial_skill_points=skill_points,
        max_skill_points=5,
    )
    return build_battle_state_from_team(team, characters)


def test_kit_001_characters_load_from_json():
    characters = load_character_specs_from_dir(KIT_DIR)

    assert {
        "break_support_mvp",
        "energy_battery_support_mvp",
        "kill_chain_carry_mvp",
        "training_enemy_mvp",
        "turn_pull_support_mvp",
    }.issubset(characters)
    for character in characters.values():
        assert character.skills
        for skill in character.skills:
            assert skill.id
            assert skill.target_type in SUPPORTED_TARGET_TYPES
            assert skill.effects is not None


def test_kill_chain_carry_grants_extra_turn_on_kill():
    state, skills = load_kit_state(
        [
            UnitInstanceSpec(
                character_id="kill_chain_carry_mvp",
                unit_id="carry",
                team="ally",
                initial_current_av=0,
            ),
            UnitInstanceSpec(
                character_id="training_enemy_mvp",
                unit_id="enemy",
                team="enemy",
                initial_hp=700,
                initial_toughness=60,
            ),
        ]
    )
    action = action_from_skill(
        skills["carry"]["skill"],
        actor_id="carry",
        target_ids=["enemy"],
        state=state,
        validate_targets=True,
    )

    action.execute(state, TurnContext(actor_id="carry"))

    assert state.get_unit("enemy").is_alive is False
    assert state.extra_turn_stack == ["carry"]
    assert "trigger:kill_chain_carry_on_kill_extra_turn" in state.logs


def test_turn_pull_support_immediate_actions_selected_ally():
    state, skills = load_kit_state(
        [
            UnitInstanceSpec(
                character_id="turn_pull_support_mvp",
                unit_id="turn_pull",
                team="ally",
                initial_current_av=0,
            ),
            UnitInstanceSpec(
                character_id="kill_chain_carry_mvp",
                unit_id="carry",
                team="ally",
                initial_current_av=50,
            ),
            UnitInstanceSpec(
                character_id="training_enemy_mvp",
                unit_id="enemy",
                team="enemy",
            ),
        ]
    )
    action = action_from_skill(
        skills["turn_pull"]["skill"],
        actor_id="turn_pull",
        target_ids=["carry"],
        state=state,
        validate_targets=True,
    )

    action.execute(state, TurnContext(actor_id="turn_pull"))

    carry = state.get_unit("carry")
    assert carry.current_av == pytest.approx(0, abs=1e-6)
    assert carry.get_buff("turn_pull_damage_buff") is not None


def test_energy_battery_ultimate_grants_energy_to_ally():
    state, skills = load_kit_state(
        [
            UnitInstanceSpec(
                character_id="energy_battery_support_mvp",
                unit_id="battery",
                team="ally",
                initial_energy=100,
            ),
            UnitInstanceSpec(
                character_id="kill_chain_carry_mvp",
                unit_id="carry",
                team="ally",
                initial_energy=90,
            ),
            UnitInstanceSpec(
                character_id="training_enemy_mvp",
                unit_id="enemy",
                team="enemy",
            ),
        ]
    )
    ultimate = skills["battery"]["ultimate"]
    action = action_from_skill(
        ultimate,
        actor_id="battery",
        target_ids=["carry"],
        state=state,
        validate_targets=True,
    )

    action.execute(state, TurnContext(actor_id="battery"))

    assert state.get_unit("battery").energy == pytest.approx(0, abs=1e-6)
    assert state.get_unit("carry").energy == pytest.approx(120, abs=1e-6)
    assert state.get_unit("carry").get_buff("battery_damage_buff") is not None

    with pytest.raises(TargetValidationError, match="not an ally"):
        action_from_skill(
            ultimate,
            actor_id="battery",
            target_ids=["enemy"],
            state=state,
            validate_targets=True,
        )


def test_break_support_increases_toughness_damage():
    state, skills = load_kit_state(
        [
            UnitInstanceSpec(
                character_id="break_support_mvp",
                unit_id="break_support",
                team="ally",
            ),
            UnitInstanceSpec(
                character_id="kill_chain_carry_mvp",
                unit_id="carry",
                team="ally",
            ),
            UnitInstanceSpec(
                character_id="training_enemy_mvp",
                unit_id="enemy",
                team="enemy",
                initial_toughness=60,
            ),
        ]
    )
    support_skill = action_from_skill(
        skills["break_support"]["skill"],
        actor_id="break_support",
        target_ids=[],
        state=state,
        validate_targets=True,
    )
    support_skill.execute(state, TurnContext(actor_id="break_support"))

    carry_basic = action_from_skill(
        skills["carry"]["basic"],
        actor_id="carry",
        target_ids=["enemy"],
        state=state,
        validate_targets=True,
    )
    carry_basic.execute(state, TurnContext(actor_id="carry"))

    assert state.get_unit("enemy").current_toughness == pytest.approx(15, abs=1e-6)


def test_character_kit_001_replay_passes():
    validator = ReplayValidator()
    result = validator.validate(validator.load_replay(KIT_REPLAY_PATH))

    assert result.passed is True
    assert result.checked_steps == 3
