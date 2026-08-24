"""Explicit file boundary for one reviewed Golden Replay case."""

from __future__ import annotations

from pathlib import Path, PurePosixPath

from hsr_axis_sim.runtime_contracts.serialization import canonical_json_dumps
from hsr_axis_sim.runtime_golden_replays import (
    render_golden_replay_validation_text,
    validate_golden_replay_bytes,
)

from .model import (
    GoldenReplayFileCase,
    GoldenReplayFileCaseInputError,
    GoldenReplayFileReadError,
    GoldenReplayFileRunResult,
)


def _resolve_base_directory(value: str | Path) -> Path:
    try:
        base = Path(value).expanduser().resolve(strict=True)
    except (TypeError, ValueError, OSError) as exc:
        raise GoldenReplayFileReadError(f"invalid Golden Replay base directory: {exc}") from exc
    if not base.is_dir():
        raise GoldenReplayFileReadError(f"Golden Replay base path is not a directory: {base}")
    return base


def _resolve_case_file(base: Path, relative_path: str) -> Path:
    candidate = base.joinpath(*PurePosixPath(relative_path).parts)
    try:
        resolved = candidate.resolve(strict=True)
    except (ValueError, OSError) as exc:
        raise GoldenReplayFileReadError(f"Golden Replay file cannot be resolved: {candidate}: {exc}") from exc
    try:
        resolved.relative_to(base)
    except ValueError as exc:
        raise GoldenReplayFileReadError(
            f"Golden Replay file escapes base directory after resolution: {resolved}"
        ) from exc
    if not resolved.is_file():
        raise GoldenReplayFileReadError(f"Golden Replay path is not a regular file: {resolved}")
    return resolved


def _read_bounded(path: Path, *, max_bytes: int) -> bytes:
    try:
        with path.open("rb") as handle:
            return handle.read(max_bytes + 1)
    except OSError as exc:
        raise GoldenReplayFileReadError(f"failed to read Golden Replay file {path}: {exc}") from exc


def run_golden_replay_file_case(
    case: GoldenReplayFileCase,
    *,
    base_directory: str | Path,
) -> GoldenReplayFileRunResult:
    """Read one explicit expected/actual file pair and delegate validation to 001B."""

    if not isinstance(case, GoldenReplayFileCase):
        raise GoldenReplayFileCaseInputError("case must be GoldenReplayFileCase")

    base = _resolve_base_directory(base_directory)
    expected_path = _resolve_case_file(base, case.expected_relative_path)
    actual_path = _resolve_case_file(base, case.actual_relative_path)
    expected_bytes = _read_bounded(expected_path, max_bytes=case.validation_config.max_bytes)
    actual_bytes = _read_bounded(actual_path, max_bytes=case.validation_config.max_bytes)

    validation = validate_golden_replay_bytes(
        expected_bytes,
        actual_bytes,
        config=case.validation_config,
    )
    return GoldenReplayFileRunResult(
        case=case,
        base_directory=str(base),
        expected_path=str(expected_path),
        actual_path=str(actual_path),
        validation=validation,
    )


def render_golden_replay_file_case_text(result: GoldenReplayFileRunResult) -> str:
    """Render stable path provenance followed by the accepted 001B report."""

    if not isinstance(result, GoldenReplayFileRunResult):
        raise GoldenReplayFileCaseInputError("result must be GoldenReplayFileRunResult")
    lines = [
        "GOLDEN_REPLAY_FILE_CASE_PASS" if result.matches else "GOLDEN_REPLAY_FILE_CASE_FAIL",
        f"base_directory={canonical_json_dumps(result.base_directory, pretty=False)}",
        f"expected_path={canonical_json_dumps(result.expected_path, pretty=False)}",
        f"actual_path={canonical_json_dumps(result.actual_path, pretty=False)}",
        "GOLDEN_REPLAY_VALIDATION",
        render_golden_replay_validation_text(result.validation).rstrip("\n"),
    ]
    return "\n".join(lines) + "\n"
