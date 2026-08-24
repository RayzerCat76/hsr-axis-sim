from pathlib import Path

from hsr_axis_sim.sim import BattleState, Timeline, Unit


ROOT = Path(__file__).parents[2]
PROTECTED_AREAS = (
    "sim",
    "search",
    "regression",
    "adapters",
    "real_bindings",
    "data",
    "runtime_contracts",
    "runtime_adapters",
    "runtime_exports",
    "runtime_trace_bridges",
    "runtime_state_captures",
    "runtime_capture_cursors",
    "runtime_trace_stitching",
    "runtime_stitched_golden_validation",
    "runtime_action_captures",
    "runtime_action_sessions",
    "runtime_session_stitching",
    "runtime_loaders",
    "runtime_comparators",
    "runtime_divergence",
    "runtime_golden_replays",
    "runtime_golden_cases",
    "runtime_golden_batches",
    "runtime_golden_manifests",
    "runtime_golden_manifest_files",
    "runtime_golden_manifest_runs",
)


def test_session_golden_handoff_is_downstream_of_all_accepted_packages():
    hits = []
    for area in PROTECTED_AREAS:
        for path in (ROOT / "hsr_axis_sim" / area).rglob("*.py"):
            if "runtime_session_golden_validation" in path.read_text():
                hits.append(path)
    assert hits == []


def test_handoff_delegates_only_to_arch_011_boundary():
    source = (
        ROOT / "hsr_axis_sim" / "runtime_session_golden_validation" / "validate.py"
    ).read_text()
    assert "validate_stitched_actual_against_golden" in source
    forbidden = (
        "validate_golden_replay_bytes",
        "load_runtime_trace_bytes",
        "compare_runtime_trace_documents",
        "build_first_divergence_report",
        "stitch_captured_trace_segments",
        "stitch_successful_action_session",
        "run_multi_action_capture_session",
        "execute_action_and_capture_pending_events",
        "Action.execute",
        "BattleState",
        "Timeline.next_turn",
        "build_runtime_trace_document",
        "build_runtime_trace_artifact",
        "write_runtime_trace_artifact",
        ".sort(",
        "sorted(",
    )
    assert all(token not in source for token in forbidden)


def test_handoff_does_not_construct_or_rewrite_trace_or_event_bytes():
    source = "\n".join(
        path.read_text()
        for path in (
            ROOT / "hsr_axis_sim" / "runtime_session_golden_validation"
        ).glob("*.py")
    )
    forbidden = (
        "Event(",
        "RuntimeEvent(",
        "payload_bytes=",
        ".encode(",
        ".decode(",
        "event.sequence =",
        "record.sequence =",
        "event_id=",
    )
    assert all(token not in source for token in forbidden)


def test_production_lifo_compatibility_behavior_remains_unchanged():
    units = [Unit(name, name, "ally", 100) for name in ("first", "second", "third")]
    state = BattleState(units=units, extra_turn_stack=["first", "second", "third"])
    assert [Timeline.next_turn(state).actor_id for _ in range(3)] == [
        "third",
        "second",
        "first",
    ]
