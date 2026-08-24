"""Explicitly invoked adapters at the legacy/runtime-contract boundary."""

from .legacy_events import (
    LEGACY_EVENT_MAPPINGS,
    AmbiguousLegacyEventError,
    AmbiguousLegacyEventPolicy,
    LegacyEventAdapterConfig,
    LegacyEventAdapterError,
    LegacyEventMapping,
    LegacyEventSchemaError,
    UnknownLegacyEventPolicy,
    UnmappedLegacyEventError,
    adapt_legacy_event,
    adapt_legacy_event_stream,
)

__all__ = [
    "LEGACY_EVENT_MAPPINGS",
    "AmbiguousLegacyEventError",
    "AmbiguousLegacyEventPolicy",
    "LegacyEventAdapterConfig",
    "LegacyEventAdapterError",
    "LegacyEventMapping",
    "LegacyEventSchemaError",
    "UnknownLegacyEventPolicy",
    "UnmappedLegacyEventError",
    "adapt_legacy_event",
    "adapt_legacy_event_stream",
]
