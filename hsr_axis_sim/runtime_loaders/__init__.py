"""Strict canonical loader and integrity validator for runtime trace v1."""

from .enums import (
    TraceCanonicalForm,
    TraceCanonicalFormPolicy,
    TraceDigestPolicy,
    TraceDigestStatus,
)
from .files import read_runtime_trace_file
from .json_decode import decode_runtime_trace_json
from .model import (
    DuplicateJsonKeyError,
    RuntimeTraceCanonicalityError,
    RuntimeTraceDigestMismatchError,
    RuntimeTraceEncodingError,
    RuntimeTraceIntegrityError,
    RuntimeTraceJsonError,
    RuntimeTraceLoadConfig,
    RuntimeTraceLoadConfigError,
    RuntimeTraceLoadError,
    RuntimeTraceLoadResult,
    RuntimeTraceReadError,
    RuntimeTraceSchemaError,
    RuntimeTraceSizeLimitError,
    UnsupportedRuntimeTraceVersionError,
)
from .trace_load import load_runtime_trace_bytes
from .validation import reconstruct_runtime_trace_document_v1, validate_runtime_trace_document_v1

__all__ = [
    "DuplicateJsonKeyError",
    "RuntimeTraceCanonicalityError",
    "RuntimeTraceDigestMismatchError",
    "RuntimeTraceEncodingError",
    "RuntimeTraceIntegrityError",
    "RuntimeTraceJsonError",
    "RuntimeTraceLoadConfig",
    "RuntimeTraceLoadConfigError",
    "RuntimeTraceLoadError",
    "RuntimeTraceLoadResult",
    "RuntimeTraceReadError",
    "RuntimeTraceSchemaError",
    "RuntimeTraceSizeLimitError",
    "TraceCanonicalForm",
    "TraceCanonicalFormPolicy",
    "TraceDigestPolicy",
    "TraceDigestStatus",
    "UnsupportedRuntimeTraceVersionError",
    "decode_runtime_trace_json",
    "load_runtime_trace_bytes",
    "read_runtime_trace_file",
    "reconstruct_runtime_trace_document_v1",
    "validate_runtime_trace_document_v1",
]
