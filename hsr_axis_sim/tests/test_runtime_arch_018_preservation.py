import hashlib
import inspect
from pathlib import Path

from hsr_axis_sim.regression.manifest import load_regression_manifest
from hsr_axis_sim.regression.runner import _check_runtime_action_session
from hsr_axis_sim.sim import BattleState, Timeline, Unit


ROOT = Path(__file__).parents[2]
MANIFEST_PATH = ROOT / "hsr_axis_sim" / "data" / "regression_manifest.json"
FIXTURE_PATH = (
    ROOT
    / "hsr_axis_sim"
    / "data"
    / "runtime_golden_fixtures"
    / "arch_017_reviewed_action_session_expected.json"
)
FIXTURE_SHA256 = "f672ffaac9ef9296e4982a6fb61f4d0257b5c0506412bcf54eb1768334118c66"


def test_arch_017_static_fixture_bytes_remain_exactly_locked():
    payload = FIXTURE_PATH.read_bytes()
    assert len(payload) == 3013
    assert hashlib.sha256(payload).hexdigest() == FIXTURE_SHA256
    assert not payload.endswith(b"\n")


def test_existing_five_manifest_groups_remain_entry_for_entry_counts():
    manifest = load_regression_manifest(MANIFEST_PATH)
    counts = manifest.counts_by_group()
    assert {
        "replays": counts["replays"],
        "manual": counts["manual"],
        "scenarios": counts["scenarios"],
        "action_sequence_traces": counts["action_sequence_traces"],
        "trace_evidence": counts["trace_evidence"],
    } == {
        "replays": 12,
        "manual": 1,
        "scenarios": 2,
        "action_sequence_traces": 1,
        "trace_evidence": 2,
    }
    assert counts["runtime_action_sessions"] == 1


def test_runtime_action_session_checker_delegates_validation_only_to_arch_016():
    source = inspect.getsource(_check_runtime_action_session)
    assert "run_action_session_validation" in source
    forbidden = (
        "run_multi_action_capture_session",
        "stitch_successful_action_session",
        "validate_successful_session_against_golden",
        "validate_stitched_actual_against_golden",
        "validate_golden_replay_bytes",
        "load_runtime_trace_bytes",
        "compare_runtime_trace_documents",
        "build_first_divergence_report",
        "execute_action_and_capture_pending_events",
        "stitch_captured_trace_segments",
    )
    assert all(token not in source for token in forbidden)


def test_runtime_action_session_checker_does_not_generate_expected_artifact():
    source = inspect.getsource(_check_runtime_action_session)
    forbidden = (
        "build_runtime_trace_document",
        "build_runtime_trace_artifact",
        "canonical_json_bytes",
        "canonical_json_dumps",
        "write_bytes",
        "write_text",
    )
    assert all(token not in source for token in forbidden)
    assert "read_bytes" in source


def test_production_lifo_compatibility_behavior_remains_unchanged():
    units = [Unit(name, name, "ally", 100) for name in ("first", "second", "third")]
    state = BattleState(units=units, extra_turn_stack=["first", "second", "third"])
    assert [Timeline.next_turn(state).actor_id for _ in range(3)] == [
        "third",
        "second",
        "first",
    ]
