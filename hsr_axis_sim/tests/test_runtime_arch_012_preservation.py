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
    "runtime_loaders",
    "runtime_comparators",
    "runtime_divergence",
    "runtime_golden_replays",
    "runtime_golden_cases",
    "runtime_golden_batches",
    "runtime_golden_manifests",
    "runtime_golden_manifest_files",
    "runtime_golden_manifest_runs",
    "runtime_stitched_golden_validation",
)


def test_action_capture_is_downstream_of_all_accepted_packages():
    hits = []
    for area in PROTECTED_AREAS:
        for path in (ROOT / "hsr_axis_sim" / area).rglob("*.py"):
            if "runtime_action_captures" in path.read_text():
                hits.append(path)
    assert hits == []


def test_orchestrator_calls_only_existing_action_and_cursor_capture_boundaries():
    source = (
        ROOT / "hsr_axis_sim" / "runtime_action_captures" / "capture.py"
    ).read_text()
    assert "action.execute(state, turn_context)" in source
    assert "capture_battle_state_pending_events_from_cursor" in source
    forbidden = (
        "Timeline.next_turn",
        "ReplayValidator",
        "validate_golden",
        "compare_runtime_trace_documents",
        "stitch_captured",
        "write_runtime_trace_artifact",
        "pending_events.clear",
        "pending_events.pop",
        "del state.pending_events",
        "state.pending_events = []",
        "try:\n",
        "except ",
    )
    assert all(token not in source for token in forbidden)


def test_orchestrator_does_not_construct_or_reinterpret_events():
    source = "\n".join(
        path.read_text()
        for path in (ROOT / "hsr_axis_sim" / "runtime_action_captures").glob("*.py")
    )
    forbidden = (
        "Event(",
        "RuntimeEvent(",
        "adapt_legacy_event",
        "build_runtime_trace_document",
        "build_runtime_trace_artifact",
        "event_id=",
    )
    assert all(token not in source for token in forbidden)


def test_production_lifo_compatibility_behavior_remains_unchanged():
    units = [Unit(name, name, "ally", 100) for name in ("first", "second", "third")]
    state = BattleState(units=units, extra_turn_stack=["first", "second", "third"])
    assert [Timeline.next_turn(state).actor_id for _ in range(3)] == ["third", "second", "first"]
