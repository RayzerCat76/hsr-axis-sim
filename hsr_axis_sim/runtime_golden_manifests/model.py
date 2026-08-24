"""Immutable Golden Replay manifest artifact models and controlled failures."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re

from hsr_axis_sim.runtime_golden_batches import GoldenReplayBatchPlan


MANIFEST_SCHEMA_NAME = "hsr_golden_replay_manifest"
MANIFEST_SCHEMA_VERSION = "1.0"
_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")


class GoldenReplayManifestError(RuntimeError):
    """Base class for controlled Golden Replay manifest failures."""


class GoldenReplayManifestInputError(GoldenReplayManifestError):
    """Raised when the manifest API receives an invalid contract input."""


class GoldenReplayManifestSizeLimitError(GoldenReplayManifestError):
    """Raised when manifest bytes exceed the explicit byte limit."""


class GoldenReplayManifestDigestMismatchError(GoldenReplayManifestError):
    """Raised when a supplied expected manifest SHA-256 does not match."""


class GoldenReplayManifestDecodeError(GoldenReplayManifestError):
    """Raised when manifest bytes are not strict decodable JSON."""


class GoldenReplayManifestSchemaError(GoldenReplayManifestError):
    """Raised when decoded manifest data violates schema v1."""


class GoldenReplayManifestCanonicalityError(GoldenReplayManifestError):
    """Raised when valid manifest data is not encoded as exact canonical bytes."""


@dataclass(frozen=True)
class GoldenReplayManifestArtifact:
    plan: GoldenReplayBatchPlan
    payload_bytes: bytes
    sha256: str

    def __post_init__(self) -> None:
        if not isinstance(self.plan, GoldenReplayBatchPlan):
            raise GoldenReplayManifestInputError("plan has an invalid type")
        if not isinstance(self.payload_bytes, bytes) or not self.payload_bytes:
            raise GoldenReplayManifestInputError("payload_bytes must be non-empty bytes")
        if not isinstance(self.sha256, str) or _SHA256_RE.fullmatch(self.sha256) is None:
            raise GoldenReplayManifestInputError(
                "sha256 must be exactly 64 lowercase hexadecimal characters"
            )
        computed = hashlib.sha256(self.payload_bytes).hexdigest()
        if computed != self.sha256:
            raise GoldenReplayManifestInputError("sha256 does not match payload_bytes")

    @property
    def byte_count(self) -> int:
        return len(self.payload_bytes)
