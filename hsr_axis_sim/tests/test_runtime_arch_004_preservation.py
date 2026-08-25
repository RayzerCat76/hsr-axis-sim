import hashlib
from pathlib import Path

from hsr_axis_sim.sim import BattleState, Timeline, Unit


ROOT = Path(__file__).parents[2]
REFERENCE_HASHES = {
    "REFERENCE_RUNTIME_TRACE_LOAD_VALIDATE_HSR_RUNTIME_ARCH_004.md": "09734938828c8cc44e0d9cd776b9ec8738ae39dd7a4d62a0df714c646bce5241",
    "REFERENCE_RUNTIME_TRACE_LOAD_VALIDATE_HSR_RUNTIME_ARCH_004.json": "548313a263f05891b432b51d5833009341f481291f8a30d3a96108f24fcef4f4",
}
# ARCH-019 explicitly authorized runtime_contracts/__init__.py and enums.py.
# ARCH-020 explicitly authorizes runtime_adapters/legacy_events.py. Historical
# ARCH-004 evidence remains pinned and every other upstream source stays exact.
SOURCE_HASHES = {
    "runtime_contracts/contexts.py": "b2cd5c4783dc5fced63a206fcc9723f2c53d499265c2f66870847b25715a3c71",
    "runtime_contracts/events.py": "4146e68bbb27b73355334d4263e920af7c15a814e2df4a738d018798b43",
    "runtime_contracts/gates.py": "529b9bc8233e556902f60a821db5719451c0d5b595616be872e71eb17e4b4941",
    "runtime_contracts/serialization.py": "626a885857b5e7fd90ae5f56ec0ee712bbdca2f28b4f28ea33bbf8be12c0937d",
    "runtime_contracts/trace.py": "ca14ac00a999c3c9ab7dc2ed5e2c9442d4926494feffa2cd4575457fafeb061e",
    "runtime_adapters/__init__.py": "03a14b2c6519750b304e98e437ffe5b3da3efc4e316dd6ce4aae0ab028ad47ad",
    "runtime_exports/__init__.py": "e447a9ad009d05301c7658bd1f81d14e5c956c1eb0732f756bcc6c96a2271177",
    "runtime_exports/enums.py": "488f5d72a3c6b72f9a79aba72947b1c5466cab67c8c0c82618055fc0c575b6a8",
    "runtime_exports/files.py": "79c964d48eb39f0384d1460c472025ffed1b78081f23bf5ddc26c8b2eaa7e6b9",
    "runtime_exports/model.py": "37c2a40cffba3211355ca6ee23137a9a451e3f598b2eba0eef9a2032382658b3",
    "runtime_exports/trace_export.py": "b2b30870a1f3d3d94e10eb29999ab10ce04cf394f45f49807b0cbb4da24cbae2",
}
PRIOR_DOCS = [
    "ARCHITECTURE_CONTRACT_V1.md", "UNRESOLVED_SEMANTICS_V1.json", "LEGACY_EVENT_ADAPTER_V1.md", "LEGACY_EVENT_MAPPING_V1.json",
    "RUNTIME_TRACE_EXPORT_V1.md", "RUNTIME_TRACE_SCHEMA_V1.json",
    "research/HSR_RUNTIME_FRAMEWORK_BASELINE_V1_0.md", "research/HSR_RUNTIME_FORMULA_REGISTRY_V1_0.json",
    "research/HSR_RUNTIME_DEFENSE_TOUGHNESS_PRECISION_MODEL_V1_0.json",
    "research/REFERENCE_LEGACY_EVENT_SURFACE_HSR_RUNTIME_ARCH_002.md",
    "research/REFERENCE_LEGACY_EVENT_SURFACE_HSR_RUNTIME_ARCH_002.json",
    "research/REFERENCE_RUNTIME_TRACE_EXPORT_HSR_RUNTIME_ARCH_003.md", "research/REFERENCE_RUNTIME_TRACE_EXPORT_HSR_RUNTIME_ARCH_003.json",
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_reference_hashes_and_prior_documents():
    research = ROOT / "docs/runtime/research"
    assert {name: digest(research / name) for name in REFERENCE_HASHES} == REFERENCE_HASHES
    assert all((ROOT / "docs/runtime" / name).is_file() for name in PRIOR_DOCS)


def test_existing_sidecars_not_authorized_by_arch_019_or_arch_020_are_unchanged_and_no_production_import():
    assert {name: digest(ROOT / "hsr_axis_sim" / name) for name in SOURCE_HASHES} == SOURCE_HASHES
    hits = []
    for area in ("sim", "search", "regression", "adapters", "real_bindings", "data", "runtime_contracts", "runtime_adapters", "runtime_exports"):
        for path in (ROOT / "hsr_axis_sim" / area).rglob("*.py"):
            if "runtime_loaders" in path.read_text():
                hits.append(path)
    assert hits == []


def test_lifo_behavior_unchanged():
    units = [Unit(name, name, "ally", 100) for name in ("first", "second", "third")]
    state = BattleState(units=units, extra_turn_stack=["first", "second", "third"])
    assert [Timeline.next_turn(state).actor_id for _ in range(3)] == ["third", "second", "first"]
