from pathlib import Path

import pytest

from hsr_axis_sim.sim import (
    EnemyAIPlan,
    EnemyPatternStep,
    ReplayValidator,
    Timeline,
    TurnContext,
    choose_enemy_action,
    execute_enemy_ai_action,
)
from hsr_axis_sim.sim.data_loader import (
    build_battle_state_from_files,
    load_character_spec,
)


ROOT = Path(__file__).resolve().parents[1]
CHARACTERS_DIR = ROOT / "data" / "sample_characters"
TEAM_PATH = ROOT / "data" / "sample_teams" / "bronya_seele_team.json"
ENEMY_AI_TEAM_PATH = ROOT / "data" / "sample_teams" / "enemy_ai_team.json"
ENEMY_AI_REPLAY_PATH = ROOT / "data" / "golden_replays" / "enemy_ai_mvp.json"
GOLDEN_REPLAYS_DIR = ROOT / "data" / "golden_replays"


def loaded_state(team_path=TEAM_PATH):
    return build_battle_state_from_files(team_path, CHARACTERS_DIR)


def test_enemy_ai_schema_parses_successfully():
    character = load_character_spec(CHARACTERS_DIR / "generic_enemy.json")

    assert character.enemy_ai is not None
    assert character.enemy_ai["pattern"][0]["skill_id"] == "basic"


def test_character_without_enemy_ai_still_loads():
    character = load_character_spec(CHARACTERS_DIR / "bronya_like.json")

    assert character.enemy_ai is None


def test_state_builder_attaches_enemy_ai_plan_per_enemy_unit_instance():
    state, _ = loaded_state()

    assert sorted(state.enemy_ai_plans) == ["enemy_1", "enemy_2"]
    assert state.enemy_ai_cursors == {"enemy_1": 0, "enemy_2": 0}
    assert state.enemy_ai_plans["enemy_1"] is not state.enemy_ai_plans["enemy_2"]


def test_choose_enemy_action_does_not_mutate_cursor_or_state():
    state, skill_lookup = loaded_state()
    before = {
        "cursor": dict(state.enemy_ai_cursors),
        "hps": {unit.id: unit.hp for unit in state.units},
        "current_avs": {unit.id: unit.current_av for unit in state.units},
        "skill_points": state.skill_points,
    }

    choice = choose_enemy_action(state, skill_lookup, "enemy_1")

    assert choice.skill_id == "basic"
    assert choice.target_ids == ["seele_like"]
    assert state.enemy_ai_cursors == before["cursor"]
    assert {unit.id: unit.hp for unit in state.units} == before["hps"]
    assert {unit.id: unit.current_av for unit in state.units} == before["current_avs"]
    assert state.skill_points == before["skill_points"]


def test_first_legal_target_strategy():
    state, skill_lookup = loaded_state()

    choice = choose_enemy_action(state, skill_lookup, "enemy_1")

    assert choice.skill_id == "basic"
    assert choice.target_ids == ["seele_like"]


def test_lowest_hp_legal_target_strategy():
    state, skill_lookup = loaded_state()
    state.enemy_ai_cursors["enemy_1"] = 1
    state.get_unit("seele_like").hp = 3000
    state.get_unit("bronya_like").hp = 900

    choice = choose_enemy_action(state, skill_lookup, "enemy_1")

    assert choice.skill_id == "heavy"
    assert choice.target_ids == ["bronya_like"]


def test_explicit_target_strategy_validates_legality():
    state, skill_lookup = loaded_state()
    state.enemy_ai_plans["enemy_1"] = EnemyAIPlan(
        pattern=[
            EnemyPatternStep(
                skill_id="basic",
                target_strategy="explicit",
                target_ids=["bronya_like"],
            )
        ]
    )

    choice = choose_enemy_action(state, skill_lookup, "enemy_1")
    assert choice.target_ids == ["bronya_like"]

    state.enemy_ai_plans["enemy_1"] = EnemyAIPlan(
        pattern=[
            EnemyPatternStep(
                skill_id="basic",
                target_strategy="explicit",
                target_ids=["enemy_2"],
            )
        ]
    )
    with pytest.raises(ValueError, match="not an enemy"):
        choose_enemy_action(state, skill_lookup, "enemy_1")


def test_forced_rng_target_strategy_uses_and_validates_forced_target():
    state, skill_lookup = loaded_state()
    state.enemy_ai_plans["enemy_1"] = EnemyAIPlan(
        pattern=[
            EnemyPatternStep(
                skill_id="basic",
                target_strategy="forced_rng_target",
            )
        ]
    )

    choice = choose_enemy_action(
        state,
        skill_lookup,
        "enemy_1",
        forced_rng={"enemy_target_id": "bronya_like"},
    )
    assert choice.target_ids == ["bronya_like"]

    with pytest.raises(ValueError, match="not an enemy"):
        choose_enemy_action(
            state,
            skill_lookup,
            "enemy_1",
            forced_rng={"target_id": "enemy_2"},
        )


def test_dead_actor_or_missing_ai_plan_fails_clearly():
    state, skill_lookup = loaded_state()
    state.get_unit("enemy_1").is_alive = False

    with pytest.raises(ValueError, match="not alive"):
        choose_enemy_action(state, skill_lookup, "enemy_1")

    state.get_unit("enemy_1").is_alive = True
    del state.enemy_ai_plans["enemy_1"]
    with pytest.raises(ValueError, match="no enemy AI plan"):
        choose_enemy_action(state, skill_lookup, "enemy_1")


def test_missing_skill_in_pattern_fails_clearly():
    state, skill_lookup = loaded_state()
    state.enemy_ai_plans["enemy_1"] = EnemyAIPlan(
        pattern=[EnemyPatternStep(skill_id="missing")]
    )

    with pytest.raises(ValueError, match="unknown skill"):
        choose_enemy_action(state, skill_lookup, "enemy_1")


def test_execute_enemy_ai_action_increments_cursor_only_after_success():
    state, skill_lookup = loaded_state(ENEMY_AI_TEAM_PATH)
    turn_context = Timeline.next_turn(state)

    choice = execute_enemy_ai_action(
        state,
        skill_lookup,
        "enemy_1",
        turn_context,
    )

    assert choice.skill_id == "basic"
    assert state.enemy_ai_cursors["enemy_1"] == 1
    assert state.get_unit("seele_like").hp == 2900

    state.enemy_ai_plans["enemy_1"] = EnemyAIPlan(
        pattern=[EnemyPatternStep(skill_id="missing")]
    )
    before_cursor = state.enemy_ai_cursors["enemy_1"]
    with pytest.raises(ValueError, match="unknown skill"):
        execute_enemy_ai_action(
            state,
            skill_lookup,
            "enemy_1",
            TurnContext(actor_id="enemy_1"),
        )
    assert state.enemy_ai_cursors["enemy_1"] == before_cursor


def test_execute_enemy_ai_action_requires_matching_turn_context_actor():
    state, skill_lookup = loaded_state()

    with pytest.raises(ValueError, match="must match"):
        execute_enemy_ai_action(
            state,
            skill_lookup,
            "enemy_1",
            TurnContext(actor_id="enemy_2"),
        )


def test_replay_validator_supports_use_enemy_ai():
    validator = ReplayValidator()
    replay = validator.load_replay(ENEMY_AI_REPLAY_PATH)

    result = validator.validate(replay)

    assert result.passed is True
    assert result.checked_steps == 2


def test_all_golden_replays_still_pass_with_enemy_ai():
    validator = ReplayValidator()

    for replay_path in sorted(GOLDEN_REPLAYS_DIR.glob("*.json")):
        result = validator.validate(validator.load_replay(replay_path))
        assert result.passed is True, (replay_path.name, result.mismatches)
