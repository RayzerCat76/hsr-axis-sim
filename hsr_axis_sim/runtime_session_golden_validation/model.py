"""Immutable provenance contract for successful-session Golden validation."""

from __future__ import annotations

from dataclasses import dataclass

from hsr_axis_sim.runtime_session_stitching import SuccessfulSessionTraceStitchResult
from hsr_axis_sim.runtime_stitched_golden_validation import (
    StitchedActualGoldenValidationResult,
)


class RuntimeSessionGoldenValidationError(RuntimeError):
    """Base class for controlled successful-session Golden handoff failures."""


class RuntimeSessionGoldenValidationInputError(RuntimeSessionGoldenValidationError):
    """Raised when handoff input or result provenance is invalid."""


@dataclass(frozen=True)
class SuccessfulSessionGoldenValidationResult:
    session_stitch_result: SuccessfulSessionTraceStitchResult
    validation_result: StitchedActualGoldenValidationResult

    def __post_init__(self) -> None:
        if not isinstance(
            self.session_stitch_result, SuccessfulSessionTraceStitchResult
        ):
            raise RuntimeSessionGoldenValidationInputError(
                "session_stitch_result has an invalid type"
            )
        if not isinstance(
            self.validation_result, StitchedActualGoldenValidationResult
        ):
            raise RuntimeSessionGoldenValidationInputError(
                "validation_result has an invalid type"
            )
        if (
            self.validation_result.stitch_result
            is not self.session_stitch_result.stitch_result
        ):
            raise RuntimeSessionGoldenValidationInputError(
                "validation stitch_result must preserve the exact ARCH-014 stitch object"
            )

    @property
    def matches(self) -> bool:
        return self.validation_result.matches

    @property
    def actual_sha256(self) -> str:
        return self.validation_result.actual_sha256
