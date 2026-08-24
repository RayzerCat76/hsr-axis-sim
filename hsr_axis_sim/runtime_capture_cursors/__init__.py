"""Explicit caller-owned cursor contracts for sequential runtime state capture."""

from .capture import capture_battle_state_pending_events_from_cursor
from .model import (
    PendingEventCaptureCursor,
    PendingEventCursorCaptureRequest,
    PendingEventCursorCaptureResult,
    RuntimeCaptureCursorError,
    RuntimeCaptureCursorInputError,
    StalePendingEventCaptureCursorError,
)

__all__ = [
    "PendingEventCaptureCursor",
    "PendingEventCursorCaptureRequest",
    "PendingEventCursorCaptureResult",
    "RuntimeCaptureCursorError",
    "RuntimeCaptureCursorInputError",
    "StalePendingEventCaptureCursorError",
    "capture_battle_state_pending_events_from_cursor",
]
