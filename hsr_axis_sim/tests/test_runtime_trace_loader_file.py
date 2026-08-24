import json
from pathlib import Path

import pytest

from hsr_axis_sim.runtime_loaders import (
    RuntimeTraceLoadConfig,
    RuntimeTraceLoadConfigError,
    RuntimeTraceReadError,
    RuntimeTraceSizeLimitError,
    TraceCanonicalForm,
    TraceCanonicalFormPolicy,
    TraceDigestPolicy,
    read_runtime_trace_file,
)


ROOT = Path(__file__).parents[2]
REF = json.loads((ROOT / "docs/runtime/research/REFERENCE_RUNTIME_TRACE_LOAD_VALIDATE_HSR_RUNTIME_ARCH_004.json").read_text())["valid_sample"]


def config(size):
    return RuntimeTraceLoadConfig(TraceCanonicalFormPolicy.EITHER_CANONICAL, TraceDigestPolicy.SKIP, None, size)


@pytest.mark.parametrize(("key", "form"), [("compact_json", TraceCanonicalForm.COMPACT), ("pretty_json", TraceCanonicalForm.PRETTY)])
def test_read_valid_file_without_mutation_or_sidecar(tmp_path, key, form):
    payload = REF[key].encode()
    target = tmp_path / "trace.json"
    target.write_bytes(payload)
    result = read_runtime_trace_file(target, config=config(len(payload)))
    assert result.canonical_form is form
    assert target.read_bytes() == payload
    assert list(tmp_path.iterdir()) == [target]


def test_file_errors_size_and_config_before_access(tmp_path):
    with pytest.raises(RuntimeTraceLoadConfigError):
        read_runtime_trace_file(tmp_path / "missing", config=object())
    with pytest.raises(RuntimeTraceReadError):
        read_runtime_trace_file(tmp_path / "missing", config=config(10))
    with pytest.raises(RuntimeTraceReadError):
        read_runtime_trace_file(tmp_path, config=config(10))
    target = tmp_path / "trace.json"
    target.write_bytes(REF["compact_json"].encode())
    with pytest.raises(RuntimeTraceSizeLimitError):
        read_runtime_trace_file(target, config=config(1))
    assert list(tmp_path.iterdir()) == [target]
