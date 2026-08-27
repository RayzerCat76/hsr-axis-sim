import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from hsr_axis_sim.runtime_adapters import LEGACY_EVENT_MAPPINGS
from hsr_axis_sim.runtime_contracts import BindingStatus, EvidenceStatus, RuntimeEventType


ROOT = Path(__file__).parents[2]
HISTORICAL_EXPECTED = {
    "action_finished": (RuntimeEventType.ACTION_END, {"action_id": "action_id", "actor_id": "actor_id"}),
    "action_started": (RuntimeEventType.ACTION_START, {"action_id": "action_id", "actor_id": "actor_id"}),
    "damage_dealt": (RuntimeEventType.DAMAGE_RESOLVED, {"source_id": "source_id", "target_id": "target_id"}),
    "energy_changed": (
        RuntimeEventType.ENERGY_CHANGED,
        {"action_id": "action_id", "actor_id": "actor_id", "target_id": "unit_id"},
    ),
    "skill_points_changed": (
        RuntimeEventType.SKILL_POINTS_CHANGED,
        {"action_id": "action_id", "actor_id": "actor_id"},
    ),
    "turn_ended": (RuntimeEventType.TURN_END, {"actor_id": "actor_id"}),
    "turn_started": (RuntimeEventType.TURN_START, {"actor_id": "actor_id"}),
    "unit_defeated": (RuntimeEventType.CONTENT_DEFINED, {"target_id": "target_id"}),
    "weakness_break": (RuntimeEventType.WEAKNESS_BROKEN, {"source_id": "source_id", "target_id": "target_id"}),
}
ARCH_031_EXPECTED = {
    "action_advanced": (
        RuntimeEventType.ACTION_VALUE_ADVANCED,
        {"action_id": "action_id", "actor_id": "actor_id", "target_id": "target_id"},
    ),
}
ARCH_034_EXPECTED = {
    "action_delayed": (
        RuntimeEventType.ACTION_VALUE_DELAYED,
        {"action_id": "action_id", "actor_id": "actor_id", "target_id": "target_id"},
    ),
}
ARCH_037_EXPECTED = {
    "speed_changed": (
        RuntimeEventType.SPEED_CHANGED,
        {"action_id": "action_id", "actor_id": "actor_id", "target_id": "target_id"},
    ),
}
ARCH_040_EXPECTED = {
    "action_immediate": (
        RuntimeEventType.ACTION_VALUE_IMMEDIATE,
        {"action_id": "action_id", "actor_id": "actor_id", "target_id": "target_id"},
    ),
}
ARCH_043_EXPECTED = {
    "extra_turn_queued": (
        RuntimeEventType.EXTRA_TURN_QUEUED,
        {"action_id": "action_id", "actor_id": "actor_id", "target_id": "target_id"},
    ),
}
CURRENT_EXPECTED = {
    **HISTORICAL_EXPECTED,
    **ARCH_031_EXPECTED,
    **ARCH_034_EXPECTED,
    **ARCH_037_EXPECTED,
    **ARCH_040_EXPECTED,
    **ARCH_043_EXPECTED,
}


def test_exact_immutable_mapping_registry():
    assert list(LEGACY_EVENT_MAPPINGS) == sorted(CURRENT_EXPECTED)
    assert len(LEGACY_EVENT_MAPPINGS) == 14
    for legacy_type, (runtime_type, fields) in CURRENT_EXPECTED.items():
        mapping = LEGACY_EVENT_MAPPINGS[legacy_type]
        assert mapping.runtime_event_type is runtime_type
        assert dict(mapping.normalized_field_map) == fields
        with pytest.raises(TypeError):
            mapping.normalized_field_map["new"] = "new"
        with pytest.raises(FrozenInstanceError):
            mapping.notes = "changed"
    with pytest.raises(TypeError):
        LEGACY_EVENT_MAPPINGS["new"] = object()


def test_thirteen_bound_contracts_and_one_unresolved_lifecycle():
    bound = [mapping for mapping in LEGACY_EVENT_MAPPINGS.values() if mapping.legacy_event_type != "unit_defeated"]
    assert len(bound) == 13
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


def test_arch_002_mapping_document_remains_exact_historical_projection():
    document = json.loads((ROOT / "docs/runtime/LEGACY_EVENT_MAPPING_V1.json").read_text())
    assert len(document) == 9
    assert [item["legacy_event_type"] for item in document] == sorted(HISTORICAL_EXPECTED)
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


def test_later_runtime_mappings_are_additive_not_backfilled_into_arch_002_document():
    assert "action_advanced" in LEGACY_EVENT_MAPPINGS
    assert "action_delayed" in LEGACY_EVENT_MAPPINGS
    assert "speed_changed" in LEGACY_EVENT_MAPPINGS
    assert "action_immediate" in LEGACY_EVENT_MAPPINGS
    assert "extra_turn_queued" in LEGACY_EVENT_MAPPINGS
    document = json.loads((ROOT / "docs/runtime/LEGACY_EVENT_MAPPING_V1.json").read_text())
    historical_types = {item["legacy_event_type"] for item in document}
    assert "action_advanced" not in historical_types
    assert "action_delayed" not in historical_types
    assert "speed_changed" not in historical_types
    assert "action_immediate" not in historical_types
    assert "extra_turn_queued" not in historical_types
