from dataclasses import FrozenInstanceError

import pytest

from hsr_axis_sim.runtime_comparators import compare_runtime_trace_documents
from hsr_axis_sim.runtime_contracts import RuntimeEvent, RuntimeEventType
from hsr_axis_sim.runtime_divergence import (
    RuntimeTraceDivergenceInputError,
    build_first_divergence_report,
    render_first_divergence_text,
)
from hsr_axis_sim.runtime_exports import (
    EmptyTracePolicy,
    TraceExportConfig,
    TraceSequencePolicy,
    build_runtime_trace_document,
)


def event(sequence, *, event_id=None, event_type=RuntimeEventType.ACTION_START, payload=None):
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


def document(events, *, trace_id="trace"):
    return build_runtime_trace_document(
        events,
        config=TraceExportConfig(
            trace_id,
            TraceSequencePolicy.CONTIGUOUS,
            EmptyTracePolicy.ALLOW,
            {},
        ),
    )


def report(expected, actual):
    return build_first_divergence_report(
        compare_runtime_trace_documents(expected, actual)
    )


def test_matching_comparison_produces_no_divergence_and_stable_text():
    value = report(
        document([event(0)], trace_id="expected"),
        document([event(0)], trace_id="actual"),
    )

    assert value.matches is True
    assert value.divergence is None
    assert value.total_mismatch_count == 0
    assert render_first_divergence_text(value) == (
        "TRACE_MATCH\n"
        'expected_trace_id="expected"\n'
        'actual_trace_id="actual"\n'
        "expected_record_count=1\n"
        "actual_record_count=1\n"
        "total_mismatch_count=0\n"
    )


def test_first_non_match_record_is_selected_and_later_divergence_is_ignored():
    expected = document(
        [
            event(0, event_id="same"),
            event(1, event_id="first", event_type=RuntimeEventType.ACTION_START),
            event(2, event_id="later", payload={"value": 1}),
        ],
        trace_id="expected",
    )
    actual = document(
        [
            event(0, event_id="same"),
            event(1, event_id="first", event_type=RuntimeEventType.ACTION_END),
            event(2, event_id="later", payload={"value": 2}),
        ],
        trace_id="actual",
    )

    value = report(expected, actual)
    divergence = value.divergence

    assert divergence is not None
    assert value.total_mismatch_count == 2
    assert divergence.record_index == 1
    assert divergence.expected_event_id == "first"
    assert divergence.actual_event_id == "first"
    assert divergence.first_field_difference is not None
    assert divergence.first_field_difference.path == "/event/event_type"


def test_first_field_difference_uses_existing_comparator_order_without_resorting():
    expected = document([event(0, payload={"z": 3, "a": [1, 2]})])
    actual = document([event(0, payload={"z": 4, "a": [1, 9]})])

    comparison = compare_runtime_trace_documents(expected, actual)
    assert [item.path for item in comparison.records[0].differences] == [
        "/event/payload/a/1",
        "/event/payload/z",
    ]

    divergence = build_first_divergence_report(comparison).divergence
    assert divergence is not None
    assert divergence.record_difference_count == 2
    assert divergence.first_field_difference is comparison.records[0].differences[0]
    assert divergence.first_field_difference.path == "/event/payload/a/1"


def test_expected_only_tail_is_reported_without_fabricated_field_difference():
    value = report(
        document([event(0), event(1, event_id="missing-actual")], trace_id="expected"),
        document([event(0)], trace_id="actual"),
    )
    divergence = value.divergence

    assert divergence is not None
    assert divergence.record_status.value == "EXPECTED_ONLY"
    assert divergence.record_index == 1
    assert divergence.expected_sequence == 1
    assert divergence.actual_sequence is None
    assert divergence.expected_event_id == "missing-actual"
    assert divergence.actual_event_id is None
    assert divergence.first_field_difference is None
    assert divergence.record_difference_count == 0

    text = render_first_divergence_text(value)
    assert "actual_sequence=ABSENT\n" in text
    assert "actual_event_id=ABSENT\n" in text
    assert "field_path=" not in text


def test_actual_only_tail_is_reported_without_fabricated_field_difference():
    value = report(
        document([event(0)], trace_id="expected"),
        document([event(0), event(1, event_id="extra-actual")], trace_id="actual"),
    )
    divergence = value.divergence

    assert divergence is not None
    assert divergence.record_status.value == "ACTUAL_ONLY"
    assert divergence.record_index == 1
    assert divergence.expected_sequence is None
    assert divergence.actual_sequence == 1
    assert divergence.expected_event_id is None
    assert divergence.actual_event_id == "extra-actual"
    assert divergence.first_field_difference is None
    assert divergence.record_difference_count == 0


def test_missing_and_present_null_are_distinct_in_structured_and_text_output():
    value = report(
        document([event(0, payload={"value": None})]),
        document([event(0, payload={})]),
    )
    difference = value.divergence.first_field_difference

    assert difference is not None
    assert difference.expected_present is True
    assert difference.expected_value is None
    assert difference.actual_present is False
    assert difference.actual_value is None

    text = render_first_divergence_text(value)
    assert "field_expected_present=true\n" in text
    assert "field_actual_present=false\n" in text
    assert "field_expected_value=null\n" in text
    assert "field_actual_value=ABSENT\n" in text


def test_canonical_rendering_is_deterministic_for_nested_json_and_unicode():
    expected = document(
        [event(0, payload={"value": {"z": 2, "a": ["星", 'x"y']}})],
        trace_id="expected",
    )
    actual = document([event(0, payload={})], trace_id="actual")

    value = report(expected, actual)
    first = render_first_divergence_text(value)
    second = render_first_divergence_text(value)

    assert first == second
    assert 'field_expected_value={"a":["星","x\\"y"],"z":2}\n' in first
    assert "field_actual_value=ABSENT\n" in first


def test_report_models_are_frozen():
    value = report(
        document([event(0, payload={"value": 1})]),
        document([event(0, payload={"value": 2})]),
    )

    with pytest.raises(FrozenInstanceError):
        value.total_mismatch_count = 99
    with pytest.raises(FrozenInstanceError):
        value.divergence.record_index = 99


def test_invalid_input_types_are_rejected():
    with pytest.raises(RuntimeTraceDivergenceInputError):
        build_first_divergence_report(object())
    with pytest.raises(RuntimeTraceDivergenceInputError):
        render_first_divergence_text(object())


def test_reporter_is_read_only_and_repeatable():
    expected = document([event(0), event(1, payload={"value": 1})])
    actual = document([event(0), event(1, payload={"value": 2})])
    comparison = compare_runtime_trace_documents(expected, actual)
    before_records = comparison.records
    before_differences = comparison.records[1].differences

    first = build_first_divergence_report(comparison)
    second = build_first_divergence_report(comparison)

    assert first == second
    assert render_first_divergence_text(first) == render_first_divergence_text(second)
    assert comparison.records is before_records
    assert comparison.records[1].differences is before_differences
