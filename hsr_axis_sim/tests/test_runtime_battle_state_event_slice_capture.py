from dataclasses import FrozenInstanceError

import pytest

from hsr_axis_sim.runtime_adapters import (
    AmbiguousLegacyEventPolicy,
    LegacyEventAdapterConfig,
    UnknownLegacyEventPolicy,
    UnmappedLegacyEventError,
)
from hsr_axis_sim.runtime_exports import (
    EmptyRuntimeTraceError,
    EmptyTracePolicy,
    TraceExportConfig,
    TraceSequencePolicy,
)
from hsr_axis_sim.runtime_state_captures import (
    BattleStatePendingEventSliceCaptureConfig,
    BattleStatePendingEventSliceCaptureResult,
    RuntimeStateCaptureInputError,
    capture_battle_state_pending_event_slice,
)
from hsr_axis_sim.runtime_trace_bridges import LegacyEventTraceBridgeConfig
from hsr_axis_sim.sim import BattleState, Unit
from hsr_axis_sim.sim.events import Event


def _state() -> BattleState:
    return BattleState(units=[Unit("ally", "Ally", "ally", 100)])


def _bridge_config(*, empty=EmptyTracePolicy.REJECT, unknown=UnknownLegacyEventPolicy.REJECT):
    return LegacyEventTraceBridgeConfig(
        LegacyEventAdapterConfig(
            "state-capture",
            unknown,
            AmbiguousLegacyEventPolicy.REJECT,
        ),
        20,
        TraceExportConfig(
            "state-event-slice",
            TraceSequencePolicy.CONTIGUOUS,
            empty,
            {"capture": "explicit-pending-event-slice"},
        ),
        False,
    )


def _populate(state: BattleState) -> None:
    state.emit_event(Event("turn_started", {"actor_id": "ally", "is_extra_turn": False}))
    state.emit_event(Event("action_started", {"actor_id": "ally", "action_id": "a"}))
    state.emit_event(Event("action_finished", {"actor_id": "ally", "action_id": "a"}))
    state.emit_event(Event("turn_ended", {"actor_id": "ally", "is_extra_turn": False}))


def test_captures_exact_middle_slice_in_current_list_order_without_mutating_state():
    state = _state()
    _populate(state)
    before = list(state.pending_events)
    config = BattleStatePendingEventSliceCaptureConfig(_bridge_config(), 1, 3)

    result = capture_battle_state_pending_event_slice(state, config=config)

    assert state.pending_events == before
    assert all(current is original for current, original in zip(state.pending_events, before))
    assert result.pending_event_count_at_capture == 4
    assert result.captured_event_count == 2
    assert result.next_index == 3
    assert result.bridge_result.record_count == 2
    records = result.bridge_result.artifact.document.records
    assert [record.sequence for record in records] == [20, 21]
    assert [record.event.event_id for record in records] == [
        "legacy:state-capture:20",
        "legacy:state-capture:21",
    ]
    assert [record.event.payload["legacy_type"] for record in records] == [
        "action_started",
        "action_finished",
    ]


def test_explicit_end_index_leaves_later_current_events_outside_snapshot():
    state = _state()
    _populate(state)
    result = capture_battle_state_pending_event_slice(
        state,
        config=BattleStatePendingEventSliceCaptureConfig(_bridge_config(), 0, 2),
    )
    assert result.pending_event_count_at_capture == 4
    assert result.captured_event_count == 2
    assert result.next_index == 2
    assert [record.event.payload["legacy_type"] for record in result.bridge_result.artifact.document.records] == [
        "turn_started",
        "action_started",
    ]
    assert len(state.pending_events) == 4


def test_built_artifact_is_immutable_snapshot_after_later_state_append_and_event_data_mutation():
    state = _state()
    event = Event("action_started", {"actor_id": "ally", "action_id": "original"})
    state.emit_event(event)
    result = capture_battle_state_pending_event_slice(
        state,
        config=BattleStatePendingEventSliceCaptureConfig(_bridge_config(), 0, 1),
    )

    event.data["action_id"] = "changed-after-capture"
    state.emit_event(Event("action_finished", {"actor_id": "ally", "action_id": "original"}))

    record = result.bridge_result.artifact.document.records[0]
    assert record.event.action_id == "original"
    assert record.event.payload["legacy_data"]["action_id"] == "original"
    assert result.pending_event_count_at_capture == 1
    assert result.next_index == 1
    assert len(state.pending_events) == 2


def test_delegated_adapter_failure_does_not_modify_pending_events():
    state = _state()
    state.emit_event(Event("future_event", {"value": 1}))
    before = list(state.pending_events)

    with pytest.raises(UnmappedLegacyEventError):
        capture_battle_state_pending_event_slice(
            state,
            config=BattleStatePendingEventSliceCaptureConfig(_bridge_config(), 0, 1),
        )

    assert state.pending_events == before
    assert state.pending_events[0] is before[0]


def test_unknown_preserve_policy_is_delegated_through_arch_007():
    state = _state()
    state.emit_event(Event("future_event", {"value": 1}))
    result = capture_battle_state_pending_event_slice(
        state,
        config=BattleStatePendingEventSliceCaptureConfig(
            _bridge_config(unknown=UnknownLegacyEventPolicy.PRESERVE_AS_CONTENT_DEFINED),
            0,
            1,
        ),
    )
    assert result.bridge_result.artifact.document.semantic_gap_ids == (
        "LEGACY_EVENT.UNMAPPED_TYPE",
    )


def test_empty_slice_follows_bridge_export_empty_policy_without_special_case():
    state = _state()
    allowed = capture_battle_state_pending_event_slice(
        state,
        config=BattleStatePendingEventSliceCaptureConfig(
            _bridge_config(empty=EmptyTracePolicy.ALLOW),
            0,
            0,
        ),
    )
    assert allowed.captured_event_count == 0
    assert allowed.bridge_result.record_count == 0
    assert allowed.pending_event_count_at_capture == 0

    with pytest.raises(EmptyRuntimeTraceError):
        capture_battle_state_pending_event_slice(
            state,
            config=BattleStatePendingEventSliceCaptureConfig(
                _bridge_config(empty=EmptyTracePolicy.REJECT),
                0,
                0,
            ),
        )


@pytest.mark.parametrize(
    ("start", "end"),
    [(-1, 0), (0, -1), (True, 1), (0, True), (2, 1)],
)
def test_config_rejects_invalid_explicit_slice_indexes(start, end):
    with pytest.raises(RuntimeStateCaptureInputError):
        BattleStatePendingEventSliceCaptureConfig(_bridge_config(), start, end)


def test_capture_rejects_end_index_beyond_current_pending_event_count():
    state = _state()
    state.emit_event(Event("turn_started", {"actor_id": "ally", "is_extra_turn": False}))
    with pytest.raises(RuntimeStateCaptureInputError, match="len\(state.pending_events\)"):
        capture_battle_state_pending_event_slice(
            state,
            config=BattleStatePendingEventSliceCaptureConfig(_bridge_config(), 0, 2),
        )
    assert len(state.pending_events) == 1


def test_capture_rejects_wrong_state_config_and_pending_event_container_shape():
    config = BattleStatePendingEventSliceCaptureConfig(_bridge_config(), 0, 0)
    with pytest.raises(RuntimeStateCaptureInputError):
        capture_battle_state_pending_event_slice(object(), config=config)
    state = _state()
    with pytest.raises(RuntimeStateCaptureInputError):
        capture_battle_state_pending_event_slice(state, config=object())
    state.pending_events = ()
    with pytest.raises(RuntimeStateCaptureInputError, match="must be a list"):
        capture_battle_state_pending_event_slice(state, config=config)


def test_capture_config_and_result_are_frozen_and_result_alignment_is_strict():
    state = _state()
    _populate(state)
    config = BattleStatePendingEventSliceCaptureConfig(_bridge_config(), 0, 2)
    result = capture_battle_state_pending_event_slice(state, config=config)

    with pytest.raises(FrozenInstanceError):
        config.end_index = 3
    with pytest.raises(FrozenInstanceError):
        result.pending_event_count_at_capture = 99

    wrong_config = BattleStatePendingEventSliceCaptureConfig(_bridge_config(), 0, 1)
    with pytest.raises(RuntimeStateCaptureInputError, match="record_count"):
        BattleStatePendingEventSliceCaptureResult(
            wrong_config,
            result.pending_event_count_at_capture,
            result.bridge_result,
        )
    with pytest.raises(RuntimeStateCaptureInputError, match="end_index"):
        BattleStatePendingEventSliceCaptureResult(
            config,
            1,
            result.bridge_result,
        )
