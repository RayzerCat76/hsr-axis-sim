"""Immutable provenance contracts for stitched actual Golden validation."""

from __future__ import annotations

from dataclasses import dataclass

from hsr_axis_sim.runtime_golden_replays import GoldenReplayValidationResult
from hsr_axis_sim.runtime_trace_stitching import CapturedTraceStitchResult


class StitchedGoldenValidationError(RuntimeError):
    """Base class for controlled stitched Golden validation failures."""


class StitchedGoldenValidationInputError(StitchedGoldenValidationError):
    """Raised when handoff input or result provenance is invalid."""


@dataclass(frozen=True)
class StitchedActualGoldenValidationResult:
    stitch_result: CapturedTraceStitchResult
    validation_result: GoldenReplayValidationResult

    def __post_init__(self) -> None:
        if not isinstance(self.stitch_result, CapturedTraceStitchResult):
            raise StitchedGoldenValidationInputError(
                "stitch_result has an invalid type"
            )
        if not isinstance(self.validation_result, GoldenReplayValidationResult):
            raise StitchedGoldenValidationInputError(
                "validation_result has an invalid type"
            )

        stitched_artifact = self.stitch_result.artifact
        actual_artifact = self.validation_result.actual_load.artifact
        if actual_artifact.payload_bytes != stitched_artifact.payload_bytes:
            raise StitchedGoldenValidationInputError(
                "Golden actual payload bytes must exactly equal stitched artifact bytes"
            )
        if actual_artifact.sha256 != stitched_artifact.sha256:
            raise StitchedGoldenValidationInputError(
                "Golden actual SHA-256 must exactly equal stitched artifact SHA-256"
            )
        if actual_artifact.document != stitched_artifact.document:
            raise StitchedGoldenValidationInputError(
                "Golden actual document must equal stitched artifact document"
            )

    @property
    def matches(self) -> bool:
        return self.validation_result.matches

    @property
    def actual_sha256(self) -> str:
        return self.stitch_result.artifact.sha256
