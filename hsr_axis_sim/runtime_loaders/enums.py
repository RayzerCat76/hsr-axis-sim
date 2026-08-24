"""Explicit policies and outcomes for strict runtime trace loading."""

from enum import Enum

try:
    from enum import StrEnum
except ImportError:  # pragma: no cover - Python < 3.11 compatibility
    class StrEnum(str, Enum):
        """Minimal standard-library-compatible StrEnum fallback."""


class TraceCanonicalFormPolicy(StrEnum):
    COMPACT_ONLY = "COMPACT_ONLY"
    PRETTY_ONLY = "PRETTY_ONLY"
    EITHER_CANONICAL = "EITHER_CANONICAL"


class TraceCanonicalForm(StrEnum):
    COMPACT = "COMPACT"
    PRETTY = "PRETTY"


class TraceDigestPolicy(StrEnum):
    REQUIRE_MATCH = "REQUIRE_MATCH"
    VERIFY_IF_PROVIDED = "VERIFY_IF_PROVIDED"
    SKIP = "SKIP"


class TraceDigestStatus(StrEnum):
    MATCHED = "MATCHED"
    NOT_PROVIDED = "NOT_PROVIDED"
    SKIPPED = "SKIPPED"
