from pathlib import Path

from hsr_axis_sim.sim import BattleState, Timeline, Unit


ROOT = Path(__file__).parents[2]
FIXTURE_NAME = "arch_017_reviewed_action_session_expected.json"
FIXTURE_ID = "arch-017-reviewed-static-action-session"
EXPECTED_SHA256 = "f672ffaac9ef9296e4982a6fb61f4d0257b5c0506412bcf54eb1768334118c66"


def test_arch_017_fixture_is_referenced_by_locked_regression_only_after_arch_018():
    manifest_path = ROOT / "hsr_axis_sim" / "data" / "regression_manifest.json"
    manifest_text = manifest_path.read_text()
    assert FIXTURE_NAME in manifest_text
    assert FIXTURE_ID in manifest_text
    assert EXPECTED_SHA256 in manifest_text
    assert '"runtime_action_sessions"' in manifest_text


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
