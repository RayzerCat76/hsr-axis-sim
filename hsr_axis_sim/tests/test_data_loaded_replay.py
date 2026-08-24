from pathlib import Path

from hsr_axis_sim.sim import ReplayValidator, Timeline
from hsr_axis_sim.sim.data_loader import action_from_skill, build_battle_state_from_files


ROOT = Path(__file__).resolve().parents[1]
CHARACTERS_DIR = ROOT / "data" / "sample_characters"
TEAM_PATH = ROOT / "data" / "sample_teams" / "bronya_seele_team.json"
DATA_LOADED_REPLAY_PATH = (
    ROOT / "data" / "golden_replays" / "data_loaded_bronya_seele_mvp.json"
)


def test_data_loaded_bronya_seele_flow():
    state, skill_lookup = build_battle_state_from_files(TEAM_PATH, CHARACTERS_DIR)

    first_turn = Timeline.next_turn(state)
    first_action = action_from_skill(
        skill_lookup["seele_like"]["basic"],
        actor_id="seele_like",
        target_ids=["enemy_1"],
    )
    first_action.execute(state, first_turn)

    assert state.extra_turn_stack == ["seele_like"]
    assert state.get_unit("enemy_1").is_alive is False

    extra_turn = Timeline.next_turn(state)
    extra_action = action_from_skill(
        skill_lookup["seele_like"]["skill"],
        actor_id="seele_like",
        target_ids=["enemy_2"],
    )
    extra_action.execute(state, extra_turn)

    assert extra_turn.is_extra_turn is True
    assert state.get_unit("enemy_2").hp == 100
    assert state.skill_points == 3


def test_data_loaded_replay_passes_validator():
    validator = ReplayValidator()
    replay = validator.load_replay(DATA_LOADED_REPLAY_PATH)

    result = validator.validate(replay)

    assert result.passed is True
    assert result.replay_name == "data_loaded_bronya_seele_mvp"
    assert result.checked_steps == 3


def test_data_loaded_replay_fails_clearly_for_illegal_skill_target():
    validator = ReplayValidator()
    replay = validator.load_replay(DATA_LOADED_REPLAY_PATH)
    replay["steps"][0]["target_ids"] = ["bronya_like"]

    result = validator.validate(replay)

    assert result.passed is False
    assert result.checked_steps == 0
    assert any("not an enemy" in mismatch for mismatch in result.mismatches)
