"""Immutable models and controlled errors for runtime trace export."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
import hashlib
from types import MappingProxyType
from typing import Any, Mapping

from hsr_axis_sim.runtime_contracts import RuntimeTraceRecord
from hsr_axis_sim.runtime_contracts.serialization import freeze_mapping

from .enums import EmptyTracePolicy, TraceSequencePolicy


class RuntimeTraceExportError(RuntimeError):
    """Base class for all controlled trace-export failures."""


class RuntimeTraceExportSchemaError(RuntimeTraceExportError):
    """Raised when trace-export input violates the export schema."""


class RuntimeTraceSequenceError(RuntimeTraceExportError):
    """Raised when event sequences violate the selected policy."""


class DuplicateRuntimeEventIdError(RuntimeTraceExportError):
    """Raised when one document contains a repeated runtime event ID."""


class EmptyRuntimeTraceError(RuntimeTraceExportError):
    """Raised when an empty trace is explicitly rejected."""


class RuntimeTraceFileError(RuntimeTraceExportError):
    """Raised when an explicit trace artifact write fails."""


def _require_non_empty(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RuntimeTraceExportSchemaError(f"{name} must be a non-empty string")
    return value


def _freeze_metadata(value: object, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise RuntimeTraceExportSchemaError(f"{name} must be a mapping")
    try:
        return freeze_mapping(value, path=name)
    except (TypeError, ValueError) as exc:
        raise RuntimeTraceExportSchemaError(f"invalid {name}: {exc}") from exc


@dataclass(frozen=True)
class TraceExportConfig:
    trace_id: str
    sequence_policy: TraceSequencePolicy
    empty_trace_policy: EmptyTracePolicy
    metadata: Mapping[str, Any]

    def __post_init__(self) -> None:
        _require_non_empty(self.trace_id, "trace_id")
        if not isinstance(self.sequence_policy, TraceSequencePolicy):
            raise RuntimeTraceExportSchemaError("sequence_policy has an invalid type")
        if not isinstance(self.empty_trace_policy, EmptyTracePolicy):
            raise RuntimeTraceExportSchemaError("empty_trace_policy has an invalid type")
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata, "metadata"))


@dataclass(frozen=True)
class RuntimeTraceDocument:
    trace_id: str
    sequence_policy: TraceSequencePolicy
    record_count: int
    first_sequence: int | None
    last_sequence: int | None
    event_type_counts: Mapping[str, int]
    semantic_gap_ids: tuple[str, ...]
    records: tuple[RuntimeTraceRecord, ...]
    metadata: Mapping[str, Any]
    schema_name: str = field(default="hsr_runtime_trace", init=False)
    schema_version: str = field(default="1.0", init=False)

    def __post_init__(self) -> None:
        _require_non_empty(self.trace_id, "trace_id")
        if not isinstance(self.sequence_policy, TraceSequencePolicy):
            raise RuntimeTraceExportSchemaError("sequence_policy has an invalid type")
        if not isinstance(self.records, tuple):
            raise RuntimeTraceExportSchemaError("records must be a tuple")
        if any(not isinstance(record, RuntimeTraceRecord) for record in self.records):
            raise RuntimeTraceExportSchemaError("records must contain RuntimeTraceRecord values")
        if not isinstance(self.record_count, int) or isinstance(self.record_count, bool):
            raise RuntimeTraceExportSchemaError("record_count must be an integer")
        if self.record_count != len(self.records):
            raise RuntimeTraceExportSchemaError("record_count must equal len(records)")

        expected_first = self.records[0].sequence if self.records else None
        expected_last = self.records[-1].sequence if self.records else None
        if self.first_sequence != expected_first or self.last_sequence != expected_last:
            raise RuntimeTraceExportSchemaError("sequence boundaries do not match records")

        if not isinstance(self.event_type_counts, Mapping):
            raise RuntimeTraceExportSchemaError("event_type_counts must be a mapping")
        counts: dict[str, int] = {}
        for key, value in self.event_type_counts.items():
            _require_non_empty(key, "event_type_counts key")
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise RuntimeTraceExportSchemaError("event_type_counts values must be non-negative integers")
            counts[key] = value
        expected_counts = Counter(record.event.event_type.value for record in self.records)
        if counts != dict(expected_counts):
            raise RuntimeTraceExportSchemaError("event_type_counts do not exactly match records")
        object.__setattr__(self, "event_type_counts", MappingProxyType(dict(sorted(counts.items()))))

        if not isinstance(self.semantic_gap_ids, tuple):
            raise RuntimeTraceExportSchemaError("semantic_gap_ids must be a tuple")
        for gap_id in self.semantic_gap_ids:
            _require_non_empty(gap_id, "semantic gap ID")
        if len(set(self.semantic_gap_ids)) != len(self.semantic_gap_ids):
            raise RuntimeTraceExportSchemaError("semantic_gap_ids must be unique")
        object.__setattr__(self, "semantic_gap_ids", tuple(sorted(self.semantic_gap_ids)))
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata, "metadata"))


@dataclass(frozen=True)
class RuntimeTraceArtifact:
    document: RuntimeTraceDocument
    pretty: bool
    payload_bytes: bytes
    sha256: str

    def __post_init__(self) -> None:
        if not isinstance(self.document, RuntimeTraceDocument):
            raise RuntimeTraceExportSchemaError("document must be RuntimeTraceDocument")
        if not isinstance(self.pretty, bool):
            raise RuntimeTraceExportSchemaError("pretty must be a bool")
        if not isinstance(self.payload_bytes, bytes):
            raise RuntimeTraceExportSchemaError("payload_bytes must be bytes")
        if not isinstance(self.sha256, str):
            raise RuntimeTraceExportSchemaError("sha256 must be a string")
        expected = hashlib.sha256(self.payload_bytes).hexdigest()
        if self.sha256 != expected:
            raise RuntimeTraceExportSchemaError("sha256 does not match payload_bytes")
