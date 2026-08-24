"""Immutable provenance contracts for end-to-end action-session validation."""

from __future__ import annotations

from dataclasses import dataclass

from hsr_axis_sim.runtime_action_sessions import MultiActionCaptureSessionResult
from hsr_axis_sim.runtime_session_golden_validation import (
    SuccessfulSessionGoldenValidationResult,
)
from hsr_axis_sim.runtime_session_stitching import SuccessfulSessionTraceStitchResult


class RuntimeActionSessionValidationError(RuntimeError):
    """Base class for controlled end-to-end session validation failures."""


class RuntimeActionSessionValidationInputError(RuntimeActionSessionValidationError):
    """Raised when orchestrator input or returned stage provenance is invalid."""


@dataclass(frozen=True)
class EndToEndActionSessionValidationResult:
    session_result: MultiActionCaptureSessionResult
    session_stitch_result: SuccessfulSessionTraceStitchResult
    validation_result: SuccessfulSessionGoldenValidationResult

    def __post_init__(self) -> None:
        if not isinstance(self.session_result, MultiActionCaptureSessionResult):
            raise RuntimeActionSessionValidationInputError(
                "session_result has an invalid type"
            )
        if not isinstance(
            self.session_stitch_result, SuccessfulSessionTraceStitchResult
        ):
            raise RuntimeActionSessionValidationInputError(
                "session_stitch_result has an invalid type"
            )
        if not isinstance(
            self.validation_result, SuccessfulSessionGoldenValidationResult
        ):
            raise RuntimeActionSessionValidationInputError(
                "validation_result has an invalid type"
            )
        if self.session_stitch_result.session_result is not self.session_result:
            raise RuntimeActionSessionValidationInputError(
                "ARCH-014 session_result must preserve the exact ARCH-013 result object"
            )
        if (
            self.validation_result.session_stitch_result
            is not self.session_stitch_result
        ):
            raise RuntimeActionSessionValidationInputError(
                "ARCH-015 session_stitch_result must preserve the exact ARCH-014 result object"
            )

    @property
    def matches(self) -> bool:
        return self.validation_result.matches

    @property
    def actual_sha256(self) -> str:
        return self.validation_result.actual_sha256
