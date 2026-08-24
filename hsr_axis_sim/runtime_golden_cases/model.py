"""Immutable file-backed Golden Replay case models and controlled failures."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from hsr_axis_sim.runtime_golden_replays import (
    GoldenReplayValidationConfig,
    GoldenReplayValidationResult,
)


class GoldenReplayFileCaseError(RuntimeError):
    """Base class for controlled file-case failures."""


class GoldenReplayFileCaseInputError(GoldenReplayFileCaseError):
    """Raised when file-case configuration or result invariants are invalid."""


class GoldenReplayFileReadError(GoldenReplayFileCaseError):
    """Raised when an explicit Golden Replay case file cannot be read safely."""


def _canonical_relative_path(value: object, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise GoldenReplayFileCaseInputError(f"{name} must be a non-empty string")
    if "\\" in value:
        raise GoldenReplayFileCaseInputError(f"{name} must use POSIX '/' separators")
    path = PurePosixPath(value)
    if path.is_absolute():
        raise GoldenReplayFileCaseInputError(f"{name} must be relative")
    if any(part == ".." for part in path.parts):
        raise GoldenReplayFileCaseInputError(f"{name} cannot contain '..'")
    canonical = path.as_posix()
    if canonical in {"", "."} or canonical != value:
        raise GoldenReplayFileCaseInputError(f"{name} must be a canonical relative POSIX path")
    return canonical


@dataclass(frozen=True)
class GoldenReplayFileCase:
    validation_config: GoldenReplayValidationConfig
    expected_relative_path: str
    actual_relative_path: str

    def __post_init__(self) -> None:
        if not isinstance(self.validation_config, GoldenReplayValidationConfig):
            raise GoldenReplayFileCaseInputError("validation_config has an invalid type")
        object.__setattr__(
            self,
            "expected_relative_path",
            _canonical_relative_path(self.expected_relative_path, "expected_relative_path"),
        )
        object.__setattr__(
            self,
            "actual_relative_path",
            _canonical_relative_path(self.actual_relative_path, "actual_relative_path"),
        )

    @property
    def replay_id(self) -> str:
        return self.validation_config.replay_id


@dataclass(frozen=True)
class GoldenReplayFileRunResult:
    case: GoldenReplayFileCase
    base_directory: str
    expected_path: str
    actual_path: str
    validation: GoldenReplayValidationResult

    def __post_init__(self) -> None:
        if not isinstance(self.case, GoldenReplayFileCase):
            raise GoldenReplayFileCaseInputError("case has an invalid type")
        if not isinstance(self.validation, GoldenReplayValidationResult):
            raise GoldenReplayFileCaseInputError("validation has an invalid type")
        for value, name in (
            (self.base_directory, "base_directory"),
            (self.expected_path, "expected_path"),
            (self.actual_path, "actual_path"),
        ):
            if not isinstance(value, str) or not value:
                raise GoldenReplayFileCaseInputError(f"{name} must be a non-empty string")
            if not Path(value).is_absolute():
                raise GoldenReplayFileCaseInputError(f"{name} must be an absolute path")
        if self.validation.config != self.case.validation_config:
            raise GoldenReplayFileCaseInputError("validation config does not match file case")

    @property
    def replay_id(self) -> str:
        return self.case.replay_id

    @property
    def matches(self) -> bool:
        return self.validation.matches
