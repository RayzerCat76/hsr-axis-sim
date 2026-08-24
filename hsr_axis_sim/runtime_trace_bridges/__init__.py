"""Explicit composition bridges into accepted runtime trace artifacts."""

from .legacy import build_legacy_event_trace_artifact
from .model import (
    LegacyEventTraceBridgeConfig,
    LegacyEventTraceBridgeResult,
    RuntimeTraceBridgeError,
    RuntimeTraceBridgeInputError,
)

__all__ = [
    "LegacyEventTraceBridgeConfig",
    "LegacyEventTraceBridgeResult",
    "RuntimeTraceBridgeError",
    "RuntimeTraceBridgeInputError",
    "build_legacy_event_trace_artifact",
]
