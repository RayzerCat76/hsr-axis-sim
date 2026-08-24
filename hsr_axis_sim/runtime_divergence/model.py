"""Immutable first-divergence report models and controlled failures."""

from __future__ import annotations

from dataclasses import dataclass

from hsr_axis_sim.runtime_comparators import (
    RuntimeTraceFieldDifference,
    TraceRecordComparisonStatus,
)
from hsr_axis_sim.runtime_contracts import RuntimeTraceRecord


class RuntimeTraceDivergenceError(RuntimeError):
    """Base class for controlled first-divergence reporting failures."""


class RuntimeTraceDivergenceInputError(RuntimeTraceDivergenceError):
    """Raised when reporter input or a report model violates its contract."""


def _require_non_empty(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RuntimeTraceDivergenceInputError(f"{name} must be a non-empty string")
    return value


@dataclass(frozen=True)
class RuntimeTraceFirstDivergence:
    record_index: int
    record_status: TraceRecordComparisonStatus
    expected_record: RuntimeTraceRecord | None
    actual_record: RuntimeTraceRecord | None
    first_field_difference: RuntimeTraceFieldDifference | None
    record_difference_count: int

    def __post_init__(self) -> None:
        if not isinstance(self.record_index, int) or isinstance(self.record_index, bool) or self.record_index < 0:
            raise RuntimeTraceDivergenceInputError("record_index must be a non-negative integer")
        if not isinstance(self.record_status, TraceRecordComparisonStatus):
            raise RuntimeTraceDivergenceInputError("record_status has an invalid type")
        if self.record_status is TraceRecordComparisonStatus.MATCH:
            raise RuntimeTraceDivergenceInputError("first divergence cannot have MATCH status")
        if self.expected_record is not None and not isinstance(self.expected_record, RuntimeTraceRecord):
            raise RuntimeTraceDivergenceInputError("expected_record has an invalid type")
        if self.actual_record is not None and not isinstance(self.actual_record, RuntimeTraceRecord):
            raise RuntimeTraceDivergenceInputError("actual_record has an invalid type")
        if self.first_field_difference is not None and not isinstance(
            self.first_field_difference, RuntimeTraceFieldDifference
        ):
            raise RuntimeTraceDivergenceInputError("first_field_difference has an invalid type")
        if not isinstance(self.record_difference_count, int) or isinstance(self.record_difference_count, bool):
            raise RuntimeTraceDivergenceInputError("record_difference_count must be an integer")
        if self.record_difference_count < 0:
            raise RuntimeTraceDivergenceInputError("record_difference_count must be non-negative")

        if self.record_status is TraceRecordComparisonStatus.MISMATCH:
            if self.expected_record is None or self.actual_record is None:
                raise RuntimeTraceDivergenceInputError("MISMATCH requires both records")
            if self.first_field_difference is None or self.record_difference_count < 1:
                raise RuntimeTraceDivergenceInputError(
                    "MISMATCH requires a first field difference and positive difference count"
                )
        elif self.record_status is TraceRecordComparisonStatus.EXPECTED_ONLY:
            if self.expected_record is None or self.actual_record is not None:
                raise RuntimeTraceDivergenceInputError("EXPECTED_ONLY requires only an expected record")
            if self.first_field_difference is not None or self.record_difference_count != 0:
                raise RuntimeTraceDivergenceInputError(
                    "EXPECTED_ONLY cannot fabricate field differences"
                )
        elif self.record_status is TraceRecordComparisonStatus.ACTUAL_ONLY:
            if self.expected_record is not None or self.actual_record is None:
                raise RuntimeTraceDivergenceInputError("ACTUAL_ONLY requires only an actual record")
            if self.first_field_difference is not None or self.record_difference_count != 0:
                raise RuntimeTraceDivergenceInputError(
                    "ACTUAL_ONLY cannot fabricate field differences"
                )

    @property
    def expected_sequence(self) -> int | None:
        return self.expected_record.sequence if self.expected_record is not None else None

    @property
    def actual_sequence(self) -> int | None:
        return self.actual_record.sequence if self.actual_record is not None else None

    @property
    def expected_event_id(self) -> str | None:
        return self.expected_record.event.event_id if self.expected_record is not None else None

    @property
    def actual_event_id(self) -> str | None:
        return self.actual_record.event.event_id if self.actual_record is not None else None

    @property
    def expected_event_type(self) -> str | None:
        return self.expected_record.event.event_type.value if self.expected_record is not None else None

    @property
    def actual_event_type(self) -> str | None:
        return self.actual_record.event.event_type.value if self.actual_record is not None else None


@dataclass(frozen=True)
class RuntimeTraceFirstDivergenceReport:
    expected_trace_id: str
    actual_trace_id: str
    expected_record_count: int
    actual_record_count: int
    total_mismatch_count: int
    divergence: RuntimeTraceFirstDivergence | None

    def __post_init__(self) -> None:
        _require_non_empty(self.expected_trace_id, "expected_trace_id")
        _require_non_empty(self.actual_trace_id, "actual_trace_id")
        for value, name in (
            (self.expected_record_count, "expected_record_count"),
            (self.actual_record_count, "actual_record_count"),
            (self.total_mismatch_count, "total_mismatch_count"),
        ):
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise RuntimeTraceDivergenceInputError(f"{name} must be a non-negative integer")
        if self.divergence is not None and not isinstance(self.divergence, RuntimeTraceFirstDivergence):
            raise RuntimeTraceDivergenceInputError("divergence has an invalid type")

        maximum_positions = max(self.expected_record_count, self.actual_record_count)
        if self.total_mismatch_count > maximum_positions:
            raise RuntimeTraceDivergenceInputError("total_mismatch_count exceeds available record positions")
        if self.total_mismatch_count == 0:
            if self.divergence is not None:
                raise RuntimeTraceDivergenceInputError("matching report cannot contain a divergence")
            if self.expected_record_count != self.actual_record_count:
                raise RuntimeTraceDivergenceInputError("matching report requires equal record counts")
        else:
            if self.divergence is None:
                raise RuntimeTraceDivergenceInputError("diverged report requires a first divergence")
            if self.divergence.record_index >= maximum_positions:
                raise RuntimeTraceDivergenceInputError("divergence record_index is outside report bounds")

    @property
    def matches(self) -> bool:
        return self.divergence is None
