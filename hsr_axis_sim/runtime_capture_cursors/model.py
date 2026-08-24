"""Immutable caller-owned cursor contracts for sequential pending-event captures."""

from __future__ import annotations

from dataclasses import dataclass

from hsr_axis_sim.runtime_state_captures import (
    BattleStatePendingEventSliceCaptureResult,
)
from hsr_axis_sim.runtime_trace_bridges import LegacyEventTraceBridgeConfig


class RuntimeCaptureCursorError(RuntimeError):
    """Base class for controlled pending-event cursor failures."""


class RuntimeCaptureCursorInputError(RuntimeCaptureCursorError):
    """Raised when cursor/request/result provenance is invalid."""


class StalePendingEventCaptureCursorError(RuntimeCaptureCursorError):
    """Raised when the cursor index is beyond the current pending-event list."""


def _require_non_negative_int(value: object, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise RuntimeCaptureCursorInputError(f"{name} must be a non-negative integer")
    return value


@dataclass(frozen=True)
class PendingEventCaptureCursor:
    pending_event_index: int
    next_runtime_sequence: int

    def __post_init__(self) -> None:
        _require_non_negative_int(self.pending_event_index, "pending_event_index")
        _require_non_negative_int(self.next_runtime_sequence, "next_runtime_sequence")


@dataclass(frozen=True)
class PendingEventCursorCaptureRequest:
    cursor: PendingEventCaptureCursor
    end_index: int
    bridge_config: LegacyEventTraceBridgeConfig

    def __post_init__(self) -> None:
        if not isinstance(self.cursor, PendingEventCaptureCursor):
            raise RuntimeCaptureCursorInputError("cursor has an invalid type")
        _require_non_negative_int(self.end_index, "end_index")
        if self.end_index < self.cursor.pending_event_index:
            raise RuntimeCaptureCursorInputError(
                "end_index must be greater than or equal to cursor.pending_event_index"
            )
        if not isinstance(self.bridge_config, LegacyEventTraceBridgeConfig):
            raise RuntimeCaptureCursorInputError("bridge_config has an invalid type")
        if self.bridge_config.start_sequence != self.cursor.next_runtime_sequence:
            raise RuntimeCaptureCursorInputError(
                "bridge_config.start_sequence must equal cursor.next_runtime_sequence"
            )

    @property
    def requested_event_count(self) -> int:
        return self.end_index - self.cursor.pending_event_index


@dataclass(frozen=True)
class PendingEventCursorCaptureResult:
    request: PendingEventCursorCaptureRequest
    capture_result: BattleStatePendingEventSliceCaptureResult
    next_cursor: PendingEventCaptureCursor

    def __post_init__(self) -> None:
        if not isinstance(self.request, PendingEventCursorCaptureRequest):
            raise RuntimeCaptureCursorInputError("request has an invalid type")
        if not isinstance(
            self.capture_result, BattleStatePendingEventSliceCaptureResult
        ):
            raise RuntimeCaptureCursorInputError("capture_result has an invalid type")
        if not isinstance(self.next_cursor, PendingEventCaptureCursor):
            raise RuntimeCaptureCursorInputError("next_cursor has an invalid type")

        capture_config = self.capture_result.config
        if capture_config.start_index != self.request.cursor.pending_event_index:
            raise RuntimeCaptureCursorInputError(
                "capture_result start_index must match request cursor"
            )
        if capture_config.end_index != self.request.end_index:
            raise RuntimeCaptureCursorInputError(
                "capture_result end_index must match request end_index"
            )
        if capture_config.bridge_config != self.request.bridge_config:
            raise RuntimeCaptureCursorInputError(
                "capture_result bridge_config must match request bridge_config"
            )
        if self.capture_result.captured_event_count != self.request.requested_event_count:
            raise RuntimeCaptureCursorInputError(
                "capture_result event count must match requested event count"
            )

        expected_next = PendingEventCaptureCursor(
            self.request.end_index,
            self.request.cursor.next_runtime_sequence
            + self.capture_result.captured_event_count,
        )
        if self.next_cursor != expected_next:
            raise RuntimeCaptureCursorInputError(
                "next_cursor must exactly follow captured index and sequence count"
            )

    @property
    def captured_event_count(self) -> int:
        return self.capture_result.captured_event_count
