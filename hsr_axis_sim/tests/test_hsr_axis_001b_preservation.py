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
)


def test_golden_replay_validator_is_downstream_sidecar_only():
    hits = []
    for area in PROTECTED_AREAS:
        for path in (ROOT / "hsr_axis_sim" / area).rglob("*.py"):
            if "runtime_golden_replays" in path.read_text():
                hits.append(path)
    assert hits == []


def test_validator_composes_accepted_pipeline_instead_of_reimplementing_it():
    source = (ROOT / "hsr_axis_sim" / "runtime_golden_replays" / "validate.py").read_text()
    assert "load_runtime_trace_bytes" in source
    assert "compare_runtime_trace_documents" in source
    assert "build_first_divergence_report" in source
    assert "differences[0]" not in source
    assert "TraceRecordComparisonStatus" not in source


def test_prior_trace_pipeline_contracts_remain_present():
    required = (
        "docs/runtime/RUNTIME_TRACE_EXPORT_V1.md",
        "docs/runtime/RUNTIME_TRACE_LOAD_VALIDATE_V1.md",
        "docs/runtime/RUNTIME_TRACE_COMPARE_V1.md",
        "docs/runtime/RUNTIME_TRACE_FIRST_DIVERGENCE_V1.md",
    )
    assert all((ROOT / path).is_file() for path in required)


def test_production_lifo_compatibility_behavior_remains_unchanged():
    units = [Unit(name, name, "ally", 100) for name in ("first", "second", "third")]
    state = BattleState(units=units, extra_turn_stack=["first", "second", "third"])
    assert [Timeline.next_turn(state).actor_id for _ in range(3)] == ["third", "second", "first"]
