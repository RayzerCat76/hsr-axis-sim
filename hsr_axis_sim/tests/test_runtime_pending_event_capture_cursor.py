from dataclasses import FrozenInstanceError

import pytest

from hsr_axis_sim.runtime_adapters import (
    AmbiguousLegacyEventPolicy,
    LegacyEventAdapterConfig,
    UnknownLegacyEventPolicy,
    UnmappedLegacyEventError,
)
from hsr_axis_sim.runtime_capture_cursors import (
    PendingEventCaptureCursor,
    PendingEventCursorCaptureRequest,
    PendingEventCursorCaptureResult,
    RuntimeCaptureCursorInputError,
    StalePendingEventCaptureCursorError,
    capture_battle_state_pending_events_from_cursor,
)
from hsr_axis_sim.runtime_exports import (
    EmptyTracePolicy,
    TraceExportConfig,
    TraceSequencePolicy,
)
from hsr_axis_sim.runtime_state_captures import RuntimeStateCaptureInputError
from hsr_axis_sim.runtime_trace_bridges import LegacyEventTraceBridgeConfig
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
    trace_id: str = "cursor-slice",
    empty: EmptyTracePolicy = EmptyTracePolicy.REJECT,
    unknown: UnknownLegacyEventPolicy = UnknownLegacyEventPolicy.REJECT,
) -> LegacyEventTraceBridgeConfig:
    return LegacyEventTraceBridgeConfig(
        LegacyEventAdapterConfig(
            "cursor-stream",
            unknown,
            AmbiguousLegacyEventPolicy.REJECT,
        ),
        start_sequence,
        TraceExportConfig(
            trace_id,
            TraceSequencePolicy.CONTIGUOUS,
            empty,
            {"capture": "explicit-cursor"},
        ),
        False,
    )


def test_two_sequential_captures_preserve_index_and_runtime_sequence_continuity():
    state = _state()
    _populate(state)
    before = list(state.pending_events)

    first_request = PendingEventCursorCaptureRequest(
        PendingEventCaptureCursor(0, 100),
        2,
        _bridge_config(100, trace_id="slice-1"),
    )
    first = capture_battle_state_pending_events_from_cursor(
        state,
        request=first_request,
    )
    assert first.next_cursor == PendingEventCaptureCursor(2, 102)
    assert [
        record.sequence
        for record in first.capture_result.bridge_result.artifact.document.records
    ] == [100, 101]
    assert [
        record.event.payload["adapter"]["legacy_event_type"]
        for record in first.capture_result.bridge_result.artifact.document.records
    ] == ["turn_started", "action_started"]

    second_request = PendingEventCursorCaptureRequest(
        first.next_cursor,
        4,
        _bridge_config(102, trace_id="slice-2"),
    )
    second = capture_battle_state_pending_events_from_cursor(
        state,
        request=second_request,
    )
    assert second.next_cursor == PendingEventCaptureCursor(4, 104)
    assert [
        record.sequence
        for record in second.capture_result.bridge_result.artifact.document.records
    ] == [102, 103]
    assert [
        record.event.payload["adapter"]["legacy_event_type"]
        for record in second.capture_result.bridge_result.artifact.document.records
    ] == ["action_finished", "turn_ended"]
    assert state.pending_events == before
    assert all(current is original for current, original in zip(state.pending_events, before))


def test_empty_capture_preserves_cursor_coordinates_when_end_equals_current_index():
    state = _state()
    _populate(state)
    cursor = PendingEventCaptureCursor(2, 50)
    request = PendingEventCursorCaptureRequest(
        cursor,
        2,
        _bridge_config(50, empty=EmptyTracePolicy.ALLOW),
    )
    result = capture_battle_state_pending_events_from_cursor(state, request=request)
    assert result.captured_event_count == 0
    assert result.next_cursor == cursor
    assert len(state.pending_events) == 4


def test_stale_cursor_beyond_current_list_length_is_rejected_before_capture():
    state = _state()
    state.emit_event(Event("turn_started", {"actor_id": "ally", "is_extra_turn": False}))
    request = PendingEventCursorCaptureRequest(
        PendingEventCaptureCursor(2, 10),
        2,
        _bridge_config(10, empty=EmptyTracePolicy.ALLOW),
    )
    with pytest.raises(StalePendingEventCaptureCursorError):
        capture_battle_state_pending_events_from_cursor(state, request=request)
    assert len(state.pending_events) == 1


def test_end_index_beyond_current_list_is_still_rejected_by_arch_008():
    state = _state()
    state.emit_event(Event("turn_started", {"actor_id": "ally", "is_extra_turn": False}))
    request = PendingEventCursorCaptureRequest(
        PendingEventCaptureCursor(0, 10),
        2,
        _bridge_config(10),
    )
    with pytest.raises(RuntimeStateCaptureInputError, match="len\\(state.pending_events\\)"):
        capture_battle_state_pending_events_from_cursor(state, request=request)
    assert len(state.pending_events) == 1


def test_bridge_start_sequence_must_match_cursor_before_capture():
    with pytest.raises(RuntimeCaptureCursorInputError, match="start_sequence"):
        PendingEventCursorCaptureRequest(
            PendingEventCaptureCursor(0, 10),
            1,
            _bridge_config(11),
        )


def test_delegated_adapter_failure_leaves_state_and_original_cursor_unchanged():
    state = _state()
    state.emit_event(Event("future_event", {"value": 1}))
    before = list(state.pending_events)
    cursor = PendingEventCaptureCursor(0, 7)
    request = PendingEventCursorCaptureRequest(cursor, 1, _bridge_config(7))

    with pytest.raises(UnmappedLegacyEventError):
        capture_battle_state_pending_events_from_cursor(state, request=request)

    assert cursor == PendingEventCaptureCursor(0, 7)
    assert state.pending_events == before
    assert state.pending_events[0] is before[0]


def test_unknown_preserve_policy_remains_delegated_through_arch_008_and_arch_007():
    state = _state()
    state.emit_event(Event("future_event", {"value": 1}))
    request = PendingEventCursorCaptureRequest(
        PendingEventCaptureCursor(0, 3),
        1,
        _bridge_config(
            3,
            unknown=UnknownLegacyEventPolicy.PRESERVE_AS_CONTENT_DEFINED,
        ),
    )
    result = capture_battle_state_pending_events_from_cursor(state, request=request)
    assert result.capture_result.bridge_result.artifact.document.semantic_gap_ids == (
        "LEGACY_EVENT.UNMAPPED_TYPE",
    )
    assert result.next_cursor == PendingEventCaptureCursor(1, 4)


@pytest.mark.parametrize(
    ("pending_index", "next_sequence"),
    [(-1, 0), (0, -1), (True, 0), (0, True)],
)
def test_cursor_rejects_invalid_coordinates(pending_index, next_sequence):
    with pytest.raises(RuntimeCaptureCursorInputError):
        PendingEventCaptureCursor(pending_index, next_sequence)


def test_request_rejects_invalid_types_and_reverse_range():
    cursor = PendingEventCaptureCursor(2, 20)
    bridge = _bridge_config(20)
    with pytest.raises(RuntimeCaptureCursorInputError):
        PendingEventCursorCaptureRequest(object(), 2, bridge)
    with pytest.raises(RuntimeCaptureCursorInputError):
        PendingEventCursorCaptureRequest(cursor, True, bridge)
    with pytest.raises(RuntimeCaptureCursorInputError):
        PendingEventCursorCaptureRequest(cursor, 1, bridge)
    with pytest.raises(RuntimeCaptureCursorInputError):
        PendingEventCursorCaptureRequest(cursor, 2, object())


def test_runner_rejects_wrong_state_request_and_pending_event_container_shape():
    request = PendingEventCursorCaptureRequest(
        PendingEventCaptureCursor(0, 0),
        0,
        _bridge_config(0, empty=EmptyTracePolicy.ALLOW),
    )
    with pytest.raises(RuntimeCaptureCursorInputError):
        capture_battle_state_pending_events_from_cursor(object(), request=request)
    state = _state()
    with pytest.raises(RuntimeCaptureCursorInputError):
        capture_battle_state_pending_events_from_cursor(state, request=object())
    state.pending_events = ()
    with pytest.raises(RuntimeCaptureCursorInputError, match="must be a list"):
        capture_battle_state_pending_events_from_cursor(state, request=request)


def test_cursor_request_and_result_are_frozen_and_result_alignment_is_strict():
    state = _state()
    _populate(state)
    cursor = PendingEventCaptureCursor(0, 5)
    request = PendingEventCursorCaptureRequest(cursor, 2, _bridge_config(5))
    result = capture_battle_state_pending_events_from_cursor(state, request=request)

    with pytest.raises(FrozenInstanceError):
        cursor.pending_event_index = 1
    with pytest.raises(FrozenInstanceError):
        request.end_index = 3
    with pytest.raises(FrozenInstanceError):
        result.next_cursor = PendingEventCaptureCursor(2, 99)

    with pytest.raises(RuntimeCaptureCursorInputError, match="next_cursor"):
        PendingEventCursorCaptureResult(
            request,
            result.capture_result,
            PendingEventCaptureCursor(2, 99),
        )
