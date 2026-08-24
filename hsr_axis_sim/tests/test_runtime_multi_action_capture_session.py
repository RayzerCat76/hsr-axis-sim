from dataclasses import FrozenInstanceError

import pytest

from hsr_axis_sim.runtime_action_sessions import (
    ExplicitActionCaptureStep,
    MultiActionCaptureSessionConfig,
    MultiActionCaptureSessionFailure,
    MultiActionCaptureSessionResult,
    RuntimeActionSessionInputError,
    run_multi_action_capture_session,
)
from hsr_axis_sim.runtime_adapters import (
    AmbiguousLegacyEventPolicy,
    LegacyEventAdapterConfig,
    UnknownLegacyEventPolicy,
    UnmappedLegacyEventError,
)
from hsr_axis_sim.runtime_capture_cursors import PendingEventCaptureCursor
from hsr_axis_sim.runtime_exports import (
    EmptyTracePolicy,
    TraceExportConfig,
    TraceSequencePolicy,
)
from hsr_axis_sim.sim.action import Action
from hsr_axis_sim.sim.effects import Effect
from hsr_axis_sim.sim.events import Event
from hsr_axis_sim.sim.state import BattleState
from hsr_axis_sim.sim.turn_context import TurnContext


def _adapter_config(*, unknown=UnknownLegacyEventPolicy.REJECT):
    return LegacyEventAdapterConfig(
        "multi-action-stream",
        unknown,
        AmbiguousLegacyEventPolicy.REJECT,
    )


def _export_config(index):
    return TraceExportConfig(
        f"segment-{index}",
        TraceSequencePolicy.CONTIGUOUS,
        EmptyTracePolicy.REJECT,
        {"segment_index": index, "source": "explicit-multi-action-session"},
    )


def _session_config(count, *, initial_cursor=None, unknown=UnknownLegacyEventPolicy.REJECT):
    return MultiActionCaptureSessionConfig(
        initial_cursor or PendingEventCaptureCursor(0, 0),
        _adapter_config(unknown=unknown),
        tuple(_export_config(index) for index in range(count)),
        False,
    )


def _simple_step(action_id, *, actor="actor", context=None):
    return ExplicitActionCaptureStep(
        Action(action_id, action_id, actor, ends_turn=False),
        context,
    )


def _document(result):
    return result.capture_result.capture_result.bridge_result.artifact.document


def test_successful_session_preserves_order_configs_and_cursor_chain():
    state = BattleState([])
    steps = (
        _simple_step("action-a"),
        _simple_step("action-b"),
        _simple_step("action-c"),
    )
    config = _session_config(3)

    result = run_multi_action_capture_session(state, steps, config=config)

    assert result.steps is steps
    assert [item.action_id for item in result.results] == [
        "action-a",
        "action-b",
        "action-c",
    ]
    assert [item.request.cursor for item in result.results] == [
        PendingEventCaptureCursor(0, 0),
        PendingEventCaptureCursor(2, 2),
        PendingEventCaptureCursor(4, 4),
    ]
    assert [item.next_cursor for item in result.results] == [
        PendingEventCaptureCursor(2, 2),
        PendingEventCaptureCursor(4, 4),
        PendingEventCaptureCursor(6, 6),
    ]
    assert result.final_cursor == PendingEventCaptureCursor(6, 6)
    assert result.action_count == 3
    assert len(state.pending_events) == 6

    documents = [_document(item) for item in result.results]
    assert [document.trace_id for document in documents] == [
        "segment-0",
        "segment-1",
        "segment-2",
    ]
    assert [document.metadata["segment_index"] for document in documents] == [0, 1, 2]
    assert [[record.sequence for record in document.records] for document in documents] == [
        [0, 1],
        [2, 3],
        [4, 5],
    ]


def test_same_caller_turn_context_can_be_reused_across_nonending_actions():
    state = BattleState([])
    context = TurnContext(actor_id="actor")
    steps = (
        _simple_step("action-a", context=context),
        _simple_step("action-b", context=context),
    )

    result = run_multi_action_capture_session(state, steps, config=_session_config(2))

    assert result.results[0].turn_context is context
    assert result.results[1].turn_context is context
    assert context.actions_taken == ["action-a", "action-b"]


class RaiseDuringAction(Effect):
    def apply(self, state, action, turn_context):
        state.logs.append(f"partial:{action.id}")
        raise ValueError("intentional session action failure")


class EmitUnknownEvent(Effect):
    def apply(self, state, action, turn_context):
        state.emit_event(Event("future_event", {"action": action.id}), turn_context)


def test_second_action_failure_stops_session_and_preserves_completed_provenance():
    state = BattleState([])
    third = Action("action-c", "action-c", "actor", ends_turn=False)
    steps = (
        _simple_step("action-a"),
        ExplicitActionCaptureStep(
            Action(
                "action-b",
                "action-b",
                "actor",
                effects=[RaiseDuringAction()],
                ends_turn=False,
            )
        ),
        ExplicitActionCaptureStep(third),
    )

    with pytest.raises(MultiActionCaptureSessionFailure) as caught:
        run_multi_action_capture_session(state, steps, config=_session_config(3))

    failure = caught.value
    assert failure.failed_action_index == 1
    assert failure.failed_action_id == "action-b"
    assert len(failure.completed_results) == 1
    assert failure.completed_results[0].action_id == "action-a"
    assert failure.last_successful_cursor == PendingEventCaptureCursor(2, 2)
    assert isinstance(failure.__cause__, ValueError)
    assert str(failure.__cause__) == "intentional session action failure"

    # The failed action emitted action_started and mutated logs before raising.
    # The retained cursor is only the last confirmed completed boundary and is
    # therefore behind the current pending-event list after partial failure.
    assert [event.data.get("action_id") for event in state.pending_events] == [
        "action-a",
        "action-a",
        "action-b",
    ]
    assert state.logs == ["partial:action-b"]
    assert len(state.pending_events) == 3
    assert failure.last_successful_cursor.pending_event_index == 2
    assert all(event.data.get("action_id") != "action-c" for event in state.pending_events)


def test_post_action_capture_failure_stops_and_preserves_successful_action_mutation():
    state = BattleState([])
    steps = (
        _simple_step("action-a"),
        ExplicitActionCaptureStep(
            Action(
                "action-b",
                "action-b",
                "actor",
                effects=[EmitUnknownEvent()],
                ends_turn=False,
            )
        ),
        _simple_step("action-c"),
    )

    with pytest.raises(MultiActionCaptureSessionFailure) as caught:
        run_multi_action_capture_session(state, steps, config=_session_config(3))

    failure = caught.value
    assert failure.failed_action_index == 1
    assert failure.failed_action_id == "action-b"
    assert len(failure.completed_results) == 1
    assert failure.last_successful_cursor == PendingEventCaptureCursor(2, 2)
    assert isinstance(failure.__cause__, UnmappedLegacyEventError)
    assert [event.type for event in state.pending_events] == [
        "action_started",
        "action_finished",
        "action_started",
        "future_event",
        "action_finished",
    ]
    assert all(event.data.get("action_id") != "action-c" for event in state.pending_events)


def test_empty_steps_and_export_config_count_mismatch_fail_before_execution():
    state = BattleState([])
    with pytest.raises(RuntimeActionSessionInputError, match="non-empty"):
        run_multi_action_capture_session(state, (), config=_session_config(0))
    assert state.pending_events == []

    steps = (_simple_step("action-a"), _simple_step("action-b"))
    with pytest.raises(RuntimeActionSessionInputError, match="length"):
        run_multi_action_capture_session(state, steps, config=_session_config(1))
    assert state.pending_events == []


def test_step_config_and_result_shells_are_strict_and_frozen():
    step = _simple_step("action-a")
    config = _session_config(1)
    result = run_multi_action_capture_session(BattleState([]), (step,), config=config)

    with pytest.raises(FrozenInstanceError):
        step.action = Action("other", "other", "actor", ends_turn=False)
    with pytest.raises(FrozenInstanceError):
        config.pretty = True
    with pytest.raises(FrozenInstanceError):
        result.final_cursor = PendingEventCaptureCursor(0, 0)

    with pytest.raises(RuntimeActionSessionInputError):
        ExplicitActionCaptureStep(object())
    with pytest.raises(RuntimeActionSessionInputError):
        ExplicitActionCaptureStep(step.action, object())
    with pytest.raises(RuntimeActionSessionInputError):
        MultiActionCaptureSessionConfig(
            object(), config.adapter_config, config.segment_export_configs, False
        )
    with pytest.raises(RuntimeActionSessionInputError):
        MultiActionCaptureSessionConfig(
            config.initial_cursor, object(), config.segment_export_configs, False
        )
    with pytest.raises(RuntimeActionSessionInputError):
        MultiActionCaptureSessionConfig(
            config.initial_cursor, config.adapter_config, [config.segment_export_configs[0]], False
        )
    with pytest.raises(RuntimeActionSessionInputError):
        MultiActionCaptureSessionConfig(
            config.initial_cursor, config.adapter_config, (object(),), False
        )
    with pytest.raises(RuntimeActionSessionInputError):
        MultiActionCaptureSessionConfig(
            config.initial_cursor, config.adapter_config, config.segment_export_configs, 1
        )

    with pytest.raises(RuntimeActionSessionInputError, match="final_cursor"):
        MultiActionCaptureSessionResult(
            result.config,
            result.steps,
            result.results,
            PendingEventCaptureCursor(99, 99),
        )


def test_runner_rejects_wrong_input_types_before_execution():
    config = _session_config(1)
    step = _simple_step("action-a")
    with pytest.raises(RuntimeActionSessionInputError):
        run_multi_action_capture_session(object(), (step,), config=config)
    with pytest.raises(RuntimeActionSessionInputError):
        run_multi_action_capture_session(BattleState([]), [step], config=config)
    with pytest.raises(RuntimeActionSessionInputError):
        run_multi_action_capture_session(BattleState([]), (object(),), config=config)
    with pytest.raises(RuntimeActionSessionInputError):
        run_multi_action_capture_session(BattleState([]), (step,), config=object())
