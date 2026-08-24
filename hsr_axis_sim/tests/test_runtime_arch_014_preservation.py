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


def test_session_stitch_handoff_is_downstream_of_all_accepted_packages():
    hits = []
    for area in PROTECTED_AREAS:
        for path in (ROOT / "hsr_axis_sim" / area).rglob("*.py"):
            if "runtime_session_stitching" in path.read_text():
                hits.append(path)
    assert hits == []


def test_handoff_delegates_only_to_arch_010_stitch_boundary():
    source = (
        ROOT / "hsr_axis_sim" / "runtime_session_stitching" / "stitch.py"
    ).read_text()
    assert "stitch_captured_trace_segments" in source
    forbidden = (
        "run_multi_action_capture_session",
        "execute_action_and_capture_pending_events",
        "Action.execute",
        "BattleState",
        "Timeline.next_turn",
        "capture_battle_state",
        "adapt_legacy_event",
        "build_runtime_trace_document",
        "build_runtime_trace_artifact",
        "validate_golden",
        "compare_runtime_trace_documents",
        "write_runtime_trace_artifact",
        ".sort(",
        "sorted(",
    )
    assert all(token not in source for token in forbidden)


def test_handoff_does_not_construct_or_rewrite_runtime_events():
    source = "\n".join(
        path.read_text()
        for path in (ROOT / "hsr_axis_sim" / "runtime_session_stitching").glob("*.py")
    )
    forbidden = (
        "Event(",
        "RuntimeEvent(",
        "event.sequence =",
        "record.sequence =",
        "event_id=",
        "payload_bytes=",
    )
    assert all(token not in source for token in forbidden)


def test_production_lifo_compatibility_behavior_remains_unchanged():
    units = [Unit(name, name, "ally", 100) for name in ("first", "second", "third")]
    state = BattleState(units=units, extra_turn_stack=["first", "second", "third"])
    assert [Timeline.next_turn(state).actor_id for _ in range(3)] == ["third", "second", "first"]
