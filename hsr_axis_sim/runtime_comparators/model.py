"""Immutable result models and controlled failures for runtime trace comparison."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from hsr_axis_sim.runtime_contracts import RuntimeTraceRecord
from hsr_axis_sim.runtime_contracts.serialization import freeze_json

from .enums import TraceRecordComparisonStatus


class RuntimeTraceComparisonError(RuntimeError):
    """Base class for controlled trace-comparison failures."""


class RuntimeTraceComparisonInputError(RuntimeTraceComparisonError):
    """Raised when comparator input has the wrong contract type."""


@dataclass(frozen=True)
class RuntimeTraceFieldDifference:
    path: str
    expected_present: bool
    actual_present: bool
    expected_value: Any
    actual_value: Any

    def __post_init__(self) -> None:
        if not isinstance(self.path, str) or not self.path.startswith("/"):
            raise RuntimeTraceComparisonInputError("difference path must be a non-empty JSON-pointer-style path")
        if not isinstance(self.expected_present, bool) or not isinstance(self.actual_present, bool):
            raise RuntimeTraceComparisonInputError("difference presence flags must be bool values")
        if not self.expected_present and not self.actual_present:
            raise RuntimeTraceComparisonInputError("a difference must be present on at least one side")
        if not self.expected_present and self.expected_value is not None:
            raise RuntimeTraceComparisonInputError("absent expected value must be None")
        if not self.actual_present and self.actual_value is not None:
            raise RuntimeTraceComparisonInputError("absent actual value must be None")
        if self.expected_present:
            object.__setattr__(self, "expected_value", freeze_json(self.expected_value, path="expected_value"))
        if self.actual_present:
            object.__setattr__(self, "actual_value", freeze_json(self.actual_value, path="actual_value"))


@dataclass(frozen=True)
class RuntimeTraceRecordComparison:
    index: int
    status: TraceRecordComparisonStatus
    expected_record: RuntimeTraceRecord | None
    actual_record: RuntimeTraceRecord | None
    differences: tuple[RuntimeTraceFieldDifference, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.index, int) or isinstance(self.index, bool) or self.index < 0:
            raise RuntimeTraceComparisonInputError("record comparison index must be a non-negative integer")
        if not isinstance(self.status, TraceRecordComparisonStatus):
            raise RuntimeTraceComparisonInputError("record comparison status has an invalid type")
        if self.expected_record is not None and not isinstance(self.expected_record, RuntimeTraceRecord):
            raise RuntimeTraceComparisonInputError("expected_record has an invalid type")
        if self.actual_record is not None and not isinstance(self.actual_record, RuntimeTraceRecord):
            raise RuntimeTraceComparisonInputError("actual_record has an invalid type")
        if not isinstance(self.differences, tuple) or any(
            not isinstance(value, RuntimeTraceFieldDifference) for value in self.differences
        ):
            raise RuntimeTraceComparisonInputError("differences must be a tuple of RuntimeTraceFieldDifference values")

        if self.status is TraceRecordComparisonStatus.MATCH:
            if self.expected_record is None or self.actual_record is None or self.differences:
                raise RuntimeTraceComparisonInputError("MATCH requires both records and no differences")
        elif self.status is TraceRecordComparisonStatus.MISMATCH:
            if self.expected_record is None or self.actual_record is None or not self.differences:
                raise RuntimeTraceComparisonInputError("MISMATCH requires both records and at least one difference")
        elif self.status is TraceRecordComparisonStatus.EXPECTED_ONLY:
            if self.expected_record is None or self.actual_record is not None or self.differences:
                raise RuntimeTraceComparisonInputError("EXPECTED_ONLY requires only an expected record")
        elif self.status is TraceRecordComparisonStatus.ACTUAL_ONLY:
            if self.expected_record is not None or self.actual_record is None or self.differences:
                raise RuntimeTraceComparisonInputError("ACTUAL_ONLY requires only an actual record")


@dataclass(frozen=True)
class RuntimeTraceComparisonResult:
    expected_trace_id: str
    actual_trace_id: str
    expected_record_count: int
    actual_record_count: int
    records: tuple[RuntimeTraceRecordComparison, ...]

    def __post_init__(self) -> None:
        for value, name in (
            (self.expected_trace_id, "expected_trace_id"),
            (self.actual_trace_id, "actual_trace_id"),
        ):
            if not isinstance(value, str) or not value.strip():
                raise RuntimeTraceComparisonInputError(f"{name} must be a non-empty string")
        for value, name in (
            (self.expected_record_count, "expected_record_count"),
            (self.actual_record_count, "actual_record_count"),
        ):
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise RuntimeTraceComparisonInputError(f"{name} must be a non-negative integer")
        if not isinstance(self.records, tuple) or any(
            not isinstance(value, RuntimeTraceRecordComparison) for value in self.records
        ):
            raise RuntimeTraceComparisonInputError("records must be a tuple of RuntimeTraceRecordComparison values")
        if tuple(value.index for value in self.records) != tuple(range(len(self.records))):
            raise RuntimeTraceComparisonInputError("record comparison indices must be contiguous from zero")
        if sum(value.expected_record is not None for value in self.records) != self.expected_record_count:
            raise RuntimeTraceComparisonInputError("expected_record_count does not match comparison records")
        if sum(value.actual_record is not None for value in self.records) != self.actual_record_count:
            raise RuntimeTraceComparisonInputError("actual_record_count does not match comparison records")
        if len(self.records) != max(self.expected_record_count, self.actual_record_count):
            raise RuntimeTraceComparisonInputError("comparison record length does not match input lengths")

    @property
    def matches(self) -> bool:
        return all(value.status is TraceRecordComparisonStatus.MATCH for value in self.records)

    @property
    def mismatch_count(self) -> int:
        return sum(value.status is not TraceRecordComparisonStatus.MATCH for value in self.records)
