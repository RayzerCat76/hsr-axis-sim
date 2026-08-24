"""Read-only handoff from successful action sessions to accepted ARCH-010."""

from __future__ import annotations

from hsr_axis_sim.runtime_action_sessions import MultiActionCaptureSessionResult
from hsr_axis_sim.runtime_trace_stitching import (
    CapturedTraceStitchConfig,
    stitch_captured_trace_segments,
)

from .model import (
    RuntimeSessionStitchInputError,
    SuccessfulSessionTraceStitchResult,
)


def stitch_successful_action_session(
    session_result: MultiActionCaptureSessionResult,
    *,
    config: CapturedTraceStitchConfig,
) -> SuccessfulSessionTraceStitchResult:
    """Stitch exactly the completed ARCH-009 segments from one successful session."""

    if not isinstance(session_result, MultiActionCaptureSessionResult):
        raise RuntimeSessionStitchInputError(
            "session_result must be MultiActionCaptureSessionResult"
        )
    if not isinstance(config, CapturedTraceStitchConfig):
        raise RuntimeSessionStitchInputError(
            "config must be CapturedTraceStitchConfig"
        )

    segments = tuple(
        action_result.capture_result
        for action_result in session_result.results
    )
    stitch_result = stitch_captured_trace_segments(
        segments,
        config=config,
    )
    return SuccessfulSessionTraceStitchResult(
        session_result=session_result,
        stitch_result=stitch_result,
    )
