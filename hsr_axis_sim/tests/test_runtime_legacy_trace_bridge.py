from dataclasses import FrozenInstanceError

import pytest

from hsr_axis_sim.runtime_adapters import (
    AmbiguousLegacyEventError,
    AmbiguousLegacyEventPolicy,
    LegacyEventAdapterConfig,
    UnknownLegacyEventPolicy,
    UnmappedLegacyEventError,
)
from hsr_axis_sim.runtime_contracts import RuntimeEventType
from hsr_axis_sim.runtime_exports import (
    EmptyRuntimeTraceError,
    EmptyTracePolicy,
    TraceExportConfig,
    TraceSequencePolicy,
)
from hsr_axis_sim.runtime_trace_bridges import (
    LegacyEventTraceBridgeConfig,
    LegacyEventTraceBridgeResult,
    RuntimeTraceBridgeInputError,
    build_legacy_event_trace_artifact,
)
from hsr_axis_sim.sim.events import Event


def _bridge_config(
    *,
    stream_id="bridge-stream",
    start_sequence=0,
    unknown=UnknownLegacyEventPolicy.REJECT,
    ambiguous=AmbiguousLegacyEventPolicy.REJECT,
    empty=EmptyTracePolicy.REJECT,
    pretty=False,
):
    return LegacyEventTraceBridgeConfig(
        LegacyEventAdapterConfig(stream_id, unknown, ambiguous),
        start_sequence,
        TraceExportConfig(
            "legacy-runtime-trace",
            TraceSequencePolicy.CONTIGUOUS,
            empty,
            {"source": "explicit-legacy-event-stream", "version": 1},
        ),
        pretty,
    )


def _known_events():
    return [
        Event("turn_started", {"actor_id": "ally", "is_extra_turn": False}),
        Event("action_started", {"actor_id": "ally", "action_id": "skill-1"}),
        Event(
            "damage_dealt",
            {
                "source_id": "ally",
                "target_id": "enemy",
                "amount": 12.5,
                "formula_parts": {"base": 12.5},
            },
        ),
        Event("action_finished", {"actor_id": "ally", "action_id": "skill-1"}),
        Event("turn_ended", {"actor_id": "ally", "is_extra_turn": False}),
    ]


def test_known_legacy_stream_builds_deterministic_runtime_trace_artifact():
    config = _bridge_config(start_sequence=7)

    first = build_legacy_event_trace_artifact(_known_events(), config=config)
    second = build_legacy_event_trace_artifact(_known_events(), config=config)

    assert first == second
    assert first.artifact.payload_bytes == second.artifact.payload_bytes
    assert first.artifact.sha256 == second.artifact.sha256
    assert first.record_count == 5
    document = first.artifact.document
    assert document.trace_id == "legacy-runtime-trace"
    assert document.first_sequence == 7
    assert document.last_sequence == 11
    assert document.metadata == {
        "source": "explicit-legacy-event-stream",
        "version": 1,
    }
    assert [record.sequence for record in document.records] == [7, 8, 9, 10, 11]
    assert [record.event.event_id for record in document.records] == [
        f"legacy:bridge-stream:{sequence}" for sequence in range(7, 12)
    ]
    assert [record.event.event_type for record in document.records] == [
        RuntimeEventType.TURN_START,
        RuntimeEventType.ACTION_START,
        RuntimeEventType.DAMAGE_RESOLVED,
        RuntimeEventType.ACTION_END,
        RuntimeEventType.TURN_END,
    ]
    assert document.semantic_gap_ids == ()


def test_unknown_event_preserve_policy_flows_into_trace_semantic_gaps():
    config = _bridge_config(
        unknown=UnknownLegacyEventPolicy.PRESERVE_AS_CONTENT_DEFINED
    )
    result = build_legacy_event_trace_artifact(
        [Event("future_event", {"value": 1})],
        config=config,
    )
    record = result.artifact.document.records[0]
    assert record.event.event_type is RuntimeEventType.CONTENT_DEFINED
    assert record.event.payload["adapter"]["mapping_status"] == "UNMAPPED_PRESERVED"
    assert result.artifact.document.semantic_gap_ids == (
        "LEGACY_EVENT.UNMAPPED_TYPE",
    )


def test_unknown_event_reject_policy_is_not_weakened_by_bridge():
    with pytest.raises(UnmappedLegacyEventError):
        build_legacy_event_trace_artifact(
            [Event("future_event", {"value": 1})],
            config=_bridge_config(),
        )


def test_ambiguous_unit_defeated_preserve_and_reject_policies_are_unchanged():
    event = Event("unit_defeated", {"killer_id": "ally", "target_id": "enemy"})
    with pytest.raises(AmbiguousLegacyEventError):
        build_legacy_event_trace_artifact([event], config=_bridge_config())

    result = build_legacy_event_trace_artifact(
        [event],
        config=_bridge_config(
            ambiguous=AmbiguousLegacyEventPolicy.PRESERVE_AS_CONTENT_DEFINED
        ),
    )
    record = result.artifact.document.records[0]
    assert record.event.event_type is RuntimeEventType.CONTENT_DEFINED
    assert record.event.source_id is None
    assert record.event.target_id == "enemy"
    assert result.artifact.document.semantic_gap_ids == (
        "LEGACY_EVENT.UNIT_DEFEATED_LIFECYCLE",
    )


def test_empty_stream_follows_existing_export_empty_policy():
    allowed = build_legacy_event_trace_artifact(
        [],
        config=_bridge_config(empty=EmptyTracePolicy.ALLOW, start_sequence=13),
    )
    assert allowed.record_count == 0
    assert allowed.artifact.document.first_sequence is None
    assert allowed.artifact.document.last_sequence is None

    with pytest.raises(EmptyRuntimeTraceError):
        build_legacy_event_trace_artifact(
            [],
            config=_bridge_config(empty=EmptyTracePolicy.REJECT),
        )


def test_caller_event_iterable_is_consumed_exactly_once():
    class SinglePassEvents:
        def __init__(self):
            self.iter_calls = 0

        def __iter__(self):
            self.iter_calls += 1
            if self.iter_calls > 1:
                raise AssertionError("legacy event source was iterated more than once")
            yield from _known_events()

    source = SinglePassEvents()
    result = build_legacy_event_trace_artifact(source, config=_bridge_config())
    assert source.iter_calls == 1
    assert result.record_count == 5


def test_pretty_flag_is_explicit_and_changes_only_artifact_encoding():
    compact = build_legacy_event_trace_artifact(
        _known_events(), config=_bridge_config(pretty=False)
    )
    pretty = build_legacy_event_trace_artifact(
        _known_events(), config=_bridge_config(pretty=True)
    )
    assert compact.artifact.document == pretty.artifact.document
    assert compact.artifact.pretty is False
    assert pretty.artifact.pretty is True
    assert compact.artifact.payload_bytes != pretty.artifact.payload_bytes
    assert compact.artifact.sha256 != pretty.artifact.sha256


def test_bridge_config_and_result_are_frozen_and_input_contract_is_strict():
    config = _bridge_config()
    result = build_legacy_event_trace_artifact(_known_events(), config=config)
    with pytest.raises(FrozenInstanceError):
        config.pretty = True
    with pytest.raises(FrozenInstanceError):
        result.artifact = object()

    with pytest.raises(RuntimeTraceBridgeInputError):
        LegacyEventTraceBridgeConfig(object(), 0, config.export_config, False)
    with pytest.raises(RuntimeTraceBridgeInputError):
        LegacyEventTraceBridgeConfig(config.adapter_config, -1, config.export_config, False)
    with pytest.raises(RuntimeTraceBridgeInputError):
        LegacyEventTraceBridgeConfig(config.adapter_config, True, config.export_config, False)
    with pytest.raises(RuntimeTraceBridgeInputError):
        LegacyEventTraceBridgeConfig(config.adapter_config, 0, object(), False)
    with pytest.raises(RuntimeTraceBridgeInputError):
        LegacyEventTraceBridgeConfig(config.adapter_config, 0, config.export_config, 1)
    with pytest.raises(RuntimeTraceBridgeInputError):
        build_legacy_event_trace_artifact(_known_events(), config=object())


def test_result_rejects_artifact_provenance_that_does_not_match_bridge_config():
    config_a = _bridge_config(stream_id="a")
    config_b = LegacyEventTraceBridgeConfig(
        config_a.adapter_config,
        config_a.start_sequence,
        TraceExportConfig(
            "different-trace-id",
            config_a.export_config.sequence_policy,
            config_a.export_config.empty_trace_policy,
            config_a.export_config.metadata,
        ),
        config_a.pretty,
    )
    result = build_legacy_event_trace_artifact(_known_events(), config=config_a)
    with pytest.raises(RuntimeTraceBridgeInputError, match="trace_id"):
        LegacyEventTraceBridgeResult(config_b, result.artifact)
