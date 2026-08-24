"""Explicit filesystem boundary for runtime trace artifacts."""

from __future__ import annotations

from pathlib import Path

from .model import RuntimeTraceArtifact, RuntimeTraceFileError


def write_runtime_trace_artifact(
    artifact: RuntimeTraceArtifact,
    path: str | Path,
    *,
    overwrite: bool,
) -> Path:
    """Write exact artifact bytes only when explicitly called."""
    if not isinstance(artifact, RuntimeTraceArtifact):
        raise RuntimeTraceFileError("artifact must be RuntimeTraceArtifact")
    if not isinstance(overwrite, bool):
        raise RuntimeTraceFileError("overwrite must be a bool")
    try:
        target = Path(path).expanduser().resolve(strict=False)
    except (TypeError, ValueError, OSError) as exc:
        raise RuntimeTraceFileError(f"invalid target path: {exc}") from exc
    if target.exists() and target.is_dir():
        raise RuntimeTraceFileError(f"target path is a directory: {target}")
    if not target.parent.exists() or not target.parent.is_dir():
        raise RuntimeTraceFileError(f"parent directory does not exist: {target.parent}")
    mode = "wb" if overwrite else "xb"
    try:
        with target.open(mode) as handle:
            handle.write(artifact.payload_bytes)
    except (OSError, ValueError) as exc:
        raise RuntimeTraceFileError(f"failed to write runtime trace artifact: {exc}") from exc
    return target
