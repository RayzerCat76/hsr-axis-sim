"""Immutable file-boundary models for strict Golden Replay manifests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import re

from hsr_axis_sim.runtime_golden_manifests import GoldenReplayManifestArtifact


_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")


class GoldenReplayManifestFileError(RuntimeError):
    """Base class for controlled manifest-file boundary failures."""


class GoldenReplayManifestFileInputError(GoldenReplayManifestFileError):
    """Raised when a manifest-file API input violates its contract."""


class GoldenReplayManifestFileReadError(GoldenReplayManifestFileError):
    """Raised when an explicit manifest file cannot be resolved or read safely."""


def _require_canonical_relative_posix_path(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise GoldenReplayManifestFileInputError(
            "manifest_relative_path must be a non-empty string"
        )
    if "\\" in value:
        raise GoldenReplayManifestFileInputError(
            "manifest_relative_path must use POSIX '/' separators"
        )
    path = PurePosixPath(value)
    if path.is_absolute():
        raise GoldenReplayManifestFileInputError(
            "manifest_relative_path must be relative"
        )
    if not path.parts or any(part in {".", ".."} for part in path.parts):
        raise GoldenReplayManifestFileInputError(
            "manifest_relative_path must not contain '.' or '..' segments"
        )
    canonical = path.as_posix()
    if value != canonical:
        raise GoldenReplayManifestFileInputError(
            "manifest_relative_path must be canonical relative POSIX form"
        )
    return value


@dataclass(frozen=True)
class GoldenReplayManifestFileSpec:
    manifest_relative_path: str
    max_bytes: int
    expected_sha256: str | None = None

    def __post_init__(self) -> None:
        _require_canonical_relative_posix_path(self.manifest_relative_path)
        if not isinstance(self.max_bytes, int) or isinstance(self.max_bytes, bool) or self.max_bytes <= 0:
            raise GoldenReplayManifestFileInputError(
                "max_bytes must be a positive integer"
            )
        if self.expected_sha256 is not None and (
            not isinstance(self.expected_sha256, str)
            or _SHA256_RE.fullmatch(self.expected_sha256) is None
        ):
            raise GoldenReplayManifestFileInputError(
                "expected_sha256 must be None or exactly 64 lowercase hexadecimal characters"
            )


@dataclass(frozen=True)
class GoldenReplayManifestFileLoadResult:
    spec: GoldenReplayManifestFileSpec
    base_directory: str
    manifest_path: str
    artifact: GoldenReplayManifestArtifact

    def __post_init__(self) -> None:
        if not isinstance(self.spec, GoldenReplayManifestFileSpec):
            raise GoldenReplayManifestFileInputError("spec has an invalid type")
        if not isinstance(self.base_directory, str) or not self.base_directory:
            raise GoldenReplayManifestFileInputError(
                "base_directory must be a non-empty string"
            )
        if not Path(self.base_directory).is_absolute():
            raise GoldenReplayManifestFileInputError(
                "base_directory must be an absolute path"
            )
        if not isinstance(self.manifest_path, str) or not self.manifest_path:
            raise GoldenReplayManifestFileInputError(
                "manifest_path must be a non-empty string"
            )
        manifest_path = Path(self.manifest_path)
        if not manifest_path.is_absolute():
            raise GoldenReplayManifestFileInputError(
                "manifest_path must be an absolute path"
            )
        try:
            manifest_path.relative_to(Path(self.base_directory))
        except ValueError as exc:
            raise GoldenReplayManifestFileInputError(
                "manifest_path must remain inside base_directory"
            ) from exc
        if not isinstance(self.artifact, GoldenReplayManifestArtifact):
            raise GoldenReplayManifestFileInputError("artifact has an invalid type")
        if self.spec.expected_sha256 is not None and self.artifact.sha256 != self.spec.expected_sha256:
            raise GoldenReplayManifestFileInputError(
                "artifact SHA-256 does not match spec.expected_sha256"
            )
