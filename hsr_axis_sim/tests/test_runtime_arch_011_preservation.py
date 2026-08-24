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
)


def test_handoff_layer_is_downstream_of_all_accepted_runtime_packages():
    hits = []
    for area in PROTECTED_AREAS:
        for path in (ROOT / "hsr_axis_sim" / area).rglob("*.py"):
            if "runtime_stitched_golden_validation" in path.read_text():
                hits.append(path)
    assert hits == []


def test_handoff_delegates_only_to_accepted_golden_validator_for_validation_semantics():
    source = (
        ROOT
        / "hsr_axis_sim"
        / "runtime_stitched_golden_validation"
        / "validate.py"
    ).read_text()
    assert "validate_golden_replay_bytes" in source
    assert "stitch_result.artifact.payload_bytes" in source
    forbidden = (
        "load_runtime_trace_bytes",
        "compare_runtime_trace_documents",
        "build_first_divergence_report",
        "build_runtime_trace_document",
        "build_runtime_trace_artifact",
        "canonical_json_bytes",
        "write_runtime_trace_artifact",
        "capture_battle_state",
        "capture_battle_state_pending_events_from_cursor",
        "stitch_captured_trace_segments",
        "BattleState",
        "Action(",
        "Timeline.",
    )
    assert all(token not in source for token in forbidden)


def test_handoff_has_no_actual_trace_reserialization_or_file_io():
    source = "\n".join(
        path.read_text()
        for path in (
            ROOT / "hsr_axis_sim" / "runtime_stitched_golden_validation"
        ).glob("*.py")
    )
    forbidden = (
        ".encode(",
        ".decode(",
        "json.dumps",
        "json.loads",
        "Path(",
        ".open(",
        ".write_bytes(",
        ".read_bytes(",
    )
    assert all(token not in source for token in forbidden)


def test_production_lifo_compatibility_behavior_remains_unchanged():
    units = [Unit(name, name, "ally", 100) for name in ("first", "second", "third")]
    state = BattleState(units=units, extra_turn_stack=["first", "second", "third"])
    assert [Timeline.next_turn(state).actor_id for _ in range(3)] == ["third", "second", "first"]
