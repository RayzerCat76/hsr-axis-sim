import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).parents[2]
RESEARCH = ROOT / "docs/runtime/research"
HASHES = {
    "HSR_RUNTIME_FRAMEWORK_BASELINE_V1_0.md": "cf6b94fb29ce8ca2cf5e0dbcd125c87a65c026304bf8c68dfdd0a4e7b9074817",
    "HSR_RUNTIME_FORMULA_REGISTRY_V1_0.json": "7adaeb30b38c70c9c32de39925561abdf64ef1415e9fdd57b56026feca6912d9",
    "HSR_RUNTIME_DEFENSE_TOUGHNESS_PRECISION_MODEL_V1_0.json": "cf3e46a7a0a12db73f30bc96837a143061e1a012d66384c43eb20685d6a223b3",
}
UNKNOWN_IDS = sorted([
    "ELATION.GENERIC", "MAX_HP.CHANGE_POLICY", "CONTROL.FROZEN_DAMAGE_FORMULA",
    "DOT.SNAPSHOT_POLICY", "MAX_HP.CURRENT_HP_COUPLING", "MAX_HP.AUTO_CURRENT_HP_CHANGE",
    "TRIGGER.COUNTER_SOURCE_EVENT", "COUNTER.ELIGIBILITY_POLICY", "REMOVE.SELECTION_PRIORITY",
    "BOUNCE.REPEAT_TARGET_POLICY", "PRECISION.DAMAGE_HP_ROUNDING",
    "COUNTER.SHIELD_BARRIER_INTERACTION",
])


def test_research_artifact_hashes_are_exact():
    for name, expected in HASHES.items():
        assert hashlib.sha256((RESEARCH / name).read_bytes()).hexdigest() == expected


def test_formula_registry_version_counts_and_unresolved_derivation():
    registry = json.loads((RESEARCH / "HSR_RUNTIME_FORMULA_REGISTRY_V1_0.json").read_text())
    formulas = registry["formulas"]
    assert registry["metadata"]["version"] == "1.0"
    assert len(formulas) == 200
    assert Counter(item["status"] for item in formulas) == {"CONFIRMED": 107, "PARTIAL": 81, "UNKNOWN": 12}
    unknown = sorted((item for item in formulas if item["status"] == "UNKNOWN"), key=lambda item: item["id"])
    unresolved = json.loads((ROOT / "docs/runtime/UNRESOLVED_SEMANTICS_V1.json").read_text())
    assert len(unresolved) == 12
    assert [item["mechanic_id"] for item in unresolved] == UNKNOWN_IDS
    assert [item["mechanic_id"] for item in unresolved] == [item["id"] for item in unknown]
    assert all(item["evidence_status"] == "UNKNOWN" for item in unresolved)
    assert all(item["binding_status"] == "UNRESOLVED" for item in unresolved)
    assert all(item["selected_policy"] is None for item in unresolved)
    assert all(item["production_binding_allowed"] is False for item in unresolved)
    assert all(item["source_registry_version"] == "1.0" for item in unresolved)
    assert [item["notes"] for item in unresolved] == [item["notes"] for item in unknown]
