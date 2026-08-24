"""Explicit ordered orchestration of accepted ARCH-012 action captures."""

from __future__ import annotations

from hsr_axis_sim.runtime_action_captures import (
    SingleActionEventCaptureRequest,
    execute_action_and_capture_pending_events,
)
from hsr_axis_sim.runtime_trace_bridges import LegacyEventTraceBridgeConfig
from hsr_axis_sim.sim.state import BattleState

from .model import (
    ExplicitActionCaptureStep,
    MultiActionCaptureSessionConfig,
    MultiActionCaptureSessionFailure,
    MultiActionCaptureSessionResult,
    RuntimeActionSessionInputError,
)


def run_multi_action_capture_session(
    state: BattleState,
    steps: tuple[ExplicitActionCaptureStep, ...],
    *,
    config: MultiActionCaptureSessionConfig,
) -> MultiActionCaptureSessionResult:
    """Run explicit actions in declared order and capture each completed window.

    The session is intentionally non-transactional. A failed step is wrapped in
    `MultiActionCaptureSessionFailure`, chained from the original exception, and
    later steps are not executed. Any simulator mutations made by the failed
    step remain exactly as production execution left them.
    """

    if not isinstance(state, BattleState):
        raise RuntimeActionSessionInputError("state must be BattleState")
    if not isinstance(steps, tuple) or not steps:
        raise RuntimeActionSessionInputError("steps must be a non-empty tuple")
    if any(not isinstance(item, ExplicitActionCaptureStep) for item in steps):
        raise RuntimeActionSessionInputError(
            "steps must contain only ExplicitActionCaptureStep values"
        )
    if not isinstance(config, MultiActionCaptureSessionConfig):
        raise RuntimeActionSessionInputError(
            "config must be MultiActionCaptureSessionConfig"
        )
    if len(config.segment_export_configs) != len(steps):
        raise RuntimeActionSessionInputError(
            "segment_export_configs length must equal steps length"
        )

    current_cursor = config.initial_cursor
    completed: list = []

    for index, (step, export_config) in enumerate(
        zip(steps, config.segment_export_configs)
    ):
        try:
            bridge_config = LegacyEventTraceBridgeConfig(
                config.adapter_config,
                current_cursor.next_runtime_sequence,
                export_config,
                config.pretty,
            )
            result = execute_action_and_capture_pending_events(
                state,
                step.action,
                request=SingleActionEventCaptureRequest(
                    current_cursor,
                    bridge_config,
                ),
                turn_context=step.turn_context,
            )
        except Exception as exc:
            failure = MultiActionCaptureSessionFailure(
                failed_action_index=index,
                failed_action_id=step.action.id,
                completed_results=tuple(completed),
                last_successful_cursor=current_cursor,
            )
            raise failure from exc

        completed.append(result)
        current_cursor = result.next_cursor

    return MultiActionCaptureSessionResult(
        config=config,
        steps=steps,
        results=tuple(completed),
        final_cursor=current_cursor,
    )
