from dataclasses import FrozenInstanceError
import hashlib

import pytest

from hsr_axis_sim.runtime_exports import EmptyTracePolicy, TraceExportConfig, TraceSequencePolicy, build_runtime_trace_artifact, build_runtime_trace_document
from hsr_axis_sim.runtime_loaders import (
    RuntimeTraceLoadConfig,
    RuntimeTraceLoadConfigError,
    RuntimeTraceLoadResult,
    TraceCanonicalForm,
    TraceCanonicalFormPolicy,
    TraceDigestPolicy,
    TraceDigestStatus,
)


def artifact():
    document = build_runtime_trace_document([], config=TraceExportConfig("empty", TraceSequencePolicy.CONTIGUOUS, EmptyTracePolicy.ALLOW, {}))
    return build_runtime_trace_artifact(document, pretty=False)


def test_exact_enum_values_and_mandatory_config():
    assert [x.value for x in TraceCanonicalFormPolicy] == ["COMPACT_ONLY", "PRETTY_ONLY", "EITHER_CANONICAL"]
    assert [x.value for x in TraceCanonicalForm] == ["COMPACT", "PRETTY"]
    assert [x.value for x in TraceDigestPolicy] == ["REQUIRE_MATCH", "VERIFY_IF_PROVIDED", "SKIP"]
    assert [x.value for x in TraceDigestStatus] == ["MATCHED", "NOT_PROVIDED", "SKIPPED"]
    with pytest.raises(TypeError):
        RuntimeTraceLoadConfig()


@pytest.mark.parametrize("max_bytes", [True, 0, -1, 1.5])
def test_config_rejects_invalid_limits(max_bytes):
    with pytest.raises(RuntimeTraceLoadConfigError):
        RuntimeTraceLoadConfig(TraceCanonicalFormPolicy.EITHER_CANONICAL, TraceDigestPolicy.SKIP, None, max_bytes)


def test_digest_config_coherence_and_freezing():
    digest = "a" * 64
    valid = [
        RuntimeTraceLoadConfig(TraceCanonicalFormPolicy.COMPACT_ONLY, TraceDigestPolicy.REQUIRE_MATCH, digest, 1),
        RuntimeTraceLoadConfig(TraceCanonicalFormPolicy.PRETTY_ONLY, TraceDigestPolicy.VERIFY_IF_PROVIDED, None, 1),
        RuntimeTraceLoadConfig(TraceCanonicalFormPolicy.EITHER_CANONICAL, TraceDigestPolicy.VERIFY_IF_PROVIDED, digest, 1),
        RuntimeTraceLoadConfig(TraceCanonicalFormPolicy.EITHER_CANONICAL, TraceDigestPolicy.SKIP, None, 1),
    ]
    with pytest.raises(FrozenInstanceError):
        valid[0].max_bytes = 2
    for bad in ("A" * 64, "g" * 64, "a" * 63, ""):
        with pytest.raises(RuntimeTraceLoadConfigError):
            RuntimeTraceLoadConfig(TraceCanonicalFormPolicy.EITHER_CANONICAL, TraceDigestPolicy.VERIFY_IF_PROVIDED, bad, 1)
    with pytest.raises(RuntimeTraceLoadConfigError):
        RuntimeTraceLoadConfig(TraceCanonicalFormPolicy.EITHER_CANONICAL, TraceDigestPolicy.REQUIRE_MATCH, None, 1)
    with pytest.raises(RuntimeTraceLoadConfigError):
        RuntimeTraceLoadConfig(TraceCanonicalFormPolicy.EITHER_CANONICAL, TraceDigestPolicy.SKIP, digest, 1)
    with pytest.raises(RuntimeTraceLoadConfigError):
        RuntimeTraceLoadConfig("EITHER_CANONICAL", TraceDigestPolicy.SKIP, None, 1)


def test_result_coherence_and_frozen_state():
    value = artifact()
    result = RuntimeTraceLoadResult(value, TraceCanonicalForm.COMPACT, TraceDigestStatus.MATCHED, value.sha256, len(value.payload_bytes))
    with pytest.raises(FrozenInstanceError):
        result.source_size_bytes = 0
    with pytest.raises(RuntimeTraceLoadConfigError):
        RuntimeTraceLoadResult(value, TraceCanonicalForm.PRETTY, TraceDigestStatus.MATCHED, value.sha256, len(value.payload_bytes))
    with pytest.raises(RuntimeTraceLoadConfigError):
        RuntimeTraceLoadResult(value, TraceCanonicalForm.COMPACT, TraceDigestStatus.NOT_PROVIDED, value.sha256, len(value.payload_bytes))
    with pytest.raises(RuntimeTraceLoadConfigError):
        RuntimeTraceLoadResult(value, TraceCanonicalForm.COMPACT, TraceDigestStatus.SKIPPED, None, 0)
