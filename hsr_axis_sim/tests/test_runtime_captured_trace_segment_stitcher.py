from dataclasses import FrozenInstanceError

import pytest

from hsr_axis_sim.runtime_adapters import (
    AmbiguousLegacyEventPolicy,
    LegacyEventAdapterConfig,
    UnknownLegacyEventPolicy,
)
from hsr_axis_sim.runtime_capture_cursors import (
    PendingEventCaptureCursor,
    PendingEventCursorCaptureRequest,
    capture_battle_state_pending_events_from_cursor,
)
from hsr_axis_sim.runtime_exports import (
    EmptyRuntimeTraceError,
    EmptyTracePolicy,
    TraceExportConfig,
    TraceSequencePolicy,
)
from hsr_axis_sim.runtime_trace_bridges import LegacyEventTraceBridgeConfig
from hsr_axis_sim.runtime_trace_stitching import (
    CapturedTraceStitchConfig,
    RuntimeTraceStitchInputError,
    stitch_captured_trace_segments,
)
from hsr_axis_sim.sim import BattleState, Unit
from hsr_axis_sim.sim.events import Event


def _state() -> BattleState:
    return BattleState(units=[Unit("ally", "Ally", "ally", 100)])


def _populate(state: BattleState) -> None:
    state.emit_event(Event("turn_started", {"actor_id": "ally", "is_extra_turn": False}))
    state.emit_event(Event("action_started", {"actor_id": "ally", "action_id": "a"}))
    state.emit_event(Event("action_finished", {"actor_id": "ally", "action_id": "a"}))
    state.emit_event(Event("turn_ended", {"actor_id": "ally", "is_extra_turn": False}))


def _bridge_config(
    start_sequence: int,
    *,
    stream_id: str = "stitch-stream",
    trace_id: str = "segment",
    empty: EmptyTracePolicy = EmptyTracePolicy.REJECT,
) -> LegacyEventTraceBridgeConfig:
    return LegacyEventTraceBridgeConfig(
        LegacyEventAdapterConfig(
            stream_id,
            UnknownLegacyEventPolicy.REJECT,
            AmbiguousLegacyEventPolicy.REJECT,
        ),
        start_sequence,
        TraceExportConfig(
            trace_id,
            TraceSequencePolicy.CONTIGUOUS,
            empty,
            {"segment_trace_id": trace_id},
        ),
        False,
    )


def _final_config(*, empty: EmptyTracePolicy = EmptyTracePolicy.REJECT, pretty=False):
    return CapturedTraceStitchConfig(
        TraceExportConfig(
            "stitched-actual-trace",
            TraceSequencePolicy.CONTIGUOUS,
            empty,
            {"source": "captured-segment-stitch", "version": 1},
        ),
        pretty,
    )


def _two_segments(state: BattleState):
    first = capture_battle_state_pending_events_from_cursor(
        state,
        request=PendingEventCursorCaptureRequest(
            PendingEventCaptureCursor(0, 100),
            2,
            _bridge_config(100, trace_id="segment-a"),
        ),
    )
    second = capture_battle_state_pending_events_from_cursor(
        state,
        request=PendingEventCursorCaptureRequest(
            first.next_cursor,
            4,
            _bridge_config(102, trace_id="segment-b"),
        ),
    )
    return first, second


def test_two_sequential_segments_stitch_deterministically_with_exact_event_identity_order():
    state = _state()
    _populate(state)
    segments = _two_segments(state)
    config = _final_config()

    first = stitch_captured_trace_segments(segments, config=config)
    second = stitch_captured_trace_segments(segments, config=config)

    assert first == second
    assert first.artifact.payload_bytes == second.artifact.payload_bytes
    assert first.artifact.sha256 == second.artifact.sha256
    assert first.segment_count == 2
    assert first.record_count == 4
    assert first.artifact.document.trace_id == "stitched-actual-trace"
    assert first.artifact.document.metadata == {
        "source": "captured-segment-stitch",
        "version": 1,
    }
    assert [record.sequence for record in first.artifact.document.records] == [100, 101, 102, 103]
    assert [
        record.event.payload["adapter"]["legacy_event_type"]
        for record in first.artifact.document.records
    ] == ["turn_started", "action_started", "action_finished", "turn_ended"]

    source_events = tuple(
        record.event
        for segment in segments
        for record in segment.capture_result.bridge_result.artifact.document.records
    )
    final_events = tuple(record.event for record in first.artifact.document.records)
    assert all(final is source for final, source in zip(final_events, source_events))


def test_segment_local_trace_ids_metadata_and_pretty_are_not_final_trace_identity():
    state = _state()
    _populate(state)
    first, second = _two_segments(state)
    assert first.capture_result.bridge_result.artifact.document.trace_id == "segment-a"
    assert second.capture_result.bridge_result.artifact.document.trace_id == "segment-b"

    result = stitch_captured_trace_segments((first, second), config=_final_config(pretty=True))
    assert result.artifact.document.trace_id == "stitched-actual-trace"
    assert result.artifact.document.metadata["source"] == "captured-segment-stitch"
    assert result.artifact.pretty is True


def test_empty_segment_between_non_empty_segments_does_not_shift_sequence():
    state = _state()
    _populate(state)
    first = capture_battle_state_pending_events_from_cursor(
        state,
        request=PendingEventCursorCaptureRequest(
            PendingEventCaptureCursor(0, 30),
            1,
            _bridge_config(30, trace_id="first"),
        ),
    )
    empty = capture_battle_state_pending_events_from_cursor(
        state,
        request=PendingEventCursorCaptureRequest(
            first.next_cursor,
            1,
            _bridge_config(31, trace_id="empty", empty=EmptyTracePolicy.ALLOW),
        ),
    )
    last = capture_battle_state_pending_events_from_cursor(
        state,
        request=PendingEventCursorCaptureRequest(
            empty.next_cursor,
            3,
            _bridge_config(31, trace_id="last"),
        ),
    )

    result = stitch_captured_trace_segments((first, empty, last), config=_final_config())
    assert result.segment_count == 3
    assert result.record_count == 3
    assert [record.sequence for record in result.artifact.document.records] == [30, 31, 32]


def test_all_empty_segments_defer_final_empty_behavior_to_final_export_config():
    state = _state()
    cursor = PendingEventCaptureCursor(0, 8)
    first = capture_battle_state_pending_events_from_cursor(
        state,
        request=PendingEventCursorCaptureRequest(
            cursor,
            0,
            _bridge_config(8, trace_id="empty-a", empty=EmptyTracePolicy.ALLOW),
        ),
    )
    second = capture_battle_state_pending_events_from_cursor(
        state,
        request=PendingEventCursorCaptureRequest(
            first.next_cursor,
            0,
            _bridge_config(8, trace_id="empty-b", empty=EmptyTracePolicy.ALLOW),
        ),
    )

    allowed = stitch_captured_trace_segments(
        (first, second),
        config=_final_config(empty=EmptyTracePolicy.ALLOW),
    )
    assert allowed.record_count == 0
    assert allowed.artifact.document.first_sequence is None
    assert allowed.artifact.document.last_sequence is None

    with pytest.raises(EmptyRuntimeTraceError):
        stitch_captured_trace_segments(
            (first, second),
            config=_final_config(empty=EmptyTracePolicy.REJECT),
        )


def test_broken_cursor_chain_is_rejected_without_realigning_segments():
    state = _state()
    _populate(state)
    first = capture_battle_state_pending_events_from_cursor(
        state,
        request=PendingEventCursorCaptureRequest(
            PendingEventCaptureCursor(0, 10),
            1,
            _bridge_config(10, trace_id="first"),
        ),
    )
    independent = capture_battle_state_pending_events_from_cursor(
        state,
        request=PendingEventCursorCaptureRequest(
            PendingEventCaptureCursor(2, 11),
            3,
            _bridge_config(11, trace_id="independent"),
        ),
    )

    with pytest.raises(RuntimeTraceStitchInputError, match="request cursor"):
        stitch_captured_trace_segments((first, independent), config=_final_config())


def test_mixed_legacy_adapter_streams_are_rejected_even_with_cursor_continuity():
    state = _state()
    _populate(state)
    first = capture_battle_state_pending_events_from_cursor(
        state,
        request=PendingEventCursorCaptureRequest(
            PendingEventCaptureCursor(0, 10),
            1,
            _bridge_config(10, stream_id="stream-a", trace_id="first"),
        ),
    )
    second = capture_battle_state_pending_events_from_cursor(
        state,
        request=PendingEventCursorCaptureRequest(
            first.next_cursor,
            2,
            _bridge_config(11, stream_id="stream-b", trace_id="second"),
        ),
    )

    with pytest.raises(RuntimeTraceStitchInputError, match="LegacyEventAdapterConfig"):
        stitch_captured_trace_segments((first, second), config=_final_config())


def test_wrong_segment_container_empty_tuple_item_type_and_config_are_rejected():
    config = _final_config(empty=EmptyTracePolicy.ALLOW)
    with pytest.raises(RuntimeTraceStitchInputError):
        stitch_captured_trace_segments([], config=config)
    with pytest.raises(RuntimeTraceStitchInputError):
        stitch_captured_trace_segments((), config=config)
    with pytest.raises(RuntimeTraceStitchInputError):
        stitch_captured_trace_segments((object(),), config=config)
    with pytest.raises(RuntimeTraceStitchInputError):
        stitch_captured_trace_segments((object(),), config=object())


def test_stitch_config_is_frozen_and_strict():
    config = _final_config()
    with pytest.raises(FrozenInstanceError):
        config.pretty = True
    with pytest.raises(RuntimeTraceStitchInputError):
        CapturedTraceStitchConfig(object(), False)
    with pytest.raises(RuntimeTraceStitchInputError):
        CapturedTraceStitchConfig(config.export_config, 1)
