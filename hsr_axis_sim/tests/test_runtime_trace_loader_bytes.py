import json
from pathlib import Path

import pytest

from hsr_axis_sim.runtime_loaders import (
    DuplicateJsonKeyError,
    RuntimeTraceCanonicalityError,
    RuntimeTraceDigestMismatchError,
    RuntimeTraceEncodingError,
    RuntimeTraceJsonError,
    RuntimeTraceLoadConfig,
    RuntimeTraceSchemaError,
    RuntimeTraceSizeLimitError,
    TraceCanonicalForm,
    TraceCanonicalFormPolicy,
    TraceDigestPolicy,
    TraceDigestStatus,
    load_runtime_trace_bytes,
)


ROOT = Path(__file__).parents[2]
REF = json.loads((ROOT / "docs/runtime/research/REFERENCE_RUNTIME_TRACE_LOAD_VALIDATE_HSR_RUNTIME_ARCH_004.json").read_text())["valid_sample"]
COMPACT = REF["compact_json"].encode()
PRETTY = REF["pretty_json"].encode()


def config(form=TraceCanonicalFormPolicy.EITHER_CANONICAL, digest=TraceDigestPolicy.SKIP, expected=None, size=None):
    return RuntimeTraceLoadConfig(form, digest, expected, len(PRETTY) if size is None else size)


def test_compact_pretty_digest_policies_and_source_retention():
    compact = load_runtime_trace_bytes(COMPACT, config=config(digest=TraceDigestPolicy.REQUIRE_MATCH, expected=REF["compact_sha256"]))
    assert compact.canonical_form is TraceCanonicalForm.COMPACT
    assert compact.digest_status is TraceDigestStatus.MATCHED
    assert compact.artifact.payload_bytes is COMPACT
    pretty = load_runtime_trace_bytes(PRETTY, config=config(digest=TraceDigestPolicy.VERIFY_IF_PROVIDED))
    assert pretty.canonical_form is TraceCanonicalForm.PRETTY
    assert pretty.digest_status is TraceDigestStatus.NOT_PROVIDED
    skipped = load_runtime_trace_bytes(COMPACT, config=config())
    assert skipped.digest_status is TraceDigestStatus.SKIPPED
    with pytest.raises(RuntimeTraceDigestMismatchError):
        load_runtime_trace_bytes(COMPACT, config=config(digest=TraceDigestPolicy.REQUIRE_MATCH, expected="0" * 64))


def test_canonical_form_policies_and_noncanonical_rejection():
    load_runtime_trace_bytes(COMPACT, config=config(TraceCanonicalFormPolicy.COMPACT_ONLY))
    load_runtime_trace_bytes(PRETTY, config=config(TraceCanonicalFormPolicy.PRETTY_ONLY))
    with pytest.raises(RuntimeTraceCanonicalityError):
        load_runtime_trace_bytes(PRETTY, config=config(TraceCanonicalFormPolicy.COMPACT_ONLY))
    with pytest.raises(RuntimeTraceCanonicalityError):
        load_runtime_trace_bytes(COMPACT, config=config(TraceCanonicalFormPolicy.PRETTY_ONLY))
    noncanonical = json.dumps(json.loads(COMPACT), ensure_ascii=False).encode()
    with pytest.raises(RuntimeTraceCanonicalityError):
        load_runtime_trace_bytes(noncanonical, config=config(size=len(noncanonical)))


def test_bytes_encoding_json_duplicates_and_size_order():
    with pytest.raises(RuntimeTraceSchemaError):
        load_runtime_trace_bytes(bytearray(COMPACT), config=config())
    with pytest.raises(RuntimeTraceSizeLimitError):
        load_runtime_trace_bytes(COMPACT, config=config(size=len(COMPACT) - 1))
    load_runtime_trace_bytes(COMPACT, config=config(size=len(COMPACT)))
    with pytest.raises(RuntimeTraceEncodingError):
        load_runtime_trace_bytes(b"\xff", config=config(size=1))
    with pytest.raises(RuntimeTraceEncodingError):
        load_runtime_trace_bytes(b"\xef\xbb\xbf{}", config=config(size=5))
    for payload in (b"", b'{"x":NaN}', b'{"x":Infinity}', b'{"x":-Infinity}'):
        with pytest.raises(RuntimeTraceJsonError):
            load_runtime_trace_bytes(payload, config=config(size=max(1, len(payload))))
    with pytest.raises(DuplicateJsonKeyError):
        load_runtime_trace_bytes(b'{"x":1,"x":2}', config=config(size=13))


def test_exporter_round_trip_preserves_document_content():
    loaded = load_runtime_trace_bytes(COMPACT, config=config())
    document = loaded.artifact.document
    assert [record.event.event_id for record in document.records] == REF["expected"]["event_ids"]
    assert document.record_count == REF["expected"]["record_count"]
    assert all(record.action_context is record.attack_context is record.hit_context is None for record in document.records)
    assert all(not record.numeric_values for record in document.records)
