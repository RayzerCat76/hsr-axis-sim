"""Immutable contracts for deterministic captured trace segment stitching."""

from __future__ import annotations

from dataclasses import dataclass

from hsr_axis_sim.runtime_capture_cursors import PendingEventCursorCaptureResult
from hsr_axis_sim.runtime_contracts import RuntimeEvent
from hsr_axis_sim.runtime_exports import RuntimeTraceArtifact, TraceExportConfig


class RuntimeTraceStitchError(RuntimeError):
    """Base class for controlled captured-trace stitch failures."""


class RuntimeTraceStitchInputError(RuntimeTraceStitchError):
    """Raised when stitch input or result provenance is invalid."""


@dataclass(frozen=True)
class CapturedTraceStitchConfig:
    export_config: TraceExportConfig
    pretty: bool

    def __post_init__(self) -> None:
        if not isinstance(self.export_config, TraceExportConfig):
            raise RuntimeTraceStitchInputError("export_config has an invalid type")
        if not isinstance(self.pretty, bool):
            raise RuntimeTraceStitchInputError("pretty must be a bool")


def validate_and_flatten_segments(
    segments: object,
) -> tuple[tuple[PendingEventCursorCaptureResult, ...], tuple[RuntimeEvent, ...]]:
    if not isinstance(segments, tuple):
        raise RuntimeTraceStitchInputError("segments must be a tuple")
    if not segments:
        raise RuntimeTraceStitchInputError("segments must be non-empty")
    if any(not isinstance(item, PendingEventCursorCaptureResult) for item in segments):
        raise RuntimeTraceStitchInputError(
            "segments must contain only PendingEventCursorCaptureResult values"
        )

    first_adapter_config = segments[0].request.bridge_config.adapter_config
    flattened: list[RuntimeEvent] = []
    expected_sequence = segments[0].request.cursor.next_runtime_sequence

    previous = None
    for index, segment in enumerate(segments):
        if previous is not None and segment.request.cursor != previous.next_cursor:
            raise RuntimeTraceStitchInputError(
                f"segments[{index}] request cursor must equal previous next_cursor"
            )
        if segment.request.bridge_config.adapter_config != first_adapter_config:
            raise RuntimeTraceStitchInputError(
                "all segments must use the same LegacyEventAdapterConfig"
            )

        records = segment.capture_result.bridge_result.artifact.document.records
        for record in records:
            event = record.event
            if event.sequence != expected_sequence:
                raise RuntimeTraceStitchInputError(
                    "captured RuntimeEvent sequences must be exactly contiguous "
                    f"across segments: expected {expected_sequence}, got {event.sequence}"
                )
            flattened.append(event)
            expected_sequence += 1
        previous = segment

    return segments, tuple(flattened)


@dataclass(frozen=True)
class CapturedTraceStitchResult:
    config: CapturedTraceStitchConfig
    segments: tuple[PendingEventCursorCaptureResult, ...]
    artifact: RuntimeTraceArtifact

    def __post_init__(self) -> None:
        if not isinstance(self.config, CapturedTraceStitchConfig):
            raise RuntimeTraceStitchInputError("config has an invalid type")
        validated_segments, flattened = validate_and_flatten_segments(self.segments)
        if validated_segments is not self.segments:
            raise RuntimeTraceStitchInputError("segments provenance must be preserved")
        if not isinstance(self.artifact, RuntimeTraceArtifact):
            raise RuntimeTraceStitchInputError("artifact has an invalid type")

        document = self.artifact.document
        if document.trace_id != self.config.export_config.trace_id:
            raise RuntimeTraceStitchInputError(
                "artifact trace_id must match final export_config.trace_id"
            )
        if document.sequence_policy is not self.config.export_config.sequence_policy:
            raise RuntimeTraceStitchInputError(
                "artifact sequence_policy must match final export_config.sequence_policy"
            )
        if document.metadata != self.config.export_config.metadata:
            raise RuntimeTraceStitchInputError(
                "artifact metadata must match final export_config.metadata"
            )
        if self.artifact.pretty is not self.config.pretty:
            raise RuntimeTraceStitchInputError(
                "artifact pretty flag must match stitch config"
            )
        if document.record_count != len(flattened):
            raise RuntimeTraceStitchInputError(
                "artifact record_count must equal flattened captured event count"
            )
        for record, source_event in zip(document.records, flattened):
            if record.event is not source_event:
                raise RuntimeTraceStitchInputError(
                    "final artifact must preserve captured RuntimeEvent object identity/order"
                )

    @property
    def segment_count(self) -> int:
        return len(self.segments)

    @property
    def record_count(self) -> int:
        return self.artifact.document.record_count
