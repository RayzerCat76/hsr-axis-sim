"""Deterministic stitching of already-adapted captured runtime trace segments."""

from __future__ import annotations

from hsr_axis_sim.runtime_exports import (
    build_runtime_trace_artifact,
    build_runtime_trace_document,
)

from .model import (
    CapturedTraceStitchConfig,
    CapturedTraceStitchResult,
    RuntimeTraceStitchInputError,
    validate_and_flatten_segments,
)


def stitch_captured_trace_segments(
    segments: object,
    *,
    config: CapturedTraceStitchConfig,
) -> CapturedTraceStitchResult:
    """Stitch one explicit ordered segment tuple without re-adapting source events."""

    if not isinstance(config, CapturedTraceStitchConfig):
        raise RuntimeTraceStitchInputError("config must be CapturedTraceStitchConfig")
    validated_segments, events = validate_and_flatten_segments(segments)
    document = build_runtime_trace_document(events, config=config.export_config)
    artifact = build_runtime_trace_artifact(document, pretty=config.pretty)
    return CapturedTraceStitchResult(
        config=config,
        segments=validated_segments,
        artifact=artifact,
    )
