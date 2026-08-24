"""Deterministic comparison outcomes for runtime trace records."""

from enum import Enum

try:
    from enum import StrEnum
except ImportError:  # pragma: no cover - Python < 3.11 compatibility
    class StrEnum(str, Enum):
        """Minimal standard-library-compatible StrEnum fallback."""


class TraceRecordComparisonStatus(StrEnum):
    MATCH = "MATCH"
    MISMATCH = "MISMATCH"
    EXPECTED_ONLY = "EXPECTED_ONLY"
    ACTUAL_ONLY = "ACTUAL_ONLY"
