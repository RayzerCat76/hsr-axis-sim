"""Immutable provenance contract for successful session trace stitching."""

from __future__ import annotations

from dataclasses import dataclass

from hsr_axis_sim.runtime_action_sessions import MultiActionCaptureSessionResult
from hsr_axis_sim.runtime_trace_stitching import CapturedTraceStitchResult


class RuntimeSessionStitchError(RuntimeError):
    """Base class for controlled successful-session stitch handoff failures."""


class RuntimeSessionStitchInputError(RuntimeSessionStitchError):
    """Raised when handoff input or result provenance is invalid."""


@dataclass(frozen=True)
class SuccessfulSessionTraceStitchResult:
    session_result: MultiActionCaptureSessionResult
    stitch_result: CapturedTraceStitchResult

    def __post_init__(self) -> None:
        if not isinstance(self.session_result, MultiActionCaptureSessionResult):
            raise RuntimeSessionStitchInputError(
                "session_result has an invalid type"
            )
        if not isinstance(self.stitch_result, CapturedTraceStitchResult):
            raise RuntimeSessionStitchInputError(
                "stitch_result has an invalid type"
            )

        expected_segments = tuple(
            action_result.capture_result
            for action_result in self.session_result.results
        )
        if len(self.stitch_result.segments) != len(expected_segments):
            raise RuntimeSessionStitchInputError(
                "stitch segment count must equal completed session capture count"
            )
        for index, (actual, expected) in enumerate(
            zip(self.stitch_result.segments, expected_segments)
        ):
            if actual is not expected:
                raise RuntimeSessionStitchInputError(
                    f"stitch segments[{index}] must preserve the exact session capture object"
                )

    @property
    def segment_count(self) -> int:
        return self.stitch_result.segment_count

    @property
    def record_count(self) -> int:
        return self.stitch_result.record_count
