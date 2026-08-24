"""Explicit policies for read-only runtime trace export."""

from enum import Enum

try:
    from enum import StrEnum
except ImportError:  # pragma: no cover - Python < 3.11 compatibility
    class StrEnum(str, Enum):
        """Minimal standard-library-compatible StrEnum fallback."""


class TraceSequencePolicy(StrEnum):
    CONTIGUOUS = "CONTIGUOUS"
    STRICTLY_INCREASING = "STRICTLY_INCREASING"


class EmptyTracePolicy(StrEnum):
    ALLOW = "ALLOW"
    REJECT = "REJECT"
