"""Immutable result model for manifest-backed Golden Replay batch execution."""

from __future__ import annotations

from dataclasses import dataclass

from hsr_axis_sim.runtime_golden_batches import GoldenReplayBatchResult
from hsr_axis_sim.runtime_golden_manifest_files import GoldenReplayManifestFileLoadResult


class GoldenReplayManifestRunError(RuntimeError):
    """Base class for controlled manifest-backed batch-run failures."""


class GoldenReplayManifestRunInputError(GoldenReplayManifestRunError):
    """Raised when the composition API receives an invalid contract input."""


@dataclass(frozen=True)
class GoldenReplayManifestBatchRunResult:
    manifest_load: GoldenReplayManifestFileLoadResult
    batch_result: GoldenReplayBatchResult

    def __post_init__(self) -> None:
        if not isinstance(self.manifest_load, GoldenReplayManifestFileLoadResult):
            raise GoldenReplayManifestRunInputError("manifest_load has an invalid type")
        if not isinstance(self.batch_result, GoldenReplayBatchResult):
            raise GoldenReplayManifestRunInputError("batch_result has an invalid type")
        if self.batch_result.plan != self.manifest_load.artifact.plan:
            raise GoldenReplayManifestRunInputError(
                "batch_result plan must match the loaded manifest plan"
            )
        if self.batch_result.base_directory != self.manifest_load.base_directory:
            raise GoldenReplayManifestRunInputError(
                "batch_result base_directory must match the manifest load base_directory"
            )

    @property
    def matches(self) -> bool:
        return self.batch_result.matches

    @property
    def batch_id(self) -> str:
        return self.batch_result.plan.batch_id

    @property
    def case_count(self) -> int:
        return self.batch_result.plan.case_count
