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


def test_stitcher_is_downstream_of_all_accepted_runtime_packages():
    hits = []
    for area in PROTECTED_AREAS:
        for path in (ROOT / "hsr_axis_sim" / area).rglob("*.py"):
            if "runtime_trace_stitching" in path.read_text():
                hits.append(path)
    assert hits == []


def test_stitcher_uses_already_adapted_events_and_only_existing_exporter_builders():
    stitch_source = (
        ROOT / "hsr_axis_sim" / "runtime_trace_stitching" / "stitch.py"
    ).read_text()
    model_source = (
        ROOT / "hsr_axis_sim" / "runtime_trace_stitching" / "model.py"
    ).read_text()
    combined = stitch_source + "\n" + model_source

    assert "record.event" in model_source
    assert "build_runtime_trace_document" in stitch_source
    assert "build_runtime_trace_artifact" in stitch_source
    forbidden = (
        "adapt_legacy_event",
        "build_legacy_event_trace_artifact",
        "capture_battle_state_pending_event_slice",
        "capture_battle_state_pending_events_from_cursor",
        "pending_events",
        "BattleState",
        "Action(",
        "Timeline.",
        "compare_runtime_trace_documents",
        "validate_golden",
        "write_runtime_trace_artifact",
        ".sort(",
        "sorted(",
    )
    assert all(token not in combined for token in forbidden)


def test_stitcher_does_not_renumber_or_mutate_runtime_events():
    source = "\n".join(
        path.read_text()
        for path in (ROOT / "hsr_axis_sim" / "runtime_trace_stitching").glob("*.py")
    )
    forbidden = (
        "event.sequence =",
        "record.sequence =",
        "replace(event",
        "RuntimeEvent(",
        "event_id=",
    )
    assert all(token not in source for token in forbidden)


def test_production_lifo_compatibility_behavior_remains_unchanged():
    units = [Unit(name, name, "ally", 100) for name in ("first", "second", "third")]
    state = BattleState(units=units, extra_turn_stack=["first", "second", "third"])
    assert [Timeline.next_turn(state).actor_id for _ in range(3)] == ["third", "second", "first"]
