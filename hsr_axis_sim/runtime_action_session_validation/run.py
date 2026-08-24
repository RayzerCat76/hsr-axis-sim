"""Explicit composition of accepted ARCH-013, ARCH-014, and ARCH-015."""

from __future__ import annotations

from hsr_axis_sim.runtime_action_sessions import (
    ExplicitActionCaptureStep,
    MultiActionCaptureSessionConfig,
    run_multi_action_capture_session,
)
from hsr_axis_sim.runtime_golden_replays import GoldenReplayValidationConfig
from hsr_axis_sim.runtime_session_golden_validation import (
    validate_successful_session_against_golden,
)
from hsr_axis_sim.runtime_session_stitching import stitch_successful_action_session
from hsr_axis_sim.runtime_trace_stitching import CapturedTraceStitchConfig
from hsr_axis_sim.sim.state import BattleState

from .model import (
    EndToEndActionSessionValidationResult,
    RuntimeActionSessionValidationInputError,
)


def run_action_session_validation(
    state: BattleState,
    steps: tuple[ExplicitActionCaptureStep, ...],
    *,
    session_config: MultiActionCaptureSessionConfig,
    stitch_config: CapturedTraceStitchConfig,
    expected_payload_bytes: bytes,
    golden_config: GoldenReplayValidationConfig,
) -> EndToEndActionSessionValidationResult:
    """Run one caller-declared action session through accepted Golden validation.

    This boundary is intentionally non-transactional. Once ARCH-013 begins,
    simulator mutations are governed by its accepted failure semantics. Later
    ARCH-014/015 failures also propagate without rollback of completed actions.
    """

    if not isinstance(state, BattleState):
        raise RuntimeActionSessionValidationInputError("state must be BattleState")
    if not isinstance(steps, tuple) or not steps:
        raise RuntimeActionSessionValidationInputError(
            "steps must be a non-empty tuple"
        )
    if any(not isinstance(item, ExplicitActionCaptureStep) for item in steps):
        raise RuntimeActionSessionValidationInputError(
            "steps must contain only ExplicitActionCaptureStep values"
        )
    if not isinstance(session_config, MultiActionCaptureSessionConfig):
        raise RuntimeActionSessionValidationInputError(
            "session_config must be MultiActionCaptureSessionConfig"
        )
    if len(session_config.segment_export_configs) != len(steps):
        raise RuntimeActionSessionValidationInputError(
            "session_config segment_export_configs length must equal steps length"
        )
    if not isinstance(stitch_config, CapturedTraceStitchConfig):
        raise RuntimeActionSessionValidationInputError(
            "stitch_config must be CapturedTraceStitchConfig"
        )
    if not isinstance(expected_payload_bytes, bytes):
        raise RuntimeActionSessionValidationInputError(
            "expected_payload_bytes must be bytes"
        )
    if not isinstance(golden_config, GoldenReplayValidationConfig):
        raise RuntimeActionSessionValidationInputError(
            "golden_config must be GoldenReplayValidationConfig"
        )

    session_result = run_multi_action_capture_session(
        state,
        steps,
        config=session_config,
    )
    session_stitch_result = stitch_successful_action_session(
        session_result,
        config=stitch_config,
    )
    validation_result = validate_successful_session_against_golden(
        session_stitch_result,
        expected_payload_bytes,
        config=golden_config,
    )
    return EndToEndActionSessionValidationResult(
        session_result=session_result,
        session_stitch_result=session_stitch_result,
        validation_result=validation_result,
    )
