"""Strict deterministic expected-vs-actual RuntimeTraceDocument comparison."""

from __future__ import annotations

from typing import Any, Mapping

from hsr_axis_sim.runtime_contracts.serialization import to_canonical_data
from hsr_axis_sim.runtime_exports import RuntimeTraceDocument

from .enums import TraceRecordComparisonStatus
from .model import (
    RuntimeTraceComparisonInputError,
    RuntimeTraceComparisonResult,
    RuntimeTraceFieldDifference,
    RuntimeTraceRecordComparison,
)


def _pointer_token(value: object) -> str:
    return str(value).replace("~", "~0").replace("/", "~1")


def _child_path(path: str, token: object) -> str:
    return f"{path}/{_pointer_token(token)}"


def _difference(
    *,
    path: str,
    expected_present: bool,
    actual_present: bool,
    expected_value: Any,
    actual_value: Any,
) -> RuntimeTraceFieldDifference:
    return RuntimeTraceFieldDifference(
        path=path,
        expected_present=expected_present,
        actual_present=actual_present,
        expected_value=expected_value,
        actual_value=actual_value,
    )


def _collect_differences(expected: Any, actual: Any, *, path: str = "") -> list[RuntimeTraceFieldDifference]:
    if type(expected) is not type(actual):
        return [
            _difference(
                path=path or "/",
                expected_present=True,
                actual_present=True,
                expected_value=expected,
                actual_value=actual,
            )
        ]

    if isinstance(expected, Mapping):
        differences: list[RuntimeTraceFieldDifference] = []
        for key in sorted(set(expected) | set(actual)):
            child = _child_path(path, key)
            expected_present = key in expected
            actual_present = key in actual
            if not expected_present or not actual_present:
                differences.append(
                    _difference(
                        path=child,
                        expected_present=expected_present,
                        actual_present=actual_present,
                        expected_value=expected[key] if expected_present else None,
                        actual_value=actual[key] if actual_present else None,
                    )
                )
                continue
            differences.extend(_collect_differences(expected[key], actual[key], path=child))
        return differences

    if isinstance(expected, list):
        differences = []
        shared = min(len(expected), len(actual))
        for index in range(shared):
            differences.extend(
                _collect_differences(expected[index], actual[index], path=_child_path(path, index))
            )
        for index in range(shared, max(len(expected), len(actual))):
            expected_present = index < len(expected)
            actual_present = index < len(actual)
            differences.append(
                _difference(
                    path=_child_path(path, index),
                    expected_present=expected_present,
                    actual_present=actual_present,
                    expected_value=expected[index] if expected_present else None,
                    actual_value=actual[index] if actual_present else None,
                )
            )
        return differences

    if expected != actual:
        return [
            _difference(
                path=path or "/",
                expected_present=True,
                actual_present=True,
                expected_value=expected,
                actual_value=actual,
            )
        ]
    return []


def compare_runtime_trace_documents(
    expected: RuntimeTraceDocument,
    actual: RuntimeTraceDocument,
) -> RuntimeTraceComparisonResult:
    """Compare ordered trace-record streams exactly without repair or realignment.

    Document identifiers, metadata, sequence policy, and derived summary fields are
    provenance/integrity data, not independent comparison axes. Runtime record
    content and position are the comparison contract.
    """

    if not isinstance(expected, RuntimeTraceDocument):
        raise RuntimeTraceComparisonInputError("expected must be a RuntimeTraceDocument")
    if not isinstance(actual, RuntimeTraceDocument):
        raise RuntimeTraceComparisonInputError("actual must be a RuntimeTraceDocument")

    comparisons: list[RuntimeTraceRecordComparison] = []
    for index in range(max(len(expected.records), len(actual.records))):
        expected_record = expected.records[index] if index < len(expected.records) else None
        actual_record = actual.records[index] if index < len(actual.records) else None

        if expected_record is None:
            comparisons.append(
                RuntimeTraceRecordComparison(
                    index,
                    TraceRecordComparisonStatus.ACTUAL_ONLY,
                    None,
                    actual_record,
                    (),
                )
            )
            continue
        if actual_record is None:
            comparisons.append(
                RuntimeTraceRecordComparison(
                    index,
                    TraceRecordComparisonStatus.EXPECTED_ONLY,
                    expected_record,
                    None,
                    (),
                )
            )
            continue

        differences = tuple(
            _collect_differences(
                to_canonical_data(expected_record),
                to_canonical_data(actual_record),
            )
        )
        comparisons.append(
            RuntimeTraceRecordComparison(
                index,
                TraceRecordComparisonStatus.MATCH if not differences else TraceRecordComparisonStatus.MISMATCH,
                expected_record,
                actual_record,
                differences,
            )
        )

    return RuntimeTraceComparisonResult(
        expected_trace_id=expected.trace_id,
        actual_trace_id=actual.trace_id,
        expected_record_count=len(expected.records),
        actual_record_count=len(actual.records),
        records=tuple(comparisons),
    )
