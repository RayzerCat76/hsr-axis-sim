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
)


def test_arch_005_is_sidecar_only_and_not_imported_by_existing_runtime_areas():
    hits = []
    for area in PROTECTED_AREAS:
        for path in (ROOT / "hsr_axis_sim" / area).rglob("*.py"):
            if "runtime_comparators" in path.read_text():
                hits.append(path)
    assert hits == []


def test_prior_trace_pipeline_docs_remain_present():
    required = (
        "docs/runtime/ARCHITECTURE_CONTRACT_V1.md",
        "docs/runtime/LEGACY_EVENT_ADAPTER_V1.md",
        "docs/runtime/RUNTIME_TRACE_EXPORT_V1.md",
        "docs/runtime/RUNTIME_TRACE_SCHEMA_V1.json",
        "docs/runtime/RUNTIME_TRACE_LOAD_VALIDATE_V1.md",
        "docs/runtime/RUNTIME_TRACE_LOAD_SCHEMA_V1.json",
    )
    assert all((ROOT / path).is_file() for path in required)


def test_production_lifo_compatibility_behavior_remains_unchanged():
    units = [Unit(name, name, "ally", 100) for name in ("first", "second", "third")]
    state = BattleState(units=units, extra_turn_stack=["first", "second", "third"])
    assert [Timeline.next_turn(state).actor_id for _ in range(3)] == ["third", "second", "first"]
