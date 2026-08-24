"""Caller-owned cursor orchestration over accepted ARCH-008 state capture."""

from __future__ import annotations

from hsr_axis_sim.runtime_state_captures import (
    BattleStatePendingEventSliceCaptureConfig,
    capture_battle_state_pending_event_slice,
)
from hsr_axis_sim.sim.state import BattleState

from .model import (
    PendingEventCaptureCursor,
    PendingEventCursorCaptureRequest,
    PendingEventCursorCaptureResult,
    RuntimeCaptureCursorInputError,
    StalePendingEventCaptureCursorError,
)


def capture_battle_state_pending_events_from_cursor(
    state: BattleState,
    *,
    request: PendingEventCursorCaptureRequest,
) -> PendingEventCursorCaptureResult:
    """Capture one caller-selected slice and return the next immutable cursor."""

    if not isinstance(state, BattleState):
        raise RuntimeCaptureCursorInputError("state must be BattleState")
    if not isinstance(request, PendingEventCursorCaptureRequest):
        raise RuntimeCaptureCursorInputError(
            "request must be PendingEventCursorCaptureRequest"
        )
    if not isinstance(state.pending_events, list):
        raise RuntimeCaptureCursorInputError(
            "BattleState.pending_events must be a list at capture time"
        )

    current_count = len(state.pending_events)
    if request.cursor.pending_event_index > current_count:
        raise StalePendingEventCaptureCursorError(
            "cursor.pending_event_index exceeds current len(state.pending_events)"
        )

    capture_result = capture_battle_state_pending_event_slice(
        state,
        config=BattleStatePendingEventSliceCaptureConfig(
            request.bridge_config,
            request.cursor.pending_event_index,
            request.end_index,
        ),
    )
    next_cursor = PendingEventCaptureCursor(
        request.end_index,
        request.cursor.next_runtime_sequence + capture_result.captured_event_count,
    )
    return PendingEventCursorCaptureResult(
        request=request,
        capture_result=capture_result,
        next_cursor=next_cursor,
    )
