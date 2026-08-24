import json
from pathlib import Path

import pytest

from hsr_axis_sim.runtime_adapters import (
    AmbiguousLegacyEventPolicy,
    LegacyEventAdapterConfig,
    UnknownLegacyEventPolicy,
    adapt_legacy_event_stream,
)
from hsr_axis_sim.runtime_contracts import RuntimeEvent, RuntimeEventType
from hsr_axis_sim.runtime_exports import (
    DuplicateRuntimeEventIdError,
    EmptyRuntimeTraceError,
    EmptyTracePolicy,
    RuntimeTraceExportSchemaError,
    RuntimeTraceSequenceError,
    TraceExportConfig,
    TraceSequencePolicy,
    build_runtime_trace_artifact,
    build_runtime_trace_document,
    runtime_event_to_trace_record,
)
from hsr_axis_sim.sim import Action, BattleState, DealDamage, Unit


ROOT = Path(__file__).parents[2]


def event(sequence, event_id=None, event_type=RuntimeEventType.ACTION_START, payload=None):
    return RuntimeEvent(event_id or f"event-{sequence}", event_type, sequence, None, None, None, None, None, None, payload or {})


def config(sequence=TraceSequencePolicy.CONTIGUOUS, empty=EmptyTracePolicy.ALLOW):
    return TraceExportConfig("trace", sequence, empty, {})


def test_exact_event_projection_retains_identity_and_extracts_nothing():
    original = event(1, payload={"legacy_data": {"amount": 10, "formula_parts": {"base": 10}}})
    record = runtime_event_to_trace_record(original)
    assert record.sequence == 1
    assert record.event is original
    assert record.action_context is record.attack_context is record.hit_context is None
    assert dict(record.numeric_values) == {}
    assert record.notes == ()
    with pytest.raises(RuntimeTraceExportSchemaError):
        runtime_event_to_trace_record(object())


def test_sequence_policies_duplicate_ids_and_empty_policies():
    contiguous = build_runtime_trace_document([event(4), event(5)], config=config())
    assert [record.sequence for record in contiguous.records] == [4, 5]
    with pytest.raises(RuntimeTraceSequenceError):
        build_runtime_trace_document([event(4), event(6)], config=config())
    increasing = build_runtime_trace_document([event(4), event(9)], config=config(TraceSequencePolicy.STRICTLY_INCREASING))
    assert increasing.last_sequence == 9
    for sequences in [(4, 4), (4, 3)]:
        with pytest.raises(RuntimeTraceSequenceError):
            build_runtime_trace_document([event(sequences[0], "first"), event(sequences[1], "second")], config=config(TraceSequencePolicy.STRICTLY_INCREASING))
    with pytest.raises(DuplicateRuntimeEventIdError):
        build_runtime_trace_document([event(1, "same"), event(2, "same")], config=config())
    empty = build_runtime_trace_document([], config=config())
    assert empty.record_count == 0 and empty.first_sequence is None and empty.last_sequence is None
    with pytest.raises(EmptyRuntimeTraceError):
        build_runtime_trace_document([], config=config(empty=EmptyTracePolicy.REJECT))


class SinglePass:
    def __init__(self, values):
        self.values = values
        self.iterations = 0

    def __iter__(self):
        self.iterations += 1
        if self.iterations > 1:
            raise AssertionError("consumed twice")
        yield from self.values


def test_stream_consumed_once_config_first_and_input_unchanged():
    source = [event(1), event(2)]
    stream = SinglePass(source)
    before = list(source)
    document = build_runtime_trace_document(stream, config=config())
    assert stream.iterations == 1 and source == before and len(document.records) == 2
    untouched = SinglePass(source)
    with pytest.raises(RuntimeTraceExportSchemaError):
        build_runtime_trace_document(untouched, config=object())
    assert untouched.iterations == 0
    with pytest.raises(RuntimeTraceExportSchemaError):
        build_runtime_trace_document([event(1), object()], config=config())


def test_semantic_gap_aggregation_and_validation():
    no_adapter = event(1, event_type=RuntimeEventType.CONTENT_DEFINED)
    no_gaps = event(2, payload={"adapter": {}})
    one = event(3, payload={"adapter": {"semantic_gap_ids": ["gap-z", "gap-a"]}})
    repeated_global = event(4, payload={"adapter": {"semantic_gap_ids": ["gap-a"]}})
    document = build_runtime_trace_document([no_adapter, no_gaps, one, repeated_global], config=config())
    assert document.semantic_gap_ids == ("gap-a", "gap-z")
    bad_payloads = [
        {"adapter": "bad"},
        {"adapter": {"semantic_gap_ids": "gap"}},
        {"adapter": {"semantic_gap_ids": [""]}},
        {"adapter": {"semantic_gap_ids": [1]}},
        {"adapter": {"semantic_gap_ids": ["gap", "gap"]}},
    ]
    for index, payload in enumerate(bad_payloads):
        with pytest.raises(RuntimeTraceExportSchemaError):
            build_runtime_trace_document([event(index, payload=payload)], config=config())


def test_reference_sample_json_and_hashes_are_exact():
    reference = json.loads((ROOT / "docs/runtime/research/REFERENCE_RUNTIME_TRACE_EXPORT_HSR_RUNTIME_ARCH_003.json").read_text())
    sample = reference["sample"]
    events = []
    for value in sample["input_runtime_events"]:
        fields = dict(value)
        fields["event_type"] = RuntimeEventType(fields["event_type"])
        events.append(RuntimeEvent(**fields))
    cfg = sample["config"]
    document = build_runtime_trace_document(events, config=TraceExportConfig(cfg["trace_id"], TraceSequencePolicy(cfg["sequence_policy"]), EmptyTracePolicy(cfg["empty_trace_policy"]), cfg["metadata"]))
    compact = build_runtime_trace_artifact(document, pretty=False)
    pretty = build_runtime_trace_artifact(document, pretty=True)
    assert compact.payload_bytes == sample["expected_compact_json"].encode()
    assert compact.sha256 == sample["expected_compact_sha256"]
    assert pretty.sha256 == sample["expected_pretty_sha256"]
    assert compact.payload_bytes != pretty.payload_bytes
    assert build_runtime_trace_artifact(document, pretty=False).payload_bytes == compact.payload_bytes
    with pytest.raises(RuntimeTraceExportSchemaError):
        build_runtime_trace_artifact(document, pretty=1)


def test_real_adapter_smoke_is_manual_and_read_only():
    actor = Unit("dps", "DPS", "ally", 100)
    target = Unit("enemy", "Enemy", "enemy", 100, hp=1000, max_hp=1000)
    state = BattleState(units=[actor, target])
    Action("hit", "Hit", "dps", ["enemy"], [DealDamage(amount=100)], False).execute(state)
    legacy_before = [(item.type, dict(item.data)) for item in state.pending_events]
    adapted = adapt_legacy_event_stream(state.pending_events, start_sequence=0, config=LegacyEventAdapterConfig("smoke", UnknownLegacyEventPolicy.REJECT, AmbiguousLegacyEventPolicy.REJECT))
    document = build_runtime_trace_document(adapted, config=TraceExportConfig("smoke", TraceSequencePolicy.CONTIGUOUS, EmptyTracePolicy.REJECT, {}))
    artifact = build_runtime_trace_artifact(document, pretty=False)
    assert [record.event.event_type for record in document.records] == [RuntimeEventType.ACTION_START, RuntimeEventType.DAMAGE_RESOLVED, RuntimeEventType.ACTION_END]
    assert [record.event.event_id for record in document.records] == [event.event_id for event in adapted]
    assert all(record.action_context is record.attack_context is record.hit_context is None for record in document.records)
    assert all(not record.numeric_values for record in document.records)
    assert [(item.type, dict(item.data)) for item in state.pending_events] == legacy_before
    assert artifact.payload_bytes
