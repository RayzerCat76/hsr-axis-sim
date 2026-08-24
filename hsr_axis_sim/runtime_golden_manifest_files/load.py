"""Explicit base-bounded file boundary for strict Golden Replay manifests."""

from __future__ import annotations

from pathlib import Path, PurePosixPath

from hsr_axis_sim.runtime_contracts.serialization import canonical_json_dumps
from hsr_axis_sim.runtime_golden_manifests import load_golden_replay_manifest_bytes

from .model import (
    GoldenReplayManifestFileInputError,
    GoldenReplayManifestFileLoadResult,
    GoldenReplayManifestFileReadError,
    GoldenReplayManifestFileSpec,
)


def _resolve_base_directory(value: str | Path) -> Path:
    try:
        base = Path(value).expanduser().resolve(strict=True)
    except (TypeError, ValueError, OSError) as exc:
        raise GoldenReplayManifestFileReadError(
            f"invalid Golden Replay manifest base directory: {exc}"
        ) from exc
    if not base.is_dir():
        raise GoldenReplayManifestFileReadError(
            f"Golden Replay manifest base path is not a directory: {base}"
        )
    return base


def _resolve_manifest_file(base: Path, relative_path: str) -> Path:
    candidate = base.joinpath(*PurePosixPath(relative_path).parts)
    try:
        resolved = candidate.resolve(strict=True)
    except (ValueError, OSError) as exc:
        raise GoldenReplayManifestFileReadError(
            f"Golden Replay manifest file cannot be resolved: {candidate}: {exc}"
        ) from exc
    try:
        resolved.relative_to(base)
    except ValueError as exc:
        raise GoldenReplayManifestFileReadError(
            "Golden Replay manifest file escapes base directory after resolution: "
            f"{resolved}"
        ) from exc
    if not resolved.is_file():
        raise GoldenReplayManifestFileReadError(
            f"Golden Replay manifest path is not a regular file: {resolved}"
        )
    return resolved


def _read_bounded(path: Path, *, max_bytes: int) -> bytes:
    try:
        with path.open("rb") as handle:
            return handle.read(max_bytes + 1)
    except OSError as exc:
        raise GoldenReplayManifestFileReadError(
            f"failed to read Golden Replay manifest file {path}: {exc}"
        ) from exc


def load_golden_replay_manifest_file(
    spec: GoldenReplayManifestFileSpec,
    *,
    base_directory: str | Path,
) -> GoldenReplayManifestFileLoadResult:
    """Read one explicit manifest file and delegate byte semantics to HSR-AXIS-001E."""

    if not isinstance(spec, GoldenReplayManifestFileSpec):
        raise GoldenReplayManifestFileInputError(
            "spec must be GoldenReplayManifestFileSpec"
        )

    base = _resolve_base_directory(base_directory)
    manifest_path = _resolve_manifest_file(base, spec.manifest_relative_path)
    payload_bytes = _read_bounded(manifest_path, max_bytes=spec.max_bytes)
    artifact = load_golden_replay_manifest_bytes(
        payload_bytes,
        max_bytes=spec.max_bytes,
        expected_sha256=spec.expected_sha256,
    )
    return GoldenReplayManifestFileLoadResult(
        spec=spec,
        base_directory=str(base),
        manifest_path=str(manifest_path),
        artifact=artifact,
    )


def render_golden_replay_manifest_file_text(
    result: GoldenReplayManifestFileLoadResult,
) -> str:
    """Render deterministic manifest-file provenance without executing the batch."""

    if not isinstance(result, GoldenReplayManifestFileLoadResult):
        raise GoldenReplayManifestFileInputError(
            "result must be GoldenReplayManifestFileLoadResult"
        )
    lines = [
        "GOLDEN_REPLAY_MANIFEST_FILE_LOADED",
        f"base_directory={canonical_json_dumps(result.base_directory, pretty=False)}",
        f"manifest_path={canonical_json_dumps(result.manifest_path, pretty=False)}",
        f"manifest_sha256={result.artifact.sha256}",
        f"manifest_byte_count={result.artifact.byte_count}",
        f"batch_id={canonical_json_dumps(result.artifact.plan.batch_id, pretty=False)}",
        f"case_count={result.artifact.plan.case_count}",
    ]
    return "\n".join(lines) + "\n"
