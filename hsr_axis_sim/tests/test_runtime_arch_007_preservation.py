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


def test_trace_bridge_is_downstream_of_all_accepted_runtime_packages():
    hits = []
    for area in PROTECTED_AREAS:
        for path in (ROOT / "hsr_axis_sim" / area).rglob("*.py"):
            if "runtime_trace_bridges" in path.read_text():
                hits.append(path)
    assert hits == []


def test_legacy_bridge_only_composes_accepted_adapter_and_exporter_boundaries():
    source = (ROOT / "hsr_axis_sim" / "runtime_trace_bridges" / "legacy.py").read_text()
    assert "adapt_legacy_event_stream" in source
    assert "build_runtime_trace_document" in source
    assert "build_runtime_trace_artifact" in source
    forbidden = (
        "BattleState",
        "pending_events",
        "dispatch_event",
        "write_runtime_trace_artifact",
        "open(",
        "Path(",
        "run_golden_replay",
        "compare_runtime_trace_documents",
        "build_first_divergence_report",
    )
    assert all(token not in source for token in forbidden)


def test_bridge_does_not_add_or_override_legacy_event_mappings():
    source = (ROOT / "hsr_axis_sim" / "runtime_trace_bridges" / "legacy.py").read_text()
    assert "LEGACY_EVENT_MAPPINGS" not in source
    assert "RuntimeEventType" not in source


def test_production_lifo_compatibility_behavior_remains_unchanged():
    units = [Unit(name, name, "ally", 100) for name in ("first", "second", "third")]
    state = BattleState(units=units, extra_turn_stack=["first", "second", "third"])
    assert [Timeline.next_turn(state).actor_id for _ in range(3)] == ["third", "second", "first"]
