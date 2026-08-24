"""Explicit handoff from stitched actual trace bytes to accepted Golden validation."""

from __future__ import annotations

from hsr_axis_sim.runtime_contracts.serialization import canonical_json_dumps
from hsr_axis_sim.runtime_golden_replays import (
    GoldenReplayValidationConfig,
    render_golden_replay_validation_text,
    validate_golden_replay_bytes,
)
from hsr_axis_sim.runtime_trace_stitching import CapturedTraceStitchResult

from .model import (
    StitchedActualGoldenValidationResult,
    StitchedGoldenValidationInputError,
)


def validate_stitched_actual_against_golden(
    stitch_result: CapturedTraceStitchResult,
    expected_payload_bytes: bytes,
    *,
    config: GoldenReplayValidationConfig,
) -> StitchedActualGoldenValidationResult:
    """Pass exact ARCH-010 actual bytes into accepted Golden Replay validation."""

    if not isinstance(stitch_result, CapturedTraceStitchResult):
        raise StitchedGoldenValidationInputError(
            "stitch_result must be CapturedTraceStitchResult"
        )
    if not isinstance(expected_payload_bytes, bytes):
        raise StitchedGoldenValidationInputError(
            "expected_payload_bytes must be bytes"
        )
    if not isinstance(config, GoldenReplayValidationConfig):
        raise StitchedGoldenValidationInputError(
            "config must be GoldenReplayValidationConfig"
        )

    validation_result = validate_golden_replay_bytes(
        expected_payload_bytes,
        stitch_result.artifact.payload_bytes,
        config=config,
    )
    return StitchedActualGoldenValidationResult(
        stitch_result=stitch_result,
        validation_result=validation_result,
    )


def render_stitched_actual_golden_validation_text(
    result: StitchedActualGoldenValidationResult,
) -> str:
    """Render stitch provenance before the accepted Golden validation report."""

    if not isinstance(result, StitchedActualGoldenValidationResult):
        raise StitchedGoldenValidationInputError(
            "result must be StitchedActualGoldenValidationResult"
        )

    lines = [
        "STITCHED_ACTUAL_GOLDEN_PASS" if result.matches else "STITCHED_ACTUAL_GOLDEN_FAIL",
        f"stitched_trace_id={canonical_json_dumps(result.stitch_result.artifact.document.trace_id, pretty=False)}",
        f"stitched_actual_sha256={result.stitch_result.artifact.sha256}",
        f"segment_count={result.stitch_result.segment_count}",
        "GOLDEN_REPLAY_VALIDATION",
    ]
    golden_text = render_golden_replay_validation_text(
        result.validation_result
    ).rstrip("\n")
    lines.append(golden_text)
    return "\n".join(lines) + "\n"
