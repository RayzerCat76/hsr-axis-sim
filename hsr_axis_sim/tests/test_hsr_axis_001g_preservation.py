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
)


def test_manifest_run_layer_is_downstream_of_all_accepted_runtime_packages():
    hits = []
    for area in PROTECTED_AREAS:
        for path in (ROOT / "hsr_axis_sim" / area).rglob("*.py"):
            if "runtime_golden_manifest_runs" in path.read_text():
                hits.append(path)
    assert hits == []


def test_manifest_run_layer_only_composes_001f_and_001d_boundaries():
    source = (
        ROOT / "hsr_axis_sim" / "runtime_golden_manifest_runs" / "run.py"
    ).read_text()
    assert "load_golden_replay_manifest_file" in source
    assert "run_golden_replay_batch" in source
    assert "load_golden_replay_manifest_bytes" not in source
    assert "run_golden_replay_file_case" not in source
    assert "validate_golden_replay_bytes" not in source
    assert "compare_runtime_trace_documents" not in source
    assert "build_first_divergence_report" not in source


def test_manifest_run_layer_has_no_discovery_retry_or_parallel_execution_hooks():
    source = (
        ROOT / "hsr_axis_sim" / "runtime_golden_manifest_runs" / "run.py"
    ).read_text()
    forbidden = ("glob(", "rglob(", "ThreadPool", "ProcessPool", "retry", "sleep(")
    assert all(token not in source for token in forbidden)


def test_production_lifo_compatibility_behavior_remains_unchanged():
    units = [Unit(name, name, "ally", 100) for name in ("first", "second", "third")]
    state = BattleState(units=units, extra_turn_stack=["first", "second", "third"])
    assert [Timeline.next_turn(state).actor_id for _ in range(3)] == ["third", "second", "first"]
