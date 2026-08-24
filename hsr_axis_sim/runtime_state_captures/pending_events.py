"""Non-mutating explicit capture of a BattleState pending-event slice."""

from __future__ import annotations

from hsr_axis_sim.runtime_trace_bridges import build_legacy_event_trace_artifact
from hsr_axis_sim.sim.state import BattleState

from .model import (
    BattleStatePendingEventSliceCaptureConfig,
    BattleStatePendingEventSliceCaptureResult,
    RuntimeStateCaptureInputError,
)


def capture_battle_state_pending_event_slice(
    state: BattleState,
    *,
    config: BattleStatePendingEventSliceCaptureConfig,
) -> BattleStatePendingEventSliceCaptureResult:
    """Capture exactly one explicit current pending-event list slice without mutation."""

    if not isinstance(state, BattleState):
        raise RuntimeStateCaptureInputError("state must be BattleState")
    if not isinstance(config, BattleStatePendingEventSliceCaptureConfig):
        raise RuntimeStateCaptureInputError(
            "config must be BattleStatePendingEventSliceCaptureConfig"
        )
    if not isinstance(state.pending_events, list):
        raise RuntimeStateCaptureInputError(
            "BattleState.pending_events must be a list at capture time"
        )

    pending_event_count = len(state.pending_events)
    if config.end_index > pending_event_count:
        raise RuntimeStateCaptureInputError(
            "end_index must not exceed len(state.pending_events) at capture time"
        )

    event_snapshot = tuple(
        state.pending_events[config.start_index : config.end_index]
    )
    bridge_result = build_legacy_event_trace_artifact(
        event_snapshot,
        config=config.bridge_config,
    )
    return BattleStatePendingEventSliceCaptureResult(
        config=config,
        pending_event_count_at_capture=pending_event_count,
        bridge_result=bridge_result,
    )
