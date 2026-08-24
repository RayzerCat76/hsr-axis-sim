from dataclasses import FrozenInstanceError

import pytest

from hsr_axis_sim.runtime_comparators import (
    RuntimeTraceComparisonInputError,
    TraceRecordComparisonStatus,
    compare_runtime_trace_documents,
)
from hsr_axis_sim.runtime_contracts import RuntimeEvent, RuntimeEventType
from hsr_axis_sim.runtime_exports import (
    EmptyTracePolicy,
    TraceExportConfig,
    TraceSequencePolicy,
    build_runtime_trace_document,
)


def event(sequence, *, event_id=None, payload=None, event_type=RuntimeEventType.ACTION_START):
    return RuntimeEvent(
        event_id or f"event-{sequence}",
        event_type,
        sequence,
        None,
        None,
        None,
        None,
        None,
        None,
        payload or {},
    )


def document(events, *, trace_id="trace", metadata=None, policy=TraceSequencePolicy.CONTIGUOUS):
    return build_runtime_trace_document(
        events,
        config=TraceExportConfig(
            trace_id,
            policy,
            EmptyTracePolicy.ALLOW,
            metadata or {},
        ),
    )


def test_identical_record_streams_match_even_when_document_provenance_differs():
    expected = document([event(4), event(5)], trace_id="expected", metadata={"source": "manual"})
    actual = document(
        [event(4), event(5)],
        trace_id="actual",
        metadata={"source": "simulator"},
        policy=TraceSequencePolicy.STRICTLY_INCREASING,
    )

    result = compare_runtime_trace_documents(expected, actual)

    assert result.matches is True
    assert result.mismatch_count == 0
    assert result.expected_trace_id == "expected"
    assert result.actual_trace_id == "actual"
    assert [item.status for item in result.records] == [
        TraceRecordComparisonStatus.MATCH,
        TraceRecordComparisonStatus.MATCH,
    ]


def test_event_field_mismatch_is_reported_with_stable_path():
    expected = document([event(0, event_type=RuntimeEventType.ACTION_START)])
    actual = document([event(0, event_type=RuntimeEventType.ACTION_END)])

    result = compare_runtime_trace_documents(expected, actual)

    comparison = result.records[0]
    assert result.matches is False
    assert result.mismatch_count == 1
    assert comparison.status is TraceRecordComparisonStatus.MISMATCH
    assert [item.path for item in comparison.differences] == ["/event/event_type"]
    assert comparison.differences[0].expected_value == RuntimeEventType.ACTION_START.value
    assert comparison.differences[0].actual_value == RuntimeEventType.ACTION_END.value


def test_nested_payload_missing_key_and_pointer_escaping_are_deterministic():
    expected = document([event(0, payload={"a/b~c": {"x": 1, "y": 2}})])
    actual = document([event(0, payload={"a/b~c": {"x": 1}})])

    differences = compare_runtime_trace_documents(expected, actual).records[0].differences

    assert [item.path for item in differences] == ["/event/payload/a~1b~0c/y"]
    assert differences[0].expected_present is True
    assert differences[0].actual_present is False
    assert differences[0].expected_value == 2
    assert differences[0].actual_value is None


def test_json_numeric_types_are_compared_strictly():
    expected = document([event(0, payload={"value": 1})])
    actual = document([event(0, payload={"value": 1.0})])

    difference = compare_runtime_trace_documents(expected, actual).records[0].differences[0]

    assert difference.path == "/event/payload/value"
    assert type(difference.expected_value) is int
    assert type(difference.actual_value) is float


def test_extra_records_are_not_repaired_or_realigned():
    first = event(0, event_id="first")
    second = event(1, event_id="second")
    extra = event(1, event_id="extra")
    shifted = event(2, event_id="second")

    expected = document([first, second])
    actual = document([first, extra, shifted])

    result = compare_runtime_trace_documents(expected, actual)

    assert [item.status for item in result.records] == [
        TraceRecordComparisonStatus.MATCH,
        TraceRecordComparisonStatus.MISMATCH,
        TraceRecordComparisonStatus.ACTUAL_ONLY,
    ]
    assert result.expected_record_count == 2
    assert result.actual_record_count == 3
    assert result.mismatch_count == 2


def test_expected_only_tail_is_explicit():
    expected = document([event(0), event(1)])
    actual = document([event(0)])

    result = compare_runtime_trace_documents(expected, actual)

    assert result.records[1].status is TraceRecordComparisonStatus.EXPECTED_ONLY
    assert result.records[1].expected_record is expected.records[1]
    assert result.records[1].actual_record is None
    assert result.records[1].differences == ()


def test_difference_values_are_deeply_frozen_and_results_are_immutable():
    expected = document([event(0, payload={"nested": {"values": [1, 2]}})])
    actual = document([event(0, payload={})])

    result = compare_runtime_trace_documents(expected, actual)
    difference = result.records[0].differences[0]

    assert difference.path == "/event/payload/nested"
    assert tuple(difference.expected_value["values"]) == (1, 2)
    with pytest.raises(TypeError):
        difference.expected_value["new"] = 1
    with pytest.raises(FrozenInstanceError):
        result.expected_record_count = 99


def test_empty_traces_match_without_special_case_guessing():
    result = compare_runtime_trace_documents(
        document([], trace_id="expected-empty"),
        document([], trace_id="actual-empty"),
    )
    assert result.matches is True
    assert result.mismatch_count == 0
    assert result.records == ()


def test_wrong_input_types_are_rejected_before_comparison():
    valid = document([event(0)])
    with pytest.raises(RuntimeTraceComparisonInputError):
        compare_runtime_trace_documents(object(), valid)
    with pytest.raises(RuntimeTraceComparisonInputError):
        compare_runtime_trace_documents(valid, object())


def test_comparison_is_read_only_and_repeatable():
    expected = document([event(0, payload={"z": 3, "a": [1, 2]})])
    actual = document([event(0, payload={"z": 4, "a": [1, 9]})])
    before_expected = expected.records
    before_actual = actual.records

    first = compare_runtime_trace_documents(expected, actual)
    second = compare_runtime_trace_documents(expected, actual)

    assert first == second
    assert [item.path for item in first.records[0].differences] == [
        "/event/payload/a/1",
        "/event/payload/z",
    ]
    assert expected.records is before_expected
    assert actual.records is before_actual
