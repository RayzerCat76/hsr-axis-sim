"""Immutable contracts for explicit legacy-event trace bridging."""

from __future__ import annotations

from dataclasses import dataclass

from hsr_axis_sim.runtime_adapters import LegacyEventAdapterConfig
from hsr_axis_sim.runtime_exports import RuntimeTraceArtifact, TraceExportConfig


class RuntimeTraceBridgeError(RuntimeError):
    """Base class for controlled trace-bridge failures."""


class RuntimeTraceBridgeInputError(RuntimeTraceBridgeError):
    """Raised when bridge configuration or result provenance is invalid."""


@dataclass(frozen=True)
class LegacyEventTraceBridgeConfig:
    adapter_config: LegacyEventAdapterConfig
    start_sequence: int
    export_config: TraceExportConfig
    pretty: bool

    def __post_init__(self) -> None:
        if not isinstance(self.adapter_config, LegacyEventAdapterConfig):
            raise RuntimeTraceBridgeInputError("adapter_config has an invalid type")
        if (
            not isinstance(self.start_sequence, int)
            or isinstance(self.start_sequence, bool)
            or self.start_sequence < 0
        ):
            raise RuntimeTraceBridgeInputError(
                "start_sequence must be a non-negative integer"
            )
        if not isinstance(self.export_config, TraceExportConfig):
            raise RuntimeTraceBridgeInputError("export_config has an invalid type")
        if not isinstance(self.pretty, bool):
            raise RuntimeTraceBridgeInputError("pretty must be a bool")


@dataclass(frozen=True)
class LegacyEventTraceBridgeResult:
    config: LegacyEventTraceBridgeConfig
    artifact: RuntimeTraceArtifact

    def __post_init__(self) -> None:
        if not isinstance(self.config, LegacyEventTraceBridgeConfig):
            raise RuntimeTraceBridgeInputError("config has an invalid type")
        if not isinstance(self.artifact, RuntimeTraceArtifact):
            raise RuntimeTraceBridgeInputError("artifact has an invalid type")
        document = self.artifact.document
        if document.trace_id != self.config.export_config.trace_id:
            raise RuntimeTraceBridgeInputError(
                "artifact trace_id must match export_config.trace_id"
            )
        if document.sequence_policy is not self.config.export_config.sequence_policy:
            raise RuntimeTraceBridgeInputError(
                "artifact sequence_policy must match export_config.sequence_policy"
            )
        if document.metadata != self.config.export_config.metadata:
            raise RuntimeTraceBridgeInputError(
                "artifact metadata must match export_config.metadata"
            )
        if self.artifact.pretty is not self.config.pretty:
            raise RuntimeTraceBridgeInputError(
                "artifact pretty flag must match bridge config"
            )

        for index, record in enumerate(document.records):
            expected_sequence = self.config.start_sequence + index
            if record.sequence != expected_sequence:
                raise RuntimeTraceBridgeInputError(
                    "artifact record sequences must match bridge start_sequence and source order"
                )
            expected_event_id = (
                f"legacy:{self.config.adapter_config.stream_id}:{expected_sequence}"
            )
            if record.event.event_id != expected_event_id:
                raise RuntimeTraceBridgeInputError(
                    "artifact event IDs must match adapter stream_id and sequence"
                )

    @property
    def record_count(self) -> int:
        return self.artifact.document.record_count
