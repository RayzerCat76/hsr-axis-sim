"""Immutable deterministic Golden Replay batch models."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from hsr_axis_sim.runtime_golden_cases import GoldenReplayFileCase, GoldenReplayFileRunResult


class GoldenReplayBatchError(RuntimeError):
    """Base class for controlled Golden Replay batch failures."""


class GoldenReplayBatchInputError(GoldenReplayBatchError):
    """Raised when a batch plan or complete result violates its contract."""


def _require_non_empty(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GoldenReplayBatchInputError(f"{name} must be a non-empty string")
    return value


@dataclass(frozen=True)
class GoldenReplayBatchPlan:
    batch_id: str
    cases: tuple[GoldenReplayFileCase, ...]

    def __post_init__(self) -> None:
        _require_non_empty(self.batch_id, "batch_id")
        if not isinstance(self.cases, tuple) or not self.cases:
            raise GoldenReplayBatchInputError("cases must be a non-empty tuple")
        if any(not isinstance(case, GoldenReplayFileCase) for case in self.cases):
            raise GoldenReplayBatchInputError("cases must contain only GoldenReplayFileCase values")
        replay_ids = tuple(case.replay_id for case in self.cases)
        if len(set(replay_ids)) != len(replay_ids):
            raise GoldenReplayBatchInputError("replay IDs must be unique within a batch")

    @property
    def case_count(self) -> int:
        return len(self.cases)


@dataclass(frozen=True)
class GoldenReplayBatchResult:
    plan: GoldenReplayBatchPlan
    base_directory: str
    results: tuple[GoldenReplayFileRunResult, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.plan, GoldenReplayBatchPlan):
            raise GoldenReplayBatchInputError("plan has an invalid type")
        if not isinstance(self.base_directory, str) or not self.base_directory:
            raise GoldenReplayBatchInputError("base_directory must be a non-empty string")
        if not Path(self.base_directory).is_absolute():
            raise GoldenReplayBatchInputError("base_directory must be an absolute path")
        if not isinstance(self.results, tuple) or any(
            not isinstance(result, GoldenReplayFileRunResult) for result in self.results
        ):
            raise GoldenReplayBatchInputError("results must be a tuple of GoldenReplayFileRunResult values")
        if len(self.results) != self.plan.case_count:
            raise GoldenReplayBatchInputError("complete batch result must contain one result per declared case")
        for index, (case, result) in enumerate(zip(self.plan.cases, self.results)):
            if result.case != case:
                raise GoldenReplayBatchInputError(
                    f"batch result case at index {index} does not match declared case"
                )
            if result.base_directory != self.base_directory:
                raise GoldenReplayBatchInputError(
                    f"batch result base directory at index {index} does not match batch base directory"
                )

    @property
    def matches(self) -> bool:
        return all(result.matches for result in self.results)

    @property
    def matched_case_count(self) -> int:
        return sum(result.matches for result in self.results)

    @property
    def mismatched_case_count(self) -> int:
        return len(self.results) - self.matched_case_count

    @property
    def first_mismatch_index(self) -> int | None:
        for index, result in enumerate(self.results):
            if not result.matches:
                return index
        return None
