from dataclasses import FrozenInstanceError

import pytest

from hsr_axis_sim.runtime_adapters import (
    AmbiguousLegacyEventError,
    AmbiguousLegacyEventPolicy,
    LegacyEventAdapterConfig,
    LegacyEventSchemaError,
    UnknownLegacyEventPolicy,
    UnmappedLegacyEventError,
    adapt_legacy_event,
)
from hsr_axis_sim.runtime_contracts import RuntimeEventType
from hsr_axis_sim.sim.events import Event


def config(*, unknown=UnknownLegacyEventPolicy.REJECT, ambiguous=AmbiguousLegacyEventPolicy.REJECT):
    return LegacyEventAdapterConfig("stream", unknown, ambiguous)


def test_config_is_explicit_validated_and_frozen():
    with pytest.raises(TypeError):
        LegacyEventAdapterConfig("stream")
    with pytest.raises(LegacyEventSchemaError):
        LegacyEventAdapterConfig("", UnknownLegacyEventPolicy.REJECT, AmbiguousLegacyEventPolicy.REJECT)
    value = config()
    with pytest.raises(FrozenInstanceError):
        value.stream_id = "other"


@pytest.mark.parametrize(
    ("legacy_type", "data", "runtime_type", "ids"),
    [
        ("action_started", {"actor_id": "actor", "action_id": "action"}, RuntimeEventType.ACTION_START, ("action", "actor", None, None)),
        ("action_finished", {"actor_id": "actor", "action_id": "action"}, RuntimeEventType.ACTION_END, ("action", "actor", None, None)),
        ("turn_started", {"actor_id": "actor", "is_extra_turn": True}, RuntimeEventType.TURN_START, (None, "actor", None, None)),
        ("turn_ended", {"actor_id": "actor", "is_extra_turn": False}, RuntimeEventType.TURN_END, (None, "actor", None, None)),
        ("damage_dealt", {"source_id": "actor", "target_id": "enemy", "amount": 10.25, "formula_parts": {"base": 10.25}, "is_break_damage": False}, RuntimeEventType.DAMAGE_RESOLVED, (None, None, "actor", "enemy")),
        ("weakness_break", {"source_id": "actor", "target_id": "enemy", "formula_parts": {"raw": "10/3"}}, RuntimeEventType.WEAKNESS_BROKEN, (None, None, "actor", "enemy")),
    ],
)
def test_every_bound_event_adapts_exactly(legacy_type, data, runtime_type, ids):
    result = adapt_legacy_event(Event(legacy_type, data), sequence=7, config=config())
    assert result.event_id == "legacy:stream:7"
    assert result.event_type is runtime_type
    assert (result.action_id, result.actor_id, result.source_id, result.target_id) == ids
    assert result.attack_id is None
    assert result.hit_id is None
    assert result.payload["adapter"]["mapping_status"] == "BOUND"
    assert dict(result.payload["legacy_data"]) == data


def test_unknown_policy_preserves_or_rejects_explicitly():
    event = Event("future_event", {"value": 1})
    with pytest.raises(UnmappedLegacyEventError):
        adapt_legacy_event(event, sequence=0, config=config())
    result = adapt_legacy_event(
        event,
        sequence=0,
        config=config(unknown=UnknownLegacyEventPolicy.PRESERVE_AS_CONTENT_DEFINED),
    )
    assert result.event_type is RuntimeEventType.CONTENT_DEFINED
    assert result.payload["adapter"]["mapping_status"] == "UNMAPPED_PRESERVED"
    assert result.payload["adapter"]["mechanic_id"] == "LEGACY_EVENT.UNMAPPED_TYPE"
    assert result.payload["adapter"]["semantic_gap_ids"] == ("LEGACY_EVENT.UNMAPPED_TYPE",)


def test_ambiguous_lifecycle_preserves_or_rejects_without_killer_inference():
    event = Event("unit_defeated", {"killer_id": "actor", "target_id": "enemy"})
    with pytest.raises(AmbiguousLegacyEventError):
        adapt_legacy_event(event, sequence=1, config=config())
    result = adapt_legacy_event(
        event,
        sequence=1,
        config=config(ambiguous=AmbiguousLegacyEventPolicy.PRESERVE_AS_CONTENT_DEFINED),
    )
    assert result.event_type is RuntimeEventType.CONTENT_DEFINED
    assert result.source_id is None
    assert result.target_id == "enemy"
    assert result.payload["legacy_data"]["killer_id"] == "actor"
    assert result.payload["adapter"]["mapping_status"] == "AMBIGUOUS"
    assert result.payload["adapter"]["semantic_gap_ids"] == ("LEGACY_EVENT.UNIT_DEFEATED_LIFECYCLE",)


@pytest.mark.parametrize("sequence", [-1, 1.5, True])
def test_invalid_sequence_rejected(sequence):
    with pytest.raises(LegacyEventSchemaError):
        adapt_legacy_event(Event("future", {}), sequence=sequence, config=config())


def test_malformed_type_data_and_normalized_ids_rejected():
    with pytest.raises(LegacyEventSchemaError):
        adapt_legacy_event(Event("", {}), sequence=0, config=config())
    with pytest.raises(LegacyEventSchemaError):
        adapt_legacy_event(Event("future", []), sequence=0, config=config())
    with pytest.raises(LegacyEventSchemaError):
        adapt_legacy_event(Event("action_started", {"actor_id": "actor"}), sequence=0, config=config())
    with pytest.raises(LegacyEventSchemaError):
        adapt_legacy_event(Event("action_started", {"actor_id": "", "action_id": "a"}), sequence=0, config=config())


@pytest.mark.parametrize("bad", [object(), float("nan"), float("inf")])
def test_unsupported_and_nonfinite_payload_values_are_controlled(bad):
    with pytest.raises(LegacyEventSchemaError):
        adapt_legacy_event(
            Event("future", {"bad": bad}), sequence=0,
            config=config(unknown=UnknownLegacyEventPolicy.PRESERVE_AS_CONTENT_DEFINED),
        )


def test_raw_payload_is_a_defensive_nested_snapshot():
    nested = {"parts": [1, {"raw": "10/3"}]}
    event = Event("future", nested)
    result = adapt_legacy_event(
        event, sequence=0,
        config=config(unknown=UnknownLegacyEventPolicy.PRESERVE_AS_CONTENT_DEFINED),
    )
    nested["parts"][1]["raw"] = "changed"
    nested["new"] = True
    assert result.payload["legacy_data"]["parts"][1]["raw"] == "10/3"
    assert "new" not in result.payload["legacy_data"]
