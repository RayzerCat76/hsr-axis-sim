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


def test_cursor_layer_is_downstream_of_all_accepted_runtime_packages():
    hits = []
    for area in PROTECTED_AREAS:
        for path in (ROOT / "hsr_axis_sim" / area).rglob("*.py"):
            if "runtime_capture_cursors" in path.read_text():
                hits.append(path)
    assert hits == []


def test_cursor_capture_delegates_only_to_arch_008_for_state_capture():
    source = (
        ROOT / "hsr_axis_sim" / "runtime_capture_cursors" / "capture.py"
    ).read_text()
    assert "capture_battle_state_pending_event_slice" in source
    forbidden = (
        "build_legacy_event_trace_artifact",
        "adapt_legacy_event",
        "build_runtime_trace_document",
        "build_runtime_trace_artifact",
        ".clear(",
        ".pop(",
        ".remove(",
        "del state.pending_events",
        "state.pending_events =",
        "dispatch_event",
        "Action(",
        "Timeline.",
    )
    assert all(token not in source for token in forbidden)


def test_cursor_layer_has_no_implicit_current_end_or_state_persistence():
    source = "\n".join(
        path.read_text()
        for path in (ROOT / "hsr_axis_sim" / "runtime_capture_cursors").glob("*.py")
    ).lower()
    assert "len(state.pending_events)" in source
    assert "end_index" in source
    assert "state.capture" not in source
    assert "state.cursor" not in source
    assert "permanent history" not in source


def test_production_lifo_compatibility_behavior_remains_unchanged():
    units = [Unit(name, name, "ally", 100) for name in ("first", "second", "third")]
    state = BattleState(units=units, extra_turn_stack=["first", "second", "third"])
    assert [Timeline.next_turn(state).actor_id for _ in range(3)] == ["third", "second", "first"]
