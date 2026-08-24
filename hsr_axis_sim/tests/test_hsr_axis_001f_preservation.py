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
)


def test_manifest_file_loader_is_downstream_of_all_accepted_runtime_packages():
    hits = []
    for area in PROTECTED_AREAS:
        for path in (ROOT / "hsr_axis_sim" / area).rglob("*.py"):
            if "runtime_golden_manifest_files" in path.read_text():
                hits.append(path)
    assert hits == []


def test_manifest_file_loader_delegates_manifest_semantics_only_to_001e_and_does_not_execute_batch():
    source = (
        ROOT / "hsr_axis_sim" / "runtime_golden_manifest_files" / "load.py"
    ).read_text()
    assert "load_golden_replay_manifest_bytes" in source
    assert "run_golden_replay_batch" not in source
    assert "run_golden_replay_file_case" not in source
    assert "validate_golden_replay_bytes" not in source
    assert "compare_runtime_trace_documents" not in source
    assert "build_first_divergence_report" not in source


def test_prior_golden_pipeline_contract_documents_remain_present():
    expected = (
        "docs/runtime/GOLDEN_REPLAY_VALIDATOR_V1.md",
        "docs/runtime/GOLDEN_REPLAY_FILE_CASE_V1.md",
        "docs/runtime/GOLDEN_REPLAY_BATCH_V1.md",
        "docs/runtime/GOLDEN_REPLAY_MANIFEST_V1.md",
    )
    assert all((ROOT / path).is_file() for path in expected)


def test_production_lifo_compatibility_behavior_remains_unchanged():
    units = [Unit(name, name, "ally", 100) for name in ("first", "second", "third")]
    state = BattleState(units=units, extra_turn_stack=["first", "second", "third"])
    assert [Timeline.next_turn(state).actor_id for _ in range(3)] == ["third", "second", "first"]
