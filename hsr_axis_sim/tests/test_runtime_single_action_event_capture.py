from dataclasses import FrozenInstanceError
import importlib

import pytest

from hsr_axis_sim.runtime_adapters import (
    AmbiguousLegacyEventPolicy,
    LegacyEventAdapterConfig,
    UnknownLegacyEventPolicy,
    UnmappedLegacyEventError,
)
from hsr_axis_sim.runtime_action_captures import (
    ActionCaptureCursorAlignmentError,
    RuntimeActionCaptureInputError,
    SingleActionEventCaptureRequest,
    SingleActionEventCaptureResult,
    execute_action_and_capture_pending_events,
)
from hsr_axis_sim.runtime_capture_cursors import PendingEventCaptureCursor
from hsr_axis_sim.runtime_contracts import RuntimeEventType
from hsr_axis_sim.runtime_exports import (
    EmptyTracePolicy,
    TraceExportConfig,
    TraceSequencePolicy,
)
from hsr_axis_sim.runtime_trace_bridges import LegacyEventTraceBridgeConfig
from hsr_axis_sim.sim.action import Action
from hsr_axis_sim.sim.effects import Effect
from hsr_axis_sim.sim.events import Event
from hsr_axis_sim.sim.state import BattleState
from hsr_axis_sim.sim.turn_context import TurnContext


def _bridge_config(*, start_sequence=0, unknown=UnknownLegacyEventPolicy.REJECT):
    return LegacyEventTraceBridgeConfig(
        LegacyEventAdapterConfig(
            "single-action-stream",
            unknown,
            AmbiguousLegacyEventPolicy.REJECT,
        ),
        start_sequence,
        TraceExportConfig(
            "single-action-trace",
            TraceSequencePolicy.CONTIGUOUS,
            EmptyTracePolicy.REJECT,
            {"source": "explicit-single-action-window"},
        ),
        False,
    )


def _request(*, index=0, sequence=0, unknown=UnknownLegacyEventPolicy.REJECT):
    return SingleActionEventCaptureRequest(
        PendingEventCaptureCursor(index, sequence),
        _bridge_config(start_sequence=sequence, unknown=unknown),
    )


def test_successful_action_captures_exact_new_pending_event_window():
    old_event = Event("turn_started", {"actor_id": "old"})
    state = BattleState([], pending_events=[old_event])
    action = Action("skill-1", "Skill 1", "actor", ends_turn=False)
    request = _request(index=1, sequence=10)

    result = execute_action_and_capture_pending_events(
        state,
        action,
        request=request,
    )

    assert state.pending_events[0] is old_event
    assert len(state.pending_events) == 3
    assert result.pending_event_count_before == 1
    assert result.pending_event_count_after == 3
    assert result.captured_event_count == 2
    assert result.action_id == "skill-1"
    assert result.actor_id == "actor"
    assert result.next_cursor == PendingEventCaptureCursor(3, 12)

    records = result.capture_result.capture_result.bridge_result.artifact.document.records
    assert [record.sequence for record in records] == [10, 11]
    assert [record.event.event_id for record in records] == [
        "legacy:single-action-stream:10",
        "legacy:single-action-stream:11",
    ]
    assert [record.event.event_type for record in records] == [
        RuntimeEventType.ACTION_START,
        RuntimeEventType.ACTION_END,
    ]
    assert [record.event.action_id for record in records] == ["skill-1", "skill-1"]


def test_preexisting_events_are_untouched_and_excluded_from_capture():
    old_a = Event("turn_started", {"actor_id": "a"})
    old_b = Event("turn_ended", {"actor_id": "a"})
    state = BattleState([], pending_events=[old_a, old_b])
    before = tuple(state.pending_events)

    result = execute_action_and_capture_pending_events(
        state,
        Action("action", "Action", "actor", ends_turn=False),
        request=_request(index=2, sequence=4),
    )

    assert tuple(state.pending_events[:2]) == before
    assert result.capture_result.request.cursor.pending_event_index == 2
    assert result.capture_result.request.end_index == 4
    assert result.captured_event_count == 2


def test_cursor_must_equal_current_event_list_end_before_action_runs():
    existing = Event("turn_started", {"actor_id": "old"})
    state = BattleState([], pending_events=[existing])
    action = Action("action", "Action", "actor", ends_turn=False)

    with pytest.raises(ActionCaptureCursorAlignmentError):
        execute_action_and_capture_pending_events(
            state,
            action,
            request=_request(index=0, sequence=0),
        )

    assert state.pending_events == [existing]


def test_caller_turn_context_is_passed_and_returned_by_identity():
    state = BattleState([])
    context = TurnContext(actor_id="actor")
    result = execute_action_and_capture_pending_events(
        state,
        Action("action", "Action", "actor", ends_turn=False),
        request=_request(),
        turn_context=context,
    )
    assert result.turn_context is context
    assert context.actions_taken == ["action"]


class RaiseDuringAction(Effect):
    def apply(self, state, action, turn_context):
        state.logs.append("partial-mutation")
        raise ValueError("intentional action failure")


class EmitUnknownEvent(Effect):
    def apply(self, state, action, turn_context):
        state.emit_event(Event("future_event", {"value": 1}), turn_context)


def test_action_failure_propagates_preserves_partial_mutation_and_skips_capture(monkeypatch):
    state = BattleState([])
    action = Action(
        "failing-action",
        "Failing Action",
        "actor",
        effects=[RaiseDuringAction()],
        ends_turn=False,
    )
    module = importlib.import_module("hsr_axis_sim.runtime_action_captures.capture")
    calls = []

    def forbidden_capture(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("capture must not run after Action.execute fails")

    monkeypatch.setattr(module, "capture_battle_state_pending_events_from_cursor", forbidden_capture)

    with pytest.raises(ValueError, match="intentional action failure"):
        module.execute_action_and_capture_pending_events(
            state,
            action,
            request=_request(),
        )

    assert calls == []
    assert state.logs == ["partial-mutation"]
    assert [event.type for event in state.pending_events] == ["action_started"]


def test_post_action_capture_failure_propagates_without_rollback():
    state = BattleState([])
    action = Action(
        "successful-action",
        "Successful Action",
        "actor",
        effects=[EmitUnknownEvent()],
        ends_turn=False,
    )

    with pytest.raises(UnmappedLegacyEventError):
        execute_action_and_capture_pending_events(
            state,
            action,
            request=_request(unknown=UnknownLegacyEventPolicy.REJECT),
        )

    assert [event.type for event in state.pending_events] == [
        "action_started",
        "future_event",
        "action_finished",
    ]


def test_request_and_result_are_strict_and_result_shell_is_frozen():
    request = _request()
    state = BattleState([])
    result = execute_action_and_capture_pending_events(
        state,
        Action("action", "Action", "actor", ends_turn=False),
        request=request,
    )

    with pytest.raises(FrozenInstanceError):
        request.cursor = PendingEventCaptureCursor(1, 1)
    with pytest.raises(FrozenInstanceError):
        result.action_id = "other"

    with pytest.raises(RuntimeActionCaptureInputError):
        SingleActionEventCaptureRequest(object(), request.bridge_config)
    with pytest.raises(RuntimeActionCaptureInputError):
        SingleActionEventCaptureRequest(request.cursor, object())
    with pytest.raises(RuntimeActionCaptureInputError, match="start_sequence"):
        SingleActionEventCaptureRequest(
            PendingEventCaptureCursor(0, 5),
            _bridge_config(start_sequence=4),
        )
    with pytest.raises(RuntimeActionCaptureInputError):
        execute_action_and_capture_pending_events(
            object(),
            Action("action", "Action", "actor", ends_turn=False),
            request=request,
        )
    with pytest.raises(RuntimeActionCaptureInputError):
        execute_action_and_capture_pending_events(
            BattleState([]),
            object(),
            request=request,
        )
    with pytest.raises(RuntimeActionCaptureInputError):
        execute_action_and_capture_pending_events(
            BattleState([]),
            Action("action", "Action", "actor", ends_turn=False),
            request=object(),
        )
    with pytest.raises(RuntimeActionCaptureInputError):
        execute_action_and_capture_pending_events(
            BattleState([]),
            Action("action", "Action", "actor", ends_turn=False),
            request=request,
            turn_context=object(),
        )

    with pytest.raises(RuntimeActionCaptureInputError, match="pre-action"):
        SingleActionEventCaptureResult(
            request,
            result.action_id,
            result.actor_id,
            1,
            result.pending_event_count_after,
            result.turn_context,
            result.capture_result,
        )
