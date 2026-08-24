"""Composition boundary for manifest-backed deterministic Golden Replay batches."""

from __future__ import annotations

from pathlib import Path

from hsr_axis_sim.runtime_golden_batches import (
    render_golden_replay_batch_text,
    run_golden_replay_batch,
)
from hsr_axis_sim.runtime_golden_manifest_files import (
    GoldenReplayManifestFileSpec,
    load_golden_replay_manifest_file,
    render_golden_replay_manifest_file_text,
)

from .model import (
    GoldenReplayManifestBatchRunResult,
    GoldenReplayManifestRunInputError,
)


def run_golden_replay_manifest_batch(
    spec: GoldenReplayManifestFileSpec,
    *,
    base_directory: str | Path,
) -> GoldenReplayManifestBatchRunResult:
    """Load one reviewed manifest then execute its accepted batch plan under the same base."""

    if not isinstance(spec, GoldenReplayManifestFileSpec):
        raise GoldenReplayManifestRunInputError(
            "spec must be GoldenReplayManifestFileSpec"
        )

    manifest_load = load_golden_replay_manifest_file(
        spec,
        base_directory=base_directory,
    )
    batch_result = run_golden_replay_batch(
        manifest_load.artifact.plan,
        base_directory=manifest_load.base_directory,
    )
    return GoldenReplayManifestBatchRunResult(
        manifest_load=manifest_load,
        batch_result=batch_result,
    )


def render_golden_replay_manifest_batch_text(
    result: GoldenReplayManifestBatchRunResult,
) -> str:
    """Render accepted manifest-file provenance followed by the accepted batch report."""

    if not isinstance(result, GoldenReplayManifestBatchRunResult):
        raise GoldenReplayManifestRunInputError(
            "result must be GoldenReplayManifestBatchRunResult"
        )

    lines = [
        "GOLDEN_REPLAY_MANIFEST_BATCH_PASS" if result.matches else "GOLDEN_REPLAY_MANIFEST_BATCH_FAIL",
        "MANIFEST_FILE",
        render_golden_replay_manifest_file_text(result.manifest_load).rstrip("\n"),
        "BATCH",
        render_golden_replay_batch_text(result.batch_result).rstrip("\n"),
    ]
    return "\n".join(lines) + "\n"
