"""Pure builders for runtime trace records, documents, and byte artifacts."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
import hashlib

from hsr_axis_sim.runtime_contracts import (
    RuntimeEvent,
    RuntimeTraceRecord,
    canonical_json_bytes,
)

from .enums import EmptyTracePolicy, TraceSequencePolicy
from .model import (
    DuplicateRuntimeEventIdError,
    EmptyRuntimeTraceError,
    RuntimeTraceArtifact,
    RuntimeTraceDocument,
    RuntimeTraceExportSchemaError,
    RuntimeTraceSequenceError,
    TraceExportConfig,
)


def runtime_event_to_trace_record(event: RuntimeEvent) -> RuntimeTraceRecord:
    """Project exactly one immutable event into exactly one empty-context record."""
    if not isinstance(event, RuntimeEvent):
        raise RuntimeTraceExportSchemaError("event must be RuntimeEvent")
    try:
        return RuntimeTraceRecord(
            sequence=event.sequence,
            event=event,
            action_context=None,
            attack_context=None,
            hit_context=None,
            numeric_values={},
            notes=(),
        )
    except (TypeError, ValueError) as exc:
        raise RuntimeTraceExportSchemaError(f"invalid RuntimeEvent projection: {exc}") from exc


def _event_semantic_gaps(event: RuntimeEvent) -> tuple[str, ...]:
    if "adapter" not in event.payload:
        return ()
    adapter = event.payload["adapter"]
    if not isinstance(adapter, Mapping):
        raise RuntimeTraceExportSchemaError("event payload adapter must be a mapping")
    if "semantic_gap_ids" not in adapter:
        return ()
    gap_ids = adapter["semantic_gap_ids"]
    if isinstance(gap_ids, (str, bytes)) or not isinstance(gap_ids, Sequence):
        raise RuntimeTraceExportSchemaError("semantic_gap_ids must be a sequence of strings")
    result: list[str] = []
    for gap_id in gap_ids:
        if not isinstance(gap_id, str) or not gap_id.strip():
            raise RuntimeTraceExportSchemaError("semantic_gap_ids must contain non-empty strings")
        result.append(gap_id)
    if len(set(result)) != len(result):
        raise RuntimeTraceExportSchemaError("one event cannot contain duplicate semantic gap IDs")
    return tuple(result)


def _validate_sequence(previous: int, current: int, policy: TraceSequencePolicy) -> None:
    if policy is TraceSequencePolicy.CONTIGUOUS:
        if current != previous + 1:
            raise RuntimeTraceSequenceError(
                f"CONTIGUOUS sequence requires {previous + 1}, got {current}"
            )
    elif current <= previous:
        raise RuntimeTraceSequenceError(
            f"STRICTLY_INCREASING sequence requires a value greater than {previous}, got {current}"
        )


def build_runtime_trace_document(
    events: Iterable[RuntimeEvent],
    *,
    config: TraceExportConfig,
) -> RuntimeTraceDocument:
    """Consume one explicit event iterable once and preserve its ordering."""
    if not isinstance(config, TraceExportConfig):
        raise RuntimeTraceExportSchemaError("config must be TraceExportConfig")

    records: list[RuntimeTraceRecord] = []
    event_ids: set[str] = set()
    semantic_gaps: set[str] = set()
    previous_sequence: int | None = None
    try:
        iterator = iter(events)
    except TypeError as exc:
        raise RuntimeTraceExportSchemaError("events must be iterable") from exc

    while True:
        try:
            event = next(iterator)
        except StopIteration:
            break
        except Exception as exc:
            raise RuntimeTraceExportSchemaError("event iterable failed during consumption") from exc
        if not isinstance(event, RuntimeEvent):
            raise RuntimeTraceExportSchemaError("events must contain only RuntimeEvent values")
        if event.event_id in event_ids:
            raise DuplicateRuntimeEventIdError(f"duplicate RuntimeEvent event_id: {event.event_id}")
        if previous_sequence is not None:
            _validate_sequence(previous_sequence, event.sequence, config.sequence_policy)
        event_ids.add(event.event_id)
        previous_sequence = event.sequence
        semantic_gaps.update(_event_semantic_gaps(event))
        records.append(runtime_event_to_trace_record(event))

    if not records and config.empty_trace_policy is EmptyTracePolicy.REJECT:
        raise EmptyRuntimeTraceError("empty runtime trace rejected by policy")

    record_tuple = tuple(records)
    counts = Counter(record.event.event_type.value for record in record_tuple)
    return RuntimeTraceDocument(
        trace_id=config.trace_id,
        sequence_policy=config.sequence_policy,
        record_count=len(record_tuple),
        first_sequence=record_tuple[0].sequence if record_tuple else None,
        last_sequence=record_tuple[-1].sequence if record_tuple else None,
        event_type_counts=dict(counts),
        semantic_gap_ids=tuple(sorted(semantic_gaps)),
        records=record_tuple,
        metadata=config.metadata,
    )


def build_runtime_trace_artifact(
    document: RuntimeTraceDocument,
    *,
    pretty: bool,
) -> RuntimeTraceArtifact:
    """Serialize one document and hash the exact exported UTF-8 bytes."""
    if not isinstance(document, RuntimeTraceDocument):
        raise RuntimeTraceExportSchemaError("document must be RuntimeTraceDocument")
    if not isinstance(pretty, bool):
        raise RuntimeTraceExportSchemaError("pretty must be a bool")
    try:
        payload = canonical_json_bytes(document, pretty=pretty)
    except (TypeError, ValueError) as exc:
        raise RuntimeTraceExportSchemaError(f"runtime trace serialization failed: {exc}") from exc
    return RuntimeTraceArtifact(
        document=document,
        pretty=pretty,
        payload_bytes=payload,
        sha256=hashlib.sha256(payload).hexdigest(),
    )
