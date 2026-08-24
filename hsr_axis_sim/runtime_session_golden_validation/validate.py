"""Read-only handoff from successful-session stitching to accepted ARCH-011."""

from __future__ import annotations

from hsr_axis_sim.runtime_golden_replays import GoldenReplayValidationConfig
from hsr_axis_sim.runtime_session_stitching import SuccessfulSessionTraceStitchResult
from hsr_axis_sim.runtime_stitched_golden_validation import (
    validate_stitched_actual_against_golden,
)

from .model import (
    RuntimeSessionGoldenValidationInputError,
    SuccessfulSessionGoldenValidationResult,
)


def validate_successful_session_against_golden(
    session_stitch_result: SuccessfulSessionTraceStitchResult,
    expected_payload_bytes: bytes,
    *,
    config: GoldenReplayValidationConfig,
) -> SuccessfulSessionGoldenValidationResult:
    """Validate one successful ARCH-014 result through accepted ARCH-011."""

    if not isinstance(
        session_stitch_result, SuccessfulSessionTraceStitchResult
    ):
        raise RuntimeSessionGoldenValidationInputError(
            "session_stitch_result must be SuccessfulSessionTraceStitchResult"
        )
    if not isinstance(expected_payload_bytes, bytes):
        raise RuntimeSessionGoldenValidationInputError(
            "expected_payload_bytes must be bytes"
        )
    if not isinstance(config, GoldenReplayValidationConfig):
        raise RuntimeSessionGoldenValidationInputError(
            "config must be GoldenReplayValidationConfig"
        )

    validation_result = validate_stitched_actual_against_golden(
        session_stitch_result.stitch_result,
        expected_payload_bytes,
        config=config,
    )
    return SuccessfulSessionGoldenValidationResult(
        session_stitch_result=session_stitch_result,
        validation_result=validation_result,
    )
