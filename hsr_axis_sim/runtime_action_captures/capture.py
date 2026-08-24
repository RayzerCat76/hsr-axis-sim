"""Explicit non-transactional orchestration of one production Action capture."""

from __future__ import annotations

from hsr_axis_sim.runtime_capture_cursors import (
    PendingEventCursorCaptureRequest,
    capture_battle_state_pending_events_from_cursor,
)
from hsr_axis_sim.sim.action import Action
from hsr_axis_sim.sim.state import BattleState
from hsr_axis_sim.sim.turn_context import TurnContext

from .model import (
    ActionCaptureCursorAlignmentError,
    RuntimeActionCaptureInputError,
    SingleActionEventCaptureRequest,
    SingleActionEventCaptureResult,
)


def execute_action_and_capture_pending_events(
    state: BattleState,
    action: Action,
    *,
    request: SingleActionEventCaptureRequest,
    turn_context: TurnContext | None = None,
) -> SingleActionEventCaptureResult:
    """Execute exactly one Action and capture exactly its newly appended event window.

    This function is intentionally non-transactional. Any exception from production
    action execution or downstream capture propagates with simulator mutations left
    exactly as they occurred.
    """

    if not isinstance(state, BattleState):
        raise RuntimeActionCaptureInputError("state must be BattleState")
    if not isinstance(action, Action):
        raise RuntimeActionCaptureInputError("action must be Action")
    if not isinstance(request, SingleActionEventCaptureRequest):
        raise RuntimeActionCaptureInputError(
            "request must be SingleActionEventCaptureRequest"
        )
    if turn_context is not None and not isinstance(turn_context, TurnContext):
        raise RuntimeActionCaptureInputError("turn_context must be TurnContext or None")
    if not isinstance(state.pending_events, list):
        raise RuntimeActionCaptureInputError(
            "BattleState.pending_events must be a list before action execution"
        )

    before_count = len(state.pending_events)
    if request.cursor.pending_event_index != before_count:
        raise ActionCaptureCursorAlignmentError(
            "cursor.pending_event_index must equal current len(state.pending_events) "
            "before action execution"
        )

    returned_context = action.execute(state, turn_context)

    if not isinstance(state.pending_events, list):
        raise RuntimeActionCaptureInputError(
            "BattleState.pending_events must remain a list after action execution"
        )
    after_count = len(state.pending_events)
    if after_count < before_count:
        raise RuntimeActionCaptureInputError(
            "pending-event list shrank during action execution; exact append window "
            "cannot be represented"
        )

    capture_result = capture_battle_state_pending_events_from_cursor(
        state,
        request=PendingEventCursorCaptureRequest(
            request.cursor,
            after_count,
            request.bridge_config,
        ),
    )
    return SingleActionEventCaptureResult(
        request=request,
        action_id=action.id,
        actor_id=action.actor_id,
        pending_event_count_before=before_count,
        pending_event_count_after=after_count,
        turn_context=returned_context,
        capture_result=capture_result,
    )
