import json
from pathlib import Path

from hsr_axis_sim.adapters.external_import import (
    load_raw_external_character,
    normalize_external_character,
    write_normalized_character,
)
from hsr_axis_sim.sim import Action, BattleState, DealDamage, ReplayValidator, TurnContext, Unit
from hsr_axis_sim.sim.data_loader import action_from_skill, load_character_spec
from hsr_axis_sim.sim.data_schema import CharacterSpec


ROOT = Path(__file__).resolve().parents[1]
RAW_FIXTURE = ROOT / "data" / "raw" / "external_sample" / "sample_external_character.json"
GOLDEN_REPLAYS_DIR = ROOT / "data" / "golden_replays"


def test_raw_fixture_loads_successfully():
    raw = load_raw_external_character(RAW_FIXTURE)

    assert raw.source == "external_fixture"
    assert raw.source_character_id == "fixture_turn_pull_support"
    assert raw.normalized_id == "imported_turn_pull_support_mvp"
    assert len(raw.skills) == 3


def test_normalization_returns_valid_character_dict():
    raw = load_raw_external_character(RAW_FIXTURE)

    normalized, report = normalize_external_character(raw)

    assert normalized["id"] == "imported_turn_pull_support_mvp"
    assert normalized["metadata"]["importer_task"] == "HSR-AXIS-001Q"
    assert report.skills_imported == 3
    assert len(report.warnings) == 1
    CharacterSpec.from_dict(normalized)


def test_write_normalized_output_and_load_character_spec(tmp_path):
    output_path = tmp_path / "imported_external_character.json"

    report = write_normalized_character(RAW_FIXTURE, output_path)
    loaded = load_character_spec(output_path)

    assert report.normalized_id == "imported_turn_pull_support_mvp"
    assert loaded.id == "imported_turn_pull_support_mvp"
    assert loaded.get_skill("skill").target_type == "single_other_ally"


def test_imported_character_can_build_state_and_execute_skill():
    raw = load_raw_external_character(RAW_FIXTURE)
    normalized, _ = normalize_external_character(raw)
    character = CharacterSpec.from_dict(normalized)
    actor = Unit("imported_support", character.name, "ally", character.base_stats.base_speed)
    ally = Unit("ally", "Ally", "ally", 100, current_av=50)
    enemy = Unit("enemy", "Enemy", "enemy", 100, hp=1000, max_hp=1000)
    state = BattleState(units=[actor, ally, enemy], skill_points=3)
    skill = character.get_skill("skill")

    action = action_from_skill(
        skill,
        actor_id="imported_support",
        target_ids=["ally"],
        state=state,
        validate_targets=True,
    )
    action.execute(state, TurnContext(actor_id="imported_support"))

    assert state.skill_points == 2
    assert ally.current_av == 0
    assert ally.get_buff("imported_turn_pull_buff") is not None


def test_unknown_raw_effect_type_warns_and_is_not_normalized():
    raw = load_raw_external_character(RAW_FIXTURE)
    raw.skills[0].effects.append({"type": "UnknownExternalEffect", "amount": 999})

    normalized, report = normalize_external_character(raw)

    assert any(warning.code == "unsupported_effect" for warning in report.warnings)
    assert all(
        effect["type"] != "UnknownExternalEffect"
        for skill in normalized["skills"]
        for effect in skill["effects"]
    )
    CharacterSpec.from_dict(normalized)


def test_written_import_can_be_loaded_and_basic_action_executes(tmp_path):
    output_path = tmp_path / "imported_external_character.json"
    write_normalized_character(RAW_FIXTURE, output_path)
    character = load_character_spec(output_path)
    actor = Unit("imported_support", character.name, "ally", character.base_stats.base_speed)
    enemy = Unit("enemy", "Enemy", "enemy", 100, hp=1000, max_hp=1000)
    state = BattleState(units=[actor, enemy], skill_points=1)

    action = action_from_skill(
        character.get_skill("basic"),
        actor_id="imported_support",
        target_ids=["enemy"],
        state=state,
        validate_targets=True,
    )
    action.execute(state, TurnContext(actor_id="imported_support"))

    assert state.skill_points == 2
    assert actor.energy == 20
    assert enemy.hp == 800


def test_normalized_fixture_file_is_valid():
    fixture = ROOT / "data" / "imported_samples" / "imported_external_character.json"

    character = load_character_spec(fixture)

    assert character.id == "imported_turn_pull_support_mvp"
    assert character.get_skill("ultimate").skill_type == "ultimate"


def test_existing_golden_replays_still_pass_with_import_adapter():
    validator = ReplayValidator()

    for replay_path in sorted(GOLDEN_REPLAYS_DIR.glob("*.json")):
        result = validator.validate(validator.load_replay(replay_path))
        assert result.passed is True, (replay_path.name, result.mismatches)
