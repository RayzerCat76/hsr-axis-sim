"""Immutable Golden Replay validation models and controlled failures."""

from __future__ import annotations

from dataclasses import dataclass
import re

from hsr_axis_sim.runtime_comparators import RuntimeTraceComparisonResult
from hsr_axis_sim.runtime_divergence import RuntimeTraceFirstDivergenceReport
from hsr_axis_sim.runtime_loaders import (
    RuntimeTraceLoadResult,
    TraceCanonicalFormPolicy,
    TraceDigestStatus,
)


class GoldenReplayValidationError(RuntimeError):
    """Base class for controlled Golden Replay validation failures."""


class GoldenReplayValidationInputError(GoldenReplayValidationError):
    """Raised when Golden Replay configuration or result invariants are invalid."""


_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")


def _require_non_empty(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GoldenReplayValidationInputError(f"{name} must be a non-empty string")
    return value


@dataclass(frozen=True)
class GoldenReplayValidationConfig:
    replay_id: str
    expected_sha256: str
    canonical_form_policy: TraceCanonicalFormPolicy
    max_bytes: int

    def __post_init__(self) -> None:
        _require_non_empty(self.replay_id, "replay_id")
        if not isinstance(self.expected_sha256, str) or _SHA256_RE.fullmatch(self.expected_sha256) is None:
            raise GoldenReplayValidationInputError(
                "expected_sha256 must be exactly 64 lowercase hexadecimal characters"
            )
        if not isinstance(self.canonical_form_policy, TraceCanonicalFormPolicy):
            raise GoldenReplayValidationInputError("canonical_form_policy has an invalid type")
        if not isinstance(self.max_bytes, int) or isinstance(self.max_bytes, bool) or self.max_bytes <= 0:
            raise GoldenReplayValidationInputError("max_bytes must be a positive integer")


@dataclass(frozen=True)
class GoldenReplayValidationResult:
    config: GoldenReplayValidationConfig
    expected_load: RuntimeTraceLoadResult
    actual_load: RuntimeTraceLoadResult
    comparison: RuntimeTraceComparisonResult
    first_divergence: RuntimeTraceFirstDivergenceReport

    def __post_init__(self) -> None:
        if not isinstance(self.config, GoldenReplayValidationConfig):
            raise GoldenReplayValidationInputError("config has an invalid type")
        if not isinstance(self.expected_load, RuntimeTraceLoadResult):
            raise GoldenReplayValidationInputError("expected_load has an invalid type")
        if not isinstance(self.actual_load, RuntimeTraceLoadResult):
            raise GoldenReplayValidationInputError("actual_load has an invalid type")
        if not isinstance(self.comparison, RuntimeTraceComparisonResult):
            raise GoldenReplayValidationInputError("comparison has an invalid type")
        if not isinstance(self.first_divergence, RuntimeTraceFirstDivergenceReport):
            raise GoldenReplayValidationInputError("first_divergence has an invalid type")

        if self.expected_load.digest_status is not TraceDigestStatus.MATCHED:
            raise GoldenReplayValidationInputError("expected golden trace must have MATCHED digest status")
        if self.expected_load.expected_sha256 != self.config.expected_sha256:
            raise GoldenReplayValidationInputError("expected golden trace digest does not match config")
        if self.actual_load.digest_status is not TraceDigestStatus.NOT_PROVIDED:
            raise GoldenReplayValidationInputError("actual trace must not claim a pre-known digest")
        if self.actual_load.expected_sha256 is not None:
            raise GoldenReplayValidationInputError("actual trace expected_sha256 must be None")

        expected_document = self.expected_load.artifact.document
        actual_document = self.actual_load.artifact.document
        if self.comparison.expected_trace_id != expected_document.trace_id:
            raise GoldenReplayValidationInputError("comparison expected_trace_id does not match expected trace")
        if self.comparison.actual_trace_id != actual_document.trace_id:
            raise GoldenReplayValidationInputError("comparison actual_trace_id does not match actual trace")
        if self.comparison.expected_record_count != expected_document.record_count:
            raise GoldenReplayValidationInputError("comparison expected_record_count does not match expected trace")
        if self.comparison.actual_record_count != actual_document.record_count:
            raise GoldenReplayValidationInputError("comparison actual_record_count does not match actual trace")

        report = self.first_divergence
        if report.expected_trace_id != self.comparison.expected_trace_id:
            raise GoldenReplayValidationInputError("first-divergence expected_trace_id does not match comparison")
        if report.actual_trace_id != self.comparison.actual_trace_id:
            raise GoldenReplayValidationInputError("first-divergence actual_trace_id does not match comparison")
        if report.expected_record_count != self.comparison.expected_record_count:
            raise GoldenReplayValidationInputError("first-divergence expected_record_count does not match comparison")
        if report.actual_record_count != self.comparison.actual_record_count:
            raise GoldenReplayValidationInputError("first-divergence actual_record_count does not match comparison")
        if report.total_mismatch_count != self.comparison.mismatch_count:
            raise GoldenReplayValidationInputError("first-divergence mismatch count does not match comparison")
        if report.matches != self.comparison.matches:
            raise GoldenReplayValidationInputError("first-divergence match status does not match comparison")

    @property
    def matches(self) -> bool:
        return self.comparison.matches

    @property
    def expected_sha256(self) -> str:
        return self.expected_load.artifact.sha256

    @property
    def actual_sha256(self) -> str:
        return self.actual_load.artifact.sha256
