from pathlib import Path

from hsr_axis_sim.sim import BattleState, Timeline, Unit


ROOT = Path(__file__).parents[2]
FIXTURE_NAME = "arch_017_reviewed_action_session_expected.json"
FIXTURE_ID = "arch-017-reviewed-static-action-session"


def test_arch_017_does_not_promote_fixture_into_locked_regression_manifest():
    manifest_path = ROOT / "hsr_axis_sim" / "data" / "regression_manifest.json"
    manifest_text = manifest_path.read_text()
    assert FIXTURE_NAME not in manifest_text
    assert FIXTURE_ID not in manifest_text
    assert "runtime_golden_fixtures" not in manifest_text


def test_arch_017_fixture_directory_contains_data_not_runtime_code():
    fixture_dir = ROOT / "hsr_axis_sim" / "data" / "runtime_golden_fixtures"
    assert (fixture_dir / FIXTURE_NAME).is_file()
    assert list(fixture_dir.glob("*.py")) == []


def test_production_lifo_compatibility_behavior_remains_unchanged():
    units = [Unit(name, name, "ally", 100) for name in ("first", "second", "third")]
    state = BattleState(units=units, extra_turn_stack=["first", "second", "third"])
    assert [Timeline.next_turn(state).actor_id for _ in range(3)] == [
        "third",
        "second",
        "first",
    ]
