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
    "runtime_session_golden_validation",
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


def test_e2e_orchestrator_is_downstream_of_all_accepted_packages():
    hits = []
    for area in PROTECTED_AREAS:
        for path in (ROOT / "hsr_axis_sim" / area).rglob("*.py"):
            if "runtime_action_session_validation" in path.read_text():
                hits.append(path)
    assert hits == []


def test_orchestrator_calls_only_accepted_arch_013_014_015_boundaries():
    source = (
        ROOT / "hsr_axis_sim" / "runtime_action_session_validation" / "run.py"
    ).read_text()
    assert "run_multi_action_capture_session" in source
    assert "stitch_successful_action_session" in source
    assert "validate_successful_session_against_golden" in source
    forbidden = (
        "execute_action_and_capture_pending_events",
        "Action.execute",
        "Timeline.next_turn",
        "capture_battle_state",
        "adapt_legacy_event",
        "stitch_captured_trace_segments",
        "validate_stitched_actual_against_golden",
        "validate_golden_replay_bytes",
        "load_runtime_trace_bytes",
        "compare_runtime_trace_documents",
        "build_first_divergence_report",
        "build_runtime_trace_document",
        "build_runtime_trace_artifact",
        "write_runtime_trace_artifact",
        ".sort(",
        "sorted(",
    )
    assert all(token not in source for token in forbidden)


def test_orchestrator_does_not_add_exception_wrapping_or_queue_lifecycle_mutation():
    run_source = (
        ROOT / "hsr_axis_sim" / "runtime_action_session_validation" / "run.py"
    ).read_text()
    source = "\n".join(
        path.read_text()
        for path in (
            ROOT / "hsr_axis_sim" / "runtime_action_session_validation"
        ).glob("*.py")
    )
    forbidden = (
        "pending_events.clear",
        "pending_events.pop",
        "pending_events =",
        "deepcopy",
        "copy.deepcopy",
        "Event(",
        "RuntimeEvent(",
        "payload_bytes=",
    )
    assert all(token not in source for token in forbidden)
    assert "except " not in run_source


def test_production_lifo_compatibility_behavior_remains_unchanged():
    units = [Unit(name, name, "ally", 100) for name in ("first", "second", "third")]
    state = BattleState(units=units, extra_turn_stack=["first", "second", "third"])
    assert [Timeline.next_turn(state).actor_id for _ in range(3)] == [
        "third",
        "second",
        "first",
    ]
