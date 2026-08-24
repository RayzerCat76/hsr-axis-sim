from dataclasses import FrozenInstanceError

import pytest

from hsr_axis_sim.runtime_contracts import RuntimeEvent, RuntimeEventType
from hsr_axis_sim.runtime_exports import (
    EmptyTracePolicy,
    RuntimeTraceArtifact,
    RuntimeTraceDocument,
    RuntimeTraceExportSchemaError,
    TraceExportConfig,
    TraceSequencePolicy,
    build_runtime_trace_artifact,
    runtime_event_to_trace_record,
)


def event(sequence=1):
    return RuntimeEvent("event-1", RuntimeEventType.ACTION_START, sequence, "action", None, None, "actor", None, None, {})


def config(metadata=None):
    return TraceExportConfig("trace", TraceSequencePolicy.CONTIGUOUS, EmptyTracePolicy.ALLOW, {} if metadata is None else metadata)


def document():
    record = runtime_event_to_trace_record(event())
    return RuntimeTraceDocument("trace", TraceSequencePolicy.CONTIGUOUS, 1, 1, 1, {"ACTION_START": 1}, (), (record,), {})


def test_exact_policy_values_and_explicit_config_fields():
    assert [item.value for item in TraceSequencePolicy] == ["CONTIGUOUS", "STRICTLY_INCREASING"]
    assert [item.value for item in EmptyTracePolicy] == ["ALLOW", "REJECT"]
    with pytest.raises(TypeError):
        TraceExportConfig("trace")


def test_config_validation_freezing_and_defensive_metadata():
    source = {"nested": {"values": [1, 2]}}
    value = config(source)
    source["nested"]["values"][0] = 99
    assert value.metadata["nested"]["values"] == (1, 2)
    with pytest.raises(FrozenInstanceError):
        value.trace_id = "changed"
    with pytest.raises(TypeError):
        value.metadata["new"] = True
    with pytest.raises(RuntimeTraceExportSchemaError):
        TraceExportConfig("", TraceSequencePolicy.CONTIGUOUS, EmptyTracePolicy.ALLOW, {})
    with pytest.raises(RuntimeTraceExportSchemaError):
        TraceExportConfig("trace", "CONTIGUOUS", EmptyTracePolicy.ALLOW, {})
    with pytest.raises(RuntimeTraceExportSchemaError):
        TraceExportConfig("trace", TraceSequencePolicy.CONTIGUOUS, "ALLOW", {})


@pytest.mark.parametrize("bad", [object(), float("nan"), float("inf")])
def test_config_rejects_opaque_and_nonfinite_metadata(bad):
    with pytest.raises(RuntimeTraceExportSchemaError) as caught:
        config({"bad": bad})
    assert caught.value.__cause__ is not None


def test_document_fixed_schema_freezing_and_validation():
    value = document()
    assert value.schema_name == "hsr_runtime_trace"
    assert value.schema_version == "1.0"
    with pytest.raises(FrozenInstanceError):
        value.trace_id = "changed"
    with pytest.raises(TypeError):
        value.event_type_counts["X"] = 1
    record = value.records[0]
    base = ("trace", TraceSequencePolicy.CONTIGUOUS)
    with pytest.raises(RuntimeTraceExportSchemaError):
        RuntimeTraceDocument(*base, 0, 1, 1, {"ACTION_START": 1}, (), (record,), {})
    with pytest.raises(RuntimeTraceExportSchemaError):
        RuntimeTraceDocument(*base, 1, None, 1, {"ACTION_START": 1}, (), (record,), {})
    with pytest.raises(RuntimeTraceExportSchemaError):
        RuntimeTraceDocument(*base, 1, 1, 1, {"ACTION_END": 1}, (), (record,), {})


def test_artifact_is_frozen_and_validates_digest():
    value = build_runtime_trace_artifact(document(), pretty=False)
    with pytest.raises(FrozenInstanceError):
        value.pretty = True
    with pytest.raises(RuntimeTraceExportSchemaError):
        RuntimeTraceArtifact(value.document, False, value.payload_bytes, "0" * 64)
