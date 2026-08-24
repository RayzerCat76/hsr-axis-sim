"""Loader configuration, result model, and controlled failures."""

from __future__ import annotations

from dataclasses import dataclass
import re

from hsr_axis_sim.runtime_exports import RuntimeTraceArtifact

from .enums import (
    TraceCanonicalForm,
    TraceCanonicalFormPolicy,
    TraceDigestPolicy,
    TraceDigestStatus,
)


class RuntimeTraceLoadError(RuntimeError):
    """Base class for controlled trace-load failures."""


class RuntimeTraceLoadConfigError(RuntimeTraceLoadError):
    pass


class RuntimeTraceSizeLimitError(RuntimeTraceLoadError):
    pass


class RuntimeTraceDigestMismatchError(RuntimeTraceLoadError):
    pass


class RuntimeTraceEncodingError(RuntimeTraceLoadError):
    pass


class RuntimeTraceJsonError(RuntimeTraceLoadError):
    pass


class DuplicateJsonKeyError(RuntimeTraceJsonError):
    pass


class RuntimeTraceSchemaError(RuntimeTraceLoadError):
    pass


class UnsupportedRuntimeTraceVersionError(RuntimeTraceSchemaError):
    pass


class RuntimeTraceIntegrityError(RuntimeTraceSchemaError):
    pass


class RuntimeTraceCanonicalityError(RuntimeTraceLoadError):
    pass


class RuntimeTraceReadError(RuntimeTraceLoadError):
    pass


_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")


def validate_sha256(value: object, *, field_name: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise RuntimeTraceLoadConfigError(
            f"{field_name} must be exactly 64 lowercase hexadecimal characters"
        )
    return value


@dataclass(frozen=True)
class RuntimeTraceLoadConfig:
    canonical_form_policy: TraceCanonicalFormPolicy
    digest_policy: TraceDigestPolicy
    expected_sha256: str | None
    max_bytes: int

    def __post_init__(self) -> None:
        if not isinstance(self.canonical_form_policy, TraceCanonicalFormPolicy):
            raise RuntimeTraceLoadConfigError("canonical_form_policy has an invalid type")
        if not isinstance(self.digest_policy, TraceDigestPolicy):
            raise RuntimeTraceLoadConfigError("digest_policy has an invalid type")
        if not isinstance(self.max_bytes, int) or isinstance(self.max_bytes, bool) or self.max_bytes <= 0:
            raise RuntimeTraceLoadConfigError("max_bytes must be a positive integer")
        if self.expected_sha256 is not None:
            validate_sha256(self.expected_sha256, field_name="expected_sha256")
        if self.digest_policy is TraceDigestPolicy.REQUIRE_MATCH and self.expected_sha256 is None:
            raise RuntimeTraceLoadConfigError("REQUIRE_MATCH requires expected_sha256")
        if self.digest_policy is TraceDigestPolicy.SKIP and self.expected_sha256 is not None:
            raise RuntimeTraceLoadConfigError("SKIP requires expected_sha256=None")


@dataclass(frozen=True)
class RuntimeTraceLoadResult:
    artifact: RuntimeTraceArtifact
    canonical_form: TraceCanonicalForm
    digest_status: TraceDigestStatus
    expected_sha256: str | None
    source_size_bytes: int

    def __post_init__(self) -> None:
        if not isinstance(self.artifact, RuntimeTraceArtifact):
            raise RuntimeTraceLoadConfigError("artifact must be RuntimeTraceArtifact")
        if not isinstance(self.canonical_form, TraceCanonicalForm):
            raise RuntimeTraceLoadConfigError("canonical_form has an invalid type")
        if not isinstance(self.digest_status, TraceDigestStatus):
            raise RuntimeTraceLoadConfigError("digest_status has an invalid type")
        if self.canonical_form is TraceCanonicalForm.PRETTY and not self.artifact.pretty:
            raise RuntimeTraceLoadConfigError("PRETTY canonical form requires artifact.pretty=True")
        if self.canonical_form is TraceCanonicalForm.COMPACT and self.artifact.pretty:
            raise RuntimeTraceLoadConfigError("COMPACT canonical form requires artifact.pretty=False")
        if not isinstance(self.source_size_bytes, int) or isinstance(self.source_size_bytes, bool):
            raise RuntimeTraceLoadConfigError("source_size_bytes must be an integer")
        if self.source_size_bytes != len(self.artifact.payload_bytes):
            raise RuntimeTraceLoadConfigError("source_size_bytes does not match artifact payload")
        if self.expected_sha256 is not None:
            validate_sha256(self.expected_sha256, field_name="expected_sha256")
        if self.digest_status is TraceDigestStatus.MATCHED:
            if self.expected_sha256 is None or self.expected_sha256 != self.artifact.sha256:
                raise RuntimeTraceLoadConfigError("MATCHED requires the artifact digest as expected_sha256")
        elif self.digest_status in {TraceDigestStatus.NOT_PROVIDED, TraceDigestStatus.SKIPPED}:
            if self.expected_sha256 is not None:
                raise RuntimeTraceLoadConfigError(
                    f"{self.digest_status.value} requires expected_sha256=None"
                )
