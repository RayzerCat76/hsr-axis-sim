"""Immutable contracts for one explicit production Action capture window."""

from __future__ import annotations

from dataclasses import dataclass

from hsr_axis_sim.runtime_capture_cursors import (
    PendingEventCaptureCursor,
    PendingEventCursorCaptureResult,
)
from hsr_axis_sim.runtime_trace_bridges import LegacyEventTraceBridgeConfig
from hsr_axis_sim.sim.turn_context import TurnContext


class RuntimeActionCaptureError(RuntimeError):
    """Base class for controlled single-action capture failures."""


class RuntimeActionCaptureInputError(RuntimeActionCaptureError):
    """Raised when orchestration input or result provenance is invalid."""


class ActionCaptureCursorAlignmentError(RuntimeActionCaptureError):
    """Raised when the caller cursor is not aligned to the current event-list end."""


def _require_non_empty(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RuntimeActionCaptureInputError(f"{name} must be a non-empty string")
    return value


@dataclass(frozen=True)
class SingleActionEventCaptureRequest:
    cursor: PendingEventCaptureCursor
    bridge_config: LegacyEventTraceBridgeConfig

    def __post_init__(self) -> None:
        if not isinstance(self.cursor, PendingEventCaptureCursor):
            raise RuntimeActionCaptureInputError("cursor has an invalid type")
        if not isinstance(self.bridge_config, LegacyEventTraceBridgeConfig):
            raise RuntimeActionCaptureInputError("bridge_config has an invalid type")
        if self.bridge_config.start_sequence != self.cursor.next_runtime_sequence:
            raise RuntimeActionCaptureInputError(
                "bridge_config.start_sequence must equal cursor.next_runtime_sequence"
            )


@dataclass(frozen=True)
class SingleActionEventCaptureResult:
    request: SingleActionEventCaptureRequest
    action_id: str
    actor_id: str
    pending_event_count_before: int
    pending_event_count_after: int
    turn_context: TurnContext
    capture_result: PendingEventCursorCaptureResult

    def __post_init__(self) -> None:
        if not isinstance(self.request, SingleActionEventCaptureRequest):
            raise RuntimeActionCaptureInputError("request has an invalid type")
        _require_non_empty(self.action_id, "action_id")
        _require_non_empty(self.actor_id, "actor_id")
        for value, name in (
            (self.pending_event_count_before, "pending_event_count_before"),
            (self.pending_event_count_after, "pending_event_count_after"),
        ):
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise RuntimeActionCaptureInputError(
                    f"{name} must be a non-negative integer"
                )
        if self.pending_event_count_after < self.pending_event_count_before:
            raise RuntimeActionCaptureInputError(
                "pending_event_count_after must be >= pending_event_count_before"
            )
        if not isinstance(self.turn_context, TurnContext):
            raise RuntimeActionCaptureInputError("turn_context has an invalid type")
        if self.turn_context.actor_id != self.actor_id:
            raise RuntimeActionCaptureInputError(
                "turn_context.actor_id must match captured action actor_id"
            )
        if not isinstance(self.capture_result, PendingEventCursorCaptureResult):
            raise RuntimeActionCaptureInputError("capture_result has an invalid type")

        capture_request = self.capture_result.request
        if capture_request.cursor != self.request.cursor:
            raise RuntimeActionCaptureInputError(
                "capture_result cursor must match orchestration request cursor"
            )
        if capture_request.bridge_config != self.request.bridge_config:
            raise RuntimeActionCaptureInputError(
                "capture_result bridge_config must match orchestration request"
            )
        if self.pending_event_count_before != self.request.cursor.pending_event_index:
            raise RuntimeActionCaptureInputError(
                "pre-action event count must equal request cursor pending-event index"
            )
        if capture_request.end_index != self.pending_event_count_after:
            raise RuntimeActionCaptureInputError(
                "capture_result end_index must equal post-action event count"
            )
        expected_count = self.pending_event_count_after - self.pending_event_count_before
        if self.capture_result.captured_event_count != expected_count:
            raise RuntimeActionCaptureInputError(
                "captured event count must equal the exact post-action append window"
            )

    @property
    def captured_event_count(self) -> int:
        return self.capture_result.captured_event_count

    @property
    def next_cursor(self) -> PendingEventCaptureCursor:
        return self.capture_result.next_cursor
