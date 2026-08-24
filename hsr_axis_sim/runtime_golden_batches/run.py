"""Deterministic sequential execution for explicit Golden Replay batches."""

from __future__ import annotations

from pathlib import Path

from hsr_axis_sim.runtime_contracts.serialization import canonical_json_dumps
from hsr_axis_sim.runtime_golden_cases import (
    render_golden_replay_file_case_text,
    run_golden_replay_file_case,
)

from .model import GoldenReplayBatchInputError, GoldenReplayBatchPlan, GoldenReplayBatchResult


def run_golden_replay_batch(
    plan: GoldenReplayBatchPlan,
    *,
    base_directory: str | Path,
) -> GoldenReplayBatchResult:
    """Run every declared case once, in tuple order, unless a case raises."""

    if not isinstance(plan, GoldenReplayBatchPlan):
        raise GoldenReplayBatchInputError("plan must be GoldenReplayBatchPlan")

    results = []
    for case in plan.cases:
        results.append(run_golden_replay_file_case(case, base_directory=base_directory))

    result_tuple = tuple(results)
    return GoldenReplayBatchResult(
        plan=plan,
        base_directory=result_tuple[0].base_directory,
        results=result_tuple,
    )


def render_golden_replay_batch_text(result: GoldenReplayBatchResult) -> str:
    """Render a deterministic batch summary and each accepted case report in order."""

    if not isinstance(result, GoldenReplayBatchResult):
        raise GoldenReplayBatchInputError("result must be GoldenReplayBatchResult")

    first_mismatch = (
        "NONE" if result.first_mismatch_index is None else str(result.first_mismatch_index)
    )
    lines = [
        "GOLDEN_REPLAY_BATCH_PASS" if result.matches else "GOLDEN_REPLAY_BATCH_FAIL",
        f"batch_id={canonical_json_dumps(result.plan.batch_id, pretty=False)}",
        f"base_directory={canonical_json_dumps(result.base_directory, pretty=False)}",
        f"case_count={result.plan.case_count}",
        f"matched_case_count={result.matched_case_count}",
        f"mismatched_case_count={result.mismatched_case_count}",
        f"first_mismatch_index={first_mismatch}",
    ]
    for index, case_result in enumerate(result.results):
        lines.append(
            f"CASE index={index} replay_id={canonical_json_dumps(case_result.replay_id, pretty=False)}"
        )
        lines.append(render_golden_replay_file_case_text(case_result).rstrip("\n"))
    return "\n".join(lines) + "\n"
