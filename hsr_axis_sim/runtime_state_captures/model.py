"""Immutable contracts for explicit BattleState event-slice trace capture."""

from __future__ import annotations

from dataclasses import dataclass

from hsr_axis_sim.runtime_trace_bridges import (
    LegacyEventTraceBridgeConfig,
    LegacyEventTraceBridgeResult,
)


class RuntimeStateCaptureError(RuntimeError):
    """Base class for controlled runtime state-capture failures."""


class RuntimeStateCaptureInputError(RuntimeStateCaptureError):
    """Raised when capture configuration or result provenance is invalid."""


@dataclass(frozen=True)
class BattleStatePendingEventSliceCaptureConfig:
    bridge_config: LegacyEventTraceBridgeConfig
    start_index: int
    end_index: int

    def __post_init__(self) -> None:
        if not isinstance(self.bridge_config, LegacyEventTraceBridgeConfig):
            raise RuntimeStateCaptureInputError("bridge_config has an invalid type")
        for name, value in (
            ("start_index", self.start_index),
            ("end_index", self.end_index),
        ):
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise RuntimeStateCaptureInputError(
                    f"{name} must be a non-negative integer"
                )
        if self.start_index > self.end_index:
            raise RuntimeStateCaptureInputError(
                "start_index must be less than or equal to end_index"
            )

    @property
    def requested_event_count(self) -> int:
        return self.end_index - self.start_index


@dataclass(frozen=True)
class BattleStatePendingEventSliceCaptureResult:
    config: BattleStatePendingEventSliceCaptureConfig
    pending_event_count_at_capture: int
    bridge_result: LegacyEventTraceBridgeResult

    def __post_init__(self) -> None:
        if not isinstance(self.config, BattleStatePendingEventSliceCaptureConfig):
            raise RuntimeStateCaptureInputError("config has an invalid type")
        if (
            not isinstance(self.pending_event_count_at_capture, int)
            or isinstance(self.pending_event_count_at_capture, bool)
            or self.pending_event_count_at_capture < 0
        ):
            raise RuntimeStateCaptureInputError(
                "pending_event_count_at_capture must be a non-negative integer"
            )
        if self.config.end_index > self.pending_event_count_at_capture:
            raise RuntimeStateCaptureInputError(
                "end_index must not exceed pending_event_count_at_capture"
            )
        if not isinstance(self.bridge_result, LegacyEventTraceBridgeResult):
            raise RuntimeStateCaptureInputError("bridge_result has an invalid type")
        if self.bridge_result.config != self.config.bridge_config:
            raise RuntimeStateCaptureInputError(
                "bridge_result config must match capture bridge_config"
            )
        if self.bridge_result.record_count != self.config.requested_event_count:
            raise RuntimeStateCaptureInputError(
                "bridge_result record_count must equal captured slice length"
            )

    @property
    def captured_event_count(self) -> int:
        return self.config.requested_event_count

    @property
    def next_index(self) -> int:
        return self.config.end_index
