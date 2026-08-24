from pathlib import Path

import pytest

from hsr_axis_sim.runtime_exports import (
    EmptyTracePolicy,
    RuntimeTraceFileError,
    TraceExportConfig,
    TraceSequencePolicy,
    build_runtime_trace_artifact,
    build_runtime_trace_document,
    write_runtime_trace_artifact,
)


def artifact(pretty=False):
    document = build_runtime_trace_document([], config=TraceExportConfig("empty", TraceSequencePolicy.CONTIGUOUS, EmptyTracePolicy.ALLOW, {}))
    return build_runtime_trace_artifact(document, pretty=pretty)


def test_write_new_file_exact_bytes_and_no_sidecars(tmp_path):
    value = artifact()
    target = tmp_path / "trace.json"
    returned = write_runtime_trace_artifact(value, target, overwrite=False)
    assert returned == target.resolve()
    assert target.read_bytes() == value.payload_bytes
    assert list(tmp_path.iterdir()) == [target]


def test_existing_target_requires_explicit_overwrite(tmp_path):
    target = tmp_path / "trace.json"
    target.write_bytes(b"old")
    with pytest.raises(RuntimeTraceFileError) as caught:
        write_runtime_trace_artifact(artifact(), target, overwrite=False)
    assert caught.value.__cause__ is not None
    value = artifact(pretty=True)
    write_runtime_trace_artifact(value, target, overwrite=True)
    assert target.read_bytes() == value.payload_bytes


def test_file_boundary_rejects_bad_inputs_and_paths(tmp_path):
    with pytest.raises(TypeError):
        write_runtime_trace_artifact(artifact(), tmp_path / "missing-overwrite")
    with pytest.raises(RuntimeTraceFileError):
        write_runtime_trace_artifact(object(), tmp_path / "bad", overwrite=False)
    with pytest.raises(RuntimeTraceFileError):
        write_runtime_trace_artifact(artifact(), tmp_path / "bad", overwrite=0)
    with pytest.raises(RuntimeTraceFileError):
        write_runtime_trace_artifact(artifact(), tmp_path / "missing" / "trace.json", overwrite=False)
    with pytest.raises(RuntimeTraceFileError):
        write_runtime_trace_artifact(artifact(), tmp_path, overwrite=True)
    assert list(tmp_path.iterdir()) == []
