"""Exact schema-v1 reconstruction and independent document integrity."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any

from hsr_axis_sim.runtime_contracts import RuntimeEvent, RuntimeEventType, RuntimeTraceRecord
from hsr_axis_sim.runtime_exports import RuntimeTraceDocument, TraceSequencePolicy
from hsr_axis_sim.runtime_exports.model import RuntimeTraceExportSchemaError

from .model import (
    RuntimeTraceIntegrityError,
    RuntimeTraceSchemaError,
    UnsupportedRuntimeTraceVersionError,
)


TOP_LEVEL_FIELDS = frozenset({
    "schema_name", "schema_version", "trace_id", "sequence_policy",
    "record_count", "first_sequence", "last_sequence", "event_type_counts",
    "semantic_gap_ids", "records", "metadata",
})
RECORD_FIELDS = frozenset({
    "sequence", "event", "action_context", "attack_context", "hit_context",
    "numeric_values", "notes",
})
EVENT_FIELDS = frozenset({
    "event_id", "event_type", "sequence", "action_id", "attack_id", "hit_id",
    "actor_id", "source_id", "target_id", "payload",
})


def _exact_keys(value: object, expected: frozenset[str], name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RuntimeTraceSchemaError(f"{name} must be an object")
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise RuntimeTraceSchemaError(f"{name} fields mismatch; missing={missing}, extra={extra}")
    return value


def _integer(value: object, name: str, *, nullable: bool = False) -> int | None:
    if nullable and value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool):
        raise RuntimeTraceSchemaError(f"{name} must be an integer")
    if value < 0:
        raise RuntimeTraceSchemaError(f"{name} must be non-negative")
    return value


def _non_empty_string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RuntimeTraceSchemaError(f"{name} must be a non-empty string")
    return value


def _optional_id(value: object, name: str) -> str | None:
    if value is None:
        return None
    return _non_empty_string(value, name)


def _event_from_data(value: object, index: int) -> RuntimeEvent:
    data = _exact_keys(value, EVENT_FIELDS, f"records[{index}].event")
    try:
        event_type = RuntimeEventType(data["event_type"])
    except (TypeError, ValueError) as exc:
        raise RuntimeTraceSchemaError(f"records[{index}].event.event_type is unknown") from exc
    if not isinstance(data["payload"], dict):
        raise RuntimeTraceSchemaError(f"records[{index}].event.payload must be an object")
    fields = {
        "event_id": _non_empty_string(data["event_id"], "event_id"),
        "event_type": event_type,
        "sequence": _integer(data["sequence"], "event.sequence"),
        "action_id": _optional_id(data["action_id"], "action_id"),
        "attack_id": _optional_id(data["attack_id"], "attack_id"),
        "hit_id": _optional_id(data["hit_id"], "hit_id"),
        "actor_id": _optional_id(data["actor_id"], "actor_id"),
        "source_id": _optional_id(data["source_id"], "source_id"),
        "target_id": _optional_id(data["target_id"], "target_id"),
        "payload": data["payload"],
    }
    try:
        return RuntimeEvent(**fields)
    except (TypeError, ValueError) as exc:
        raise RuntimeTraceSchemaError(f"invalid records[{index}].event: {exc}") from exc


def _record_from_data(value: object, index: int) -> RuntimeTraceRecord:
    data = _exact_keys(value, RECORD_FIELDS, f"records[{index}]")
    sequence = _integer(data["sequence"], f"records[{index}].sequence")
    if data["action_context"] is not None or data["attack_context"] is not None or data["hit_context"] is not None:
        raise RuntimeTraceSchemaError("schema v1 record contexts must be null")
    if not isinstance(data["numeric_values"], dict) or data["numeric_values"]:
        raise RuntimeTraceSchemaError("schema v1 numeric_values must be an empty object")
    if not isinstance(data["notes"], list) or data["notes"]:
        raise RuntimeTraceSchemaError("schema v1 notes must be an empty array")
    event = _event_from_data(data["event"], index)
    try:
        return RuntimeTraceRecord(sequence, event, None, None, None, {}, ())
    except (TypeError, ValueError) as exc:
        raise RuntimeTraceSchemaError(f"invalid records[{index}]: {exc}") from exc


def reconstruct_runtime_trace_document_v1(value: object) -> RuntimeTraceDocument:
    data = _exact_keys(value, TOP_LEVEL_FIELDS, "document")
    if data["schema_name"] != "hsr_runtime_trace":
        raise RuntimeTraceSchemaError("schema_name must equal hsr_runtime_trace")
    if data["schema_version"] != "1.0":
        raise UnsupportedRuntimeTraceVersionError(
            f"unsupported runtime trace schema version: {data['schema_version']!r}"
        )
    trace_id = _non_empty_string(data["trace_id"], "trace_id")
    try:
        sequence_policy = TraceSequencePolicy(data["sequence_policy"])
    except (TypeError, ValueError) as exc:
        raise RuntimeTraceSchemaError("sequence_policy is unknown") from exc
    record_count = _integer(data["record_count"], "record_count")
    first_sequence = _integer(data["first_sequence"], "first_sequence", nullable=True)
    last_sequence = _integer(data["last_sequence"], "last_sequence", nullable=True)
    if not isinstance(data["records"], list):
        raise RuntimeTraceSchemaError("records must be an array")
    records = tuple(_record_from_data(record, index) for index, record in enumerate(data["records"]))
    if not isinstance(data["event_type_counts"], dict):
        raise RuntimeTraceSchemaError("event_type_counts must be an object")
    counts: dict[str, int] = {}
    for key, count in data["event_type_counts"].items():
        try:
            RuntimeEventType(key)
        except (TypeError, ValueError) as exc:
            raise RuntimeTraceSchemaError(f"unknown event_type_counts key: {key!r}") from exc
        counts[key] = _integer(count, f"event_type_counts.{key}")
    if not isinstance(data["semantic_gap_ids"], list):
        raise RuntimeTraceSchemaError("semantic_gap_ids must be an array")
    gaps = tuple(_non_empty_string(item, "semantic gap ID") for item in data["semantic_gap_ids"])
    if gaps != tuple(sorted(set(gaps))):
        raise RuntimeTraceIntegrityError(
            "semantic_gap_ids summary must already be sorted and unique"
        )
    if not isinstance(data["metadata"], dict):
        raise RuntimeTraceSchemaError("metadata must be an object")
    try:
        return RuntimeTraceDocument(
            trace_id=trace_id,
            sequence_policy=sequence_policy,
            record_count=record_count,
            first_sequence=first_sequence,
            last_sequence=last_sequence,
            event_type_counts=counts,
            semantic_gap_ids=gaps,
            records=records,
            metadata=data["metadata"],
        )
    except RuntimeTraceExportSchemaError as exc:
        raise RuntimeTraceIntegrityError(f"document contract integrity failed: {exc}") from exc
    except (TypeError, ValueError) as exc:
        raise RuntimeTraceSchemaError(f"document reconstruction failed: {exc}") from exc


def _semantic_gaps(event: RuntimeEvent) -> tuple[str, ...]:
    if "adapter" not in event.payload:
        return ()
    adapter = event.payload["adapter"]
    if not isinstance(adapter, Mapping):
        raise RuntimeTraceIntegrityError("event payload adapter must be a mapping")
    if "semantic_gap_ids" not in adapter:
        return ()
    gaps = adapter["semantic_gap_ids"]
    if isinstance(gaps, (str, bytes)) or not isinstance(gaps, Sequence):
        raise RuntimeTraceIntegrityError("adapter semantic_gap_ids must be a sequence")
    values: list[str] = []
    for gap in gaps:
        if not isinstance(gap, str) or not gap.strip():
            raise RuntimeTraceIntegrityError("adapter semantic gaps must be non-empty strings")
        values.append(gap)
    if len(set(values)) != len(values):
        raise RuntimeTraceIntegrityError("one event contains duplicate semantic gap IDs")
    return tuple(values)


def validate_runtime_trace_document_v1(document: RuntimeTraceDocument) -> None:
    if not isinstance(document, RuntimeTraceDocument):
        raise RuntimeTraceIntegrityError("document must be RuntimeTraceDocument")
    if document.schema_name != "hsr_runtime_trace" or document.schema_version != "1.0":
        raise RuntimeTraceIntegrityError("document schema identity is not exact v1")
    records = document.records
    event_ids: set[str] = set()
    gaps: set[str] = set()
    previous: int | None = None
    for record in records:
        if record.sequence != record.event.sequence:
            raise RuntimeTraceIntegrityError("record sequence differs from event sequence")
        if record.event.event_id in event_ids:
            raise RuntimeTraceIntegrityError("duplicate RuntimeEvent event_id")
        event_ids.add(record.event.event_id)
        if previous is not None:
            if document.sequence_policy is TraceSequencePolicy.CONTIGUOUS and record.sequence != previous + 1:
                raise RuntimeTraceIntegrityError("CONTIGUOUS sequence integrity failed")
            if document.sequence_policy is TraceSequencePolicy.STRICTLY_INCREASING and record.sequence <= previous:
                raise RuntimeTraceIntegrityError("STRICTLY_INCREASING sequence integrity failed")
        previous = record.sequence
        if record.action_context is not None or record.attack_context is not None or record.hit_context is not None:
            raise RuntimeTraceIntegrityError("schema v1 contexts must remain None")
        if record.numeric_values or record.notes:
            raise RuntimeTraceIntegrityError("schema v1 numeric_values and notes must remain empty")
        gaps.update(_semantic_gaps(record.event))
    if document.record_count != len(records):
        raise RuntimeTraceIntegrityError("record_count integrity failed")
    expected_first = records[0].sequence if records else None
    expected_last = records[-1].sequence if records else None
    if document.first_sequence != expected_first or document.last_sequence != expected_last:
        raise RuntimeTraceIntegrityError("sequence boundary integrity failed")
    counts = dict(Counter(record.event.event_type.value for record in records))
    if dict(document.event_type_counts) != counts:
        raise RuntimeTraceIntegrityError("event_type_counts integrity failed")
    if document.semantic_gap_ids != tuple(sorted(gaps)):
        raise RuntimeTraceIntegrityError("semantic_gap_ids integrity failed")
