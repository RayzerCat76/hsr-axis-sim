import json
from pathlib import Path

import pytest

from hsr_axis_sim.runtime_loaders import (
    RuntimeTraceIntegrityError,
    RuntimeTraceSchemaError,
    UnsupportedRuntimeTraceVersionError,
    reconstruct_runtime_trace_document_v1,
    validate_runtime_trace_document_v1,
)


ROOT = Path(__file__).parents[2]


def sample():
    ref = json.loads((ROOT / "docs/runtime/research/REFERENCE_RUNTIME_TRACE_LOAD_VALIDATE_HSR_RUNTIME_ARCH_004.json").read_text())
    return json.loads(ref["valid_sample"]["compact_json"])


def test_valid_reconstruction_and_exact_field_sets():
    document = reconstruct_runtime_trace_document_v1(sample())
    validate_runtime_trace_document_v1(document)
    assert document.record_count == 2
    for field in ("metadata", "schema_name"):
        value = sample(); value.pop(field)
        with pytest.raises(RuntimeTraceSchemaError):
            reconstruct_runtime_trace_document_v1(value)
    value = sample(); value["extra"] = True
    with pytest.raises(RuntimeTraceSchemaError):
        reconstruct_runtime_trace_document_v1(value)
    for container in ("records",):
        value = sample(); value[container][0]["extra"] = True
        with pytest.raises(RuntimeTraceSchemaError):
            reconstruct_runtime_trace_document_v1(value)
    value = sample(); value["records"][0]["event"]["extra"] = True
    with pytest.raises(RuntimeTraceSchemaError):
        reconstruct_runtime_trace_document_v1(value)


def test_schema_identity_enums_and_primitives_are_strict():
    cases = []
    value = sample(); value["schema_name"] = "other"; cases.append(value)
    value = sample(); value["sequence_policy"] = "FUTURE"; cases.append(value)
    value = sample(); value["records"][0]["event"]["event_type"] = "FUTURE"; cases.append(value)
    value = sample(); value["record_count"] = True; cases.append(value)
    value = sample(); value["records"][0]["sequence"] = -1; cases.append(value)
    value = sample(); value["records"][0]["action_context"] = {}; cases.append(value)
    value = sample(); value["records"][0]["numeric_values"] = {"x": 1}; cases.append(value)
    value = sample(); value["records"][0]["notes"] = ["x"]; cases.append(value)
    for case in cases:
        with pytest.raises(RuntimeTraceSchemaError):
            reconstruct_runtime_trace_document_v1(case)
    value = sample(); value["schema_version"] = "2.0"
    with pytest.raises(UnsupportedRuntimeTraceVersionError):
        reconstruct_runtime_trace_document_v1(value)


def test_integrity_rejects_sequences_ids_counts_boundaries_and_gaps():
    mutations = [
        ("record_sequence", lambda d: object.__setattr__(d.records[0], "sequence", 99)),
        ("duplicate_id", lambda d: object.__setattr__(d.records[1].event, "event_id", d.records[0].event.event_id)),
        ("sequence_gap", lambda d: object.__setattr__(d.records[1], "sequence", 13)),
        ("record_count", lambda d: object.__setattr__(d, "record_count", 3)),
        ("first", lambda d: object.__setattr__(d, "first_sequence", 9)),
        ("counts", lambda d: object.__setattr__(d, "event_type_counts", {"ACTION_START": 2})),
        ("gaps", lambda d: object.__setattr__(d, "semantic_gap_ids", ())),
    ]
    for _, mutate in mutations:
        document = reconstruct_runtime_trace_document_v1(sample())
        mutate(document)
        with pytest.raises(RuntimeTraceIntegrityError):
            validate_runtime_trace_document_v1(document)


def test_semantic_gap_metadata_is_validated_without_type_inference():
    no_gap = sample()
    no_gap["records"][1]["event"]["payload"] = {}
    no_gap["semantic_gap_ids"] = []
    validate_runtime_trace_document_v1(reconstruct_runtime_trace_document_v1(no_gap))
    bad = sample(); bad["records"][1]["event"]["payload"]["adapter"] = "bad"
    with pytest.raises(RuntimeTraceIntegrityError):
        validate_runtime_trace_document_v1(reconstruct_runtime_trace_document_v1(bad))
    bad = sample(); bad["records"][1]["event"]["payload"]["adapter"]["semantic_gap_ids"] = ["gap", "gap"]
    with pytest.raises(RuntimeTraceIntegrityError):
        validate_runtime_trace_document_v1(reconstruct_runtime_trace_document_v1(bad))
