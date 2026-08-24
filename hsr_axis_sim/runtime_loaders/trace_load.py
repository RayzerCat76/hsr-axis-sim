"""Ordered strict loading of canonical runtime trace artifact bytes."""

from __future__ import annotations

import hashlib

from hsr_axis_sim.runtime_contracts import canonical_json_bytes
from hsr_axis_sim.runtime_exports import RuntimeTraceArtifact
from hsr_axis_sim.runtime_exports.model import RuntimeTraceExportSchemaError

from .enums import (
    TraceCanonicalForm,
    TraceCanonicalFormPolicy,
    TraceDigestPolicy,
    TraceDigestStatus,
)
from .json_decode import decode_runtime_trace_json
from .model import (
    RuntimeTraceCanonicalityError,
    RuntimeTraceDigestMismatchError,
    RuntimeTraceEncodingError,
    RuntimeTraceLoadConfig,
    RuntimeTraceLoadConfigError,
    RuntimeTraceLoadResult,
    RuntimeTraceSchemaError,
    RuntimeTraceSizeLimitError,
)
from .validation import reconstruct_runtime_trace_document_v1, validate_runtime_trace_document_v1


def _digest_status(digest: str, config: RuntimeTraceLoadConfig) -> TraceDigestStatus:
    if config.digest_policy is TraceDigestPolicy.SKIP:
        return TraceDigestStatus.SKIPPED
    if config.expected_sha256 is None:
        return TraceDigestStatus.NOT_PROVIDED
    if digest != config.expected_sha256:
        raise RuntimeTraceDigestMismatchError(
            f"runtime trace SHA-256 mismatch: expected {config.expected_sha256}, got {digest}"
        )
    return TraceDigestStatus.MATCHED


def load_runtime_trace_bytes(
    payload_bytes: bytes,
    *,
    config: RuntimeTraceLoadConfig,
) -> RuntimeTraceLoadResult:
    if not isinstance(config, RuntimeTraceLoadConfig):
        raise RuntimeTraceLoadConfigError("config must be RuntimeTraceLoadConfig")
    if type(payload_bytes) is not bytes:
        raise RuntimeTraceSchemaError("payload_bytes must be exact bytes")
    if len(payload_bytes) > config.max_bytes:
        raise RuntimeTraceSizeLimitError(
            f"runtime trace is {len(payload_bytes)} bytes; limit is {config.max_bytes}"
        )
    digest = hashlib.sha256(payload_bytes).hexdigest()
    digest_status = _digest_status(digest, config)
    if payload_bytes.startswith(b"\xef\xbb\xbf"):
        raise RuntimeTraceEncodingError("UTF-8 BOM is forbidden")
    try:
        text = payload_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise RuntimeTraceEncodingError(f"invalid UTF-8: {exc}") from exc
    data = decode_runtime_trace_json(text)
    document = reconstruct_runtime_trace_document_v1(data)
    validate_runtime_trace_document_v1(document)
    try:
        compact = canonical_json_bytes(document, pretty=False)
        pretty = canonical_json_bytes(document, pretty=True)
    except (TypeError, ValueError) as exc:
        raise RuntimeTraceCanonicalityError(f"canonical serialization failed: {exc}") from exc
    if payload_bytes == compact:
        canonical_form = TraceCanonicalForm.COMPACT
    elif payload_bytes == pretty:
        canonical_form = TraceCanonicalForm.PRETTY
    else:
        raise RuntimeTraceCanonicalityError("source bytes are not an exact canonical trace form")
    if config.canonical_form_policy is TraceCanonicalFormPolicy.COMPACT_ONLY and canonical_form is not TraceCanonicalForm.COMPACT:
        raise RuntimeTraceCanonicalityError("COMPACT_ONLY rejects pretty canonical input")
    if config.canonical_form_policy is TraceCanonicalFormPolicy.PRETTY_ONLY and canonical_form is not TraceCanonicalForm.PRETTY:
        raise RuntimeTraceCanonicalityError("PRETTY_ONLY rejects compact canonical input")
    try:
        artifact = RuntimeTraceArtifact(document, canonical_form is TraceCanonicalForm.PRETTY, payload_bytes, digest)
    except RuntimeTraceExportSchemaError as exc:
        raise RuntimeTraceSchemaError(f"artifact reconstruction failed: {exc}") from exc
    return RuntimeTraceLoadResult(
        artifact=artifact,
        canonical_form=canonical_form,
        digest_status=digest_status,
        expected_sha256=config.expected_sha256,
        source_size_bytes=len(payload_bytes),
    )
