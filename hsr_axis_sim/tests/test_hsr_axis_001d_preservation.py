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
)


def test_batch_runner_is_downstream_of_all_accepted_runtime_packages():
    hits = []
    for area in PROTECTED_AREAS:
        for path in (ROOT / "hsr_axis_sim" / area).rglob("*.py"):
            if "runtime_golden_batches" in path.read_text():
                hits.append(path)
    assert hits == []


def test_batch_runner_delegates_only_to_file_case_boundary():
    source = (ROOT / "hsr_axis_sim" / "runtime_golden_batches" / "run.py").read_text()
    assert "run_golden_replay_file_case" in source
    assert "validate_golden_replay_bytes" not in source
    assert "compare_runtime_trace_documents" not in source
    assert "build_first_divergence_report" not in source
    assert "load_runtime_trace_bytes" not in source


def test_production_lifo_compatibility_behavior_remains_unchanged():
    units = [Unit(name, name, "ally", 100) for name in ("first", "second", "third")]
    state = BattleState(units=units, extra_turn_stack=["first", "second", "third"])
    assert [Timeline.next_turn(state).actor_id for _ in range(3)] == ["third", "second", "first"]
