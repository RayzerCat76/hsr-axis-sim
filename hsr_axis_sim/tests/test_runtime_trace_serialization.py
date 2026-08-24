import json

import pytest

from hsr_axis_sim.runtime_contracts import (
    ActionContext, ActionFamily, AttackContext, HitContext, PriorityClass,
    QuantizationPolicy, RuntimeEvent, RuntimeEventType, RuntimeTraceRecord,
    SamePriorityPolicy, TargetPolicyKind, TargetRole, TraceNumericValue, TurnKind,
    canonical_json_bytes, canonical_json_dumps,
)


def contexts():
    action = ActionContext("a", "actor", None, None, ActionFamily.NORMAL_TURN, TurnKind.NORMAL, PriorityClass.NORMAL_TURN, SamePriorityPolicy.UNRESOLVED, None, None, None, {})
    attack = AttackContext("atk", "a", "actor", (), TargetPolicyKind.SINGLE, "target", False, False, {})
    hit = HitContext("hit", "atk", 0, "target", TargetRole.PRIMARY, "damage", None, (), {})
    return action, attack, hit


def event(**overrides):
    values = dict(event_id="event", event_type=RuntimeEventType.DAMAGE_RESOLVED, sequence=3, action_id="a", attack_id="atk", hit_id="hit", actor_id="actor", source_id=None, target_id="target", payload={"b": 2, "a": [1, 2]})
    values.update(overrides)
    return RuntimeEvent(**values)


def test_event_envelope_is_validated_and_payload_frozen():
    value = event()
    with pytest.raises(TypeError):
        value.payload["new"] = 1
    with pytest.raises(ValueError):
        event(sequence=-1)
    with pytest.raises(ValueError):
        event(event_id="")


def test_trace_separates_numeric_values_and_is_byte_stable():
    action, attack, hit = contexts()
    numeric = TraceNumericValue("10/3", "3", QuantizationPolicy.DISPLAY_ONLY)
    record = RuntimeTraceRecord(3, event(), action, attack, hit, {"damage": numeric}, ("second", "first"))
    assert record.numeric_values["damage"].raw_value == "10/3"
    assert record.numeric_values["damage"].displayed_value == "3"
    assert record.notes == ("first", "second")
    compact = canonical_json_dumps(record)
    pretty = canonical_json_dumps(record, pretty=True)
    assert compact == canonical_json_dumps(json.loads(compact))
    assert pretty == canonical_json_dumps(json.loads(pretty), pretty=True)
    assert canonical_json_bytes(record) == compact.encode()


def test_nested_context_mismatches_are_rejected():
    action, attack, hit = contexts()
    with pytest.raises(ValueError):
        RuntimeTraceRecord(0, event(), action, AttackContext("atk", "other", "actor", (), TargetPolicyKind.SINGLE, "target", False, False, {}), hit)
    with pytest.raises(ValueError):
        RuntimeTraceRecord(0, event(), action, attack, HitContext("hit", "other", 0, "target", TargetRole.PRIMARY, None, None, (), {}))
    with pytest.raises(ValueError):
        RuntimeTraceRecord(0, event(action_id="other"), action, attack, hit)


def test_negative_trace_sequence_and_unsupported_objects_rejected():
    action, attack, hit = contexts()
    with pytest.raises(ValueError):
        RuntimeTraceRecord(-1, event(), action, attack, hit)
    with pytest.raises(TypeError):
        canonical_json_dumps(object())
