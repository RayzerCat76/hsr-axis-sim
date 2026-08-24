import hashlib
from pathlib import Path

from hsr_axis_sim.sim import BattleState, Timeline, Unit


ROOT = Path(__file__).parents[2]
REFERENCE_HASHES = {
    "REFERENCE_RUNTIME_TRACE_EXPORT_HSR_RUNTIME_ARCH_003.md": "fad9697cda084cbcb84d98e81588181548e08806a8c1a83ebe3a28a6441894b8",
    "REFERENCE_RUNTIME_TRACE_EXPORT_HSR_RUNTIME_ARCH_003.json": "5adea3181e488cc9e74e3ee73a483a8107f59b13d8abb8e7f2071be6cacf48ea",
}
# ARCH-019 explicitly authorizes additive changes to runtime_contracts/__init__.py
# and runtime_contracts/enums.py. All other ARCH-003 upstream sources stay pinned.
SOURCE_HASHES = {
    "runtime_contracts/contexts.py": "b2cd5c4783dc5fced63a206fcc9723f2c53d499265c2f66870847b25715a3c71",
    "runtime_contracts/events.py": "4146e68bbb27b733db13355334d4263e920af7c15a814e2df4a738d018798b43",
    "runtime_contracts/gates.py": "529b9bc8233e556902f60a821db5719451c0d5b595616be872e71eb17e4b4941",
    "runtime_contracts/serialization.py": "626a885857b5e7fd90ae5f56ec0ee712bbdca2f28b4f28ea33bbf8be12c0937d",
    "runtime_contracts/trace.py": "ca14ac00a999c3c9ab7dc2ed5e2c9442d4926494feffa2cd4575457fafeb061e",
    "runtime_adapters/__init__.py": "03a14b2c6519750b304e98e437ffe5b3da3efc4e316dd6ce4aae0ab028ad47ad",
    "runtime_adapters/legacy_events.py": "fcc6ba8367b0ec39324670c159d80640ed7819aadf439df733d116bd9baf2605",
}
PRIOR_DOCS = [
    "ARCHITECTURE_CONTRACT_V1.md", "UNRESOLVED_SEMANTICS_V1.json",
    "LEGACY_EVENT_ADAPTER_V1.md", "LEGACY_EVENT_MAPPING_V1.json",
    "research/HSR_RUNTIME_FRAMEWORK_BASELINE_V1_0.md",
    "research/HSR_RUNTIME_FORMULA_REGISTRY_V1_0.json",
    "research/HSR_RUNTIME_DEFENSE_TOUGHNESS_PRECISION_MODEL_V1_0.json",
    "research/REFERENCE_LEGACY_EVENT_SURFACE_HSR_RUNTIME_ARCH_002.md",
    "research/REFERENCE_LEGACY_EVENT_SURFACE_HSR_RUNTIME_ARCH_002.json",
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_arch_003_reference_hashes_and_prior_documents():
    research = ROOT / "docs/runtime/research"
    assert {name: digest(research / name) for name in REFERENCE_HASHES} == REFERENCE_HASHES
    assert all((ROOT / "docs/runtime" / name).is_file() for name in PRIOR_DOCS)


def test_contract_and_adapter_sources_not_authorized_by_arch_019_are_unchanged():
    assert {name: digest(ROOT / "hsr_axis_sim" / name) for name in SOURCE_HASHES} == SOURCE_HASHES


def test_no_existing_production_module_imports_runtime_exports():
    hits = []
    for area in ("sim", "search", "regression", "adapters", "real_bindings", "data", "runtime_contracts", "runtime_adapters"):
        for path in (ROOT / "hsr_axis_sim" / area).rglob("*.py"):
            if "runtime_exports" in path.read_text():
                hits.append(path)
    assert hits == []


def test_existing_extra_turn_stack_remains_lifo():
    units = [Unit(name, name, "ally", 100) for name in ("first", "second", "third")]
    state = BattleState(units=units, extra_turn_stack=["first", "second", "third"])
    assert [Timeline.next_turn(state).actor_id for _ in range(3)] == ["third", "second", "first"]
