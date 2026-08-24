"""Explicit read-only file boundary for runtime trace loading."""

from __future__ import annotations

from pathlib import Path

from .model import (
    RuntimeTraceLoadConfig,
    RuntimeTraceLoadConfigError,
    RuntimeTraceLoadResult,
    RuntimeTraceReadError,
)
from .trace_load import load_runtime_trace_bytes


def read_runtime_trace_file(
    path: str | Path,
    *,
    config: RuntimeTraceLoadConfig,
) -> RuntimeTraceLoadResult:
    if not isinstance(config, RuntimeTraceLoadConfig):
        raise RuntimeTraceLoadConfigError("config must be RuntimeTraceLoadConfig")
    try:
        target = Path(path).expanduser().resolve(strict=False)
    except (TypeError, ValueError, OSError) as exc:
        raise RuntimeTraceReadError(f"invalid runtime trace path: {exc}") from exc
    if not target.exists():
        raise RuntimeTraceReadError(f"runtime trace file does not exist: {target}")
    if not target.is_file():
        raise RuntimeTraceReadError(f"runtime trace path is not a regular file: {target}")
    try:
        with target.open("rb") as handle:
            payload = handle.read(config.max_bytes + 1)
    except OSError as exc:
        raise RuntimeTraceReadError(f"failed to read runtime trace file: {exc}") from exc
    return load_runtime_trace_bytes(payload, config=config)
