"""Selection and deterministic rendering of the first runtime trace divergence."""

from __future__ import annotations

from hsr_axis_sim.runtime_comparators import (
    RuntimeTraceComparisonResult,
    TraceRecordComparisonStatus,
)
from hsr_axis_sim.runtime_contracts.serialization import canonical_json_dumps

from .model import (
    RuntimeTraceDivergenceInputError,
    RuntimeTraceFirstDivergence,
    RuntimeTraceFirstDivergenceReport,
)


_ABSENT = "ABSENT"


def build_first_divergence_report(
    comparison: RuntimeTraceComparisonResult,
) -> RuntimeTraceFirstDivergenceReport:
    """Select the first existing ARCH-005 divergence without recomputing order."""

    if not isinstance(comparison, RuntimeTraceComparisonResult):
        raise RuntimeTraceDivergenceInputError(
            "comparison must be a RuntimeTraceComparisonResult"
        )

    selected = next(
        (
            record
            for record in comparison.records
            if record.status is not TraceRecordComparisonStatus.MATCH
        ),
        None,
    )

    divergence = None
    if selected is not None:
        first_difference = (
            selected.differences[0]
            if selected.status is TraceRecordComparisonStatus.MISMATCH
            else None
        )
        divergence = RuntimeTraceFirstDivergence(
            record_index=selected.index,
            record_status=selected.status,
            expected_record=selected.expected_record,
            actual_record=selected.actual_record,
            first_field_difference=first_difference,
            record_difference_count=len(selected.differences),
        )

    return RuntimeTraceFirstDivergenceReport(
        expected_trace_id=comparison.expected_trace_id,
        actual_trace_id=comparison.actual_trace_id,
        expected_record_count=comparison.expected_record_count,
        actual_record_count=comparison.actual_record_count,
        total_mismatch_count=comparison.mismatch_count,
        divergence=divergence,
    )


def _render_json(value: object) -> str:
    return canonical_json_dumps(value, pretty=False)


def _render_optional_record_value(value: object | None, *, present: bool) -> str:
    return _render_json(value) if present else _ABSENT


def render_first_divergence_text(report: RuntimeTraceFirstDivergenceReport) -> str:
    """Render one stable text report without mutating or re-evaluating comparison data."""

    if not isinstance(report, RuntimeTraceFirstDivergenceReport):
        raise RuntimeTraceDivergenceInputError(
            "report must be a RuntimeTraceFirstDivergenceReport"
        )

    lines = [
        "TRACE_MATCH" if report.matches else "TRACE_DIVERGED",
        f"expected_trace_id={_render_json(report.expected_trace_id)}",
        f"actual_trace_id={_render_json(report.actual_trace_id)}",
        f"expected_record_count={report.expected_record_count}",
        f"actual_record_count={report.actual_record_count}",
        f"total_mismatch_count={report.total_mismatch_count}",
    ]

    if report.matches:
        return "\n".join(lines) + "\n"

    divergence = report.divergence
    assert divergence is not None  # model invariant

    expected_present = divergence.expected_record is not None
    actual_present = divergence.actual_record is not None
    lines.extend(
        [
            f"record_index={divergence.record_index}",
            f"record_status={divergence.record_status.value}",
            "expected_sequence="
            + _render_optional_record_value(
                divergence.expected_sequence,
                present=expected_present,
            ),
            "actual_sequence="
            + _render_optional_record_value(
                divergence.actual_sequence,
                present=actual_present,
            ),
            "expected_event_id="
            + _render_optional_record_value(
                divergence.expected_event_id,
                present=expected_present,
            ),
            "actual_event_id="
            + _render_optional_record_value(
                divergence.actual_event_id,
                present=actual_present,
            ),
            "expected_event_type="
            + _render_optional_record_value(
                divergence.expected_event_type,
                present=expected_present,
            ),
            "actual_event_type="
            + _render_optional_record_value(
                divergence.actual_event_type,
                present=actual_present,
            ),
            f"record_difference_count={divergence.record_difference_count}",
        ]
    )

    difference = divergence.first_field_difference
    if difference is not None:
        lines.extend(
            [
                f"field_path={_render_json(difference.path)}",
                f"field_expected_present={_render_json(difference.expected_present)}",
                f"field_actual_present={_render_json(difference.actual_present)}",
                "field_expected_value="
                + (
                    _render_json(difference.expected_value)
                    if difference.expected_present
                    else _ABSENT
                ),
                "field_actual_value="
                + (
                    _render_json(difference.actual_value)
                    if difference.actual_present
                    else _ABSENT
                ),
            ]
        )

    return "\n".join(lines) + "\n"
