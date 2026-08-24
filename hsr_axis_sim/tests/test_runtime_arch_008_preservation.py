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


def test_state_capture_is_downstream_of_all_accepted_runtime_packages():
    hits = []
    for area in PROTECTED_AREAS:
        for path in (ROOT / "hsr_axis_sim" / area).rglob("*.py"):
            if "runtime_state_captures" in path.read_text():
                hits.append(path)
    assert hits == []


def test_pending_event_capture_only_reads_slice_and_delegates_to_arch_007():
    source = (
        ROOT / "hsr_axis_sim" / "runtime_state_captures" / "pending_events.py"
    ).read_text()
    assert "state.pending_events[config.start_index : config.end_index]" in source
    assert "build_legacy_event_trace_artifact" in source
    forbidden = (
        ".clear(",
        ".pop(",
        ".remove(",
        "del state.pending_events",
        "state.pending_events =",
        "dispatch_event",
        "adapt_legacy_event_stream",
        "build_runtime_trace_document",
        "build_runtime_trace_artifact",
        "Action(",
        "Timeline.",
    )
    assert all(token not in source for token in forbidden)


def test_capture_source_does_not_claim_pending_events_are_permanent_history():
    source = (
        ROOT / "hsr_axis_sim" / "runtime_state_captures" / "pending_events.py"
    ).read_text().lower()
    assert "history" not in source
    assert "permanent" not in source


def test_production_lifo_compatibility_behavior_remains_unchanged():
    units = [Unit(name, name, "ally", 100) for name in ("first", "second", "third")]
    state = BattleState(units=units, extra_turn_stack=["first", "second", "third"])
    assert [Timeline.next_turn(state).actor_id for _ in range(3)] == ["third", "second", "first"]
