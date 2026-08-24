import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from hsr_axis_sim.runtime_adapters import LEGACY_EVENT_MAPPINGS
from hsr_axis_sim.runtime_contracts import BindingStatus, EvidenceStatus, RuntimeEventType


ROOT = Path(__file__).parents[2]
EXPECTED = {
    "action_finished": (RuntimeEventType.ACTION_END, {"action_id": "action_id", "actor_id": "actor_id"}),
    "action_started": (RuntimeEventType.ACTION_START, {"action_id": "action_id", "actor_id": "actor_id"}),
    "damage_dealt": (RuntimeEventType.DAMAGE_RESOLVED, {"source_id": "source_id", "target_id": "target_id"}),
    "turn_ended": (RuntimeEventType.TURN_END, {"actor_id": "actor_id"}),
    "turn_started": (RuntimeEventType.TURN_START, {"actor_id": "actor_id"}),
    "unit_defeated": (RuntimeEventType.CONTENT_DEFINED, {"target_id": "target_id"}),
    "weakness_break": (RuntimeEventType.WEAKNESS_BROKEN, {"source_id": "source_id", "target_id": "target_id"}),
}


def test_exact_immutable_mapping_registry():
    assert list(LEGACY_EVENT_MAPPINGS) == sorted(EXPECTED)
    assert len(LEGACY_EVENT_MAPPINGS) == 7
    for legacy_type, (runtime_type, fields) in EXPECTED.items():
        mapping = LEGACY_EVENT_MAPPINGS[legacy_type]
        assert mapping.runtime_event_type is runtime_type
        assert dict(mapping.normalized_field_map) == fields
        with pytest.raises(TypeError):
            mapping.normalized_field_map["new"] = "new"
        with pytest.raises(FrozenInstanceError):
            mapping.notes = "changed"
    with pytest.raises(TypeError):
        LEGACY_EVENT_MAPPINGS["new"] = object()


def test_six_bound_contracts_and_one_unresolved_lifecycle():
    bound = [mapping for mapping in LEGACY_EVENT_MAPPINGS.values() if mapping.legacy_event_type != "unit_defeated"]
    assert len(bound) == 6
    for mapping in bound:
        contract = mapping.semantic_contract
        assert contract.evidence_status is EvidenceStatus.CONFIRMED
        assert contract.binding_status is BindingStatus.BOUND
        assert contract.selected_policy == mapping.runtime_event_type.value
        assert contract.source_refs
    lifecycle = LEGACY_EVENT_MAPPINGS["unit_defeated"]
    assert lifecycle.runtime_event_type is RuntimeEventType.CONTENT_DEFINED
    assert lifecycle.semantic_contract.mechanic_id == "LEGACY_EVENT.UNIT_DEFEATED_LIFECYCLE"
    assert lifecycle.semantic_contract.evidence_status is EvidenceStatus.UNKNOWN
    assert lifecycle.semantic_contract.binding_status is BindingStatus.UNRESOLVED
    assert lifecycle.semantic_contract.selected_policy is None


def test_mapping_document_is_exact_sorted_projection():
    document = json.loads((ROOT / "docs/runtime/LEGACY_EVENT_MAPPING_V1.json").read_text())
    assert len(document) == 7
    assert [item["legacy_event_type"] for item in document] == sorted(EXPECTED)
    for item in document:
        mapping = LEGACY_EVENT_MAPPINGS[item["legacy_event_type"]]
        contract = mapping.semantic_contract
        assert item["runtime_event_type"] == mapping.runtime_event_type.value
        assert item["mechanic_id"] == contract.mechanic_id
        assert item["evidence_status"] == contract.evidence_status.value
        assert item["binding_status"] == contract.binding_status.value
        assert item["selected_policy"] == contract.selected_policy
        assert item["normalized_field_map"] == dict(mapping.normalized_field_map)
        assert item["source_refs"] == list(contract.source_refs)
