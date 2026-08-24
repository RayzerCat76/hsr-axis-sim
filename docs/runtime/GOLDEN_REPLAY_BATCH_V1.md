# Golden Replay Batch Runner V1

`HSR-AXIS-001D` executes an explicit immutable ordered tuple of accepted file-backed Golden Replay cases.

## Plan

`GoldenReplayBatchPlan` contains:
- a non-empty `batch_id`;
- a non-empty tuple of `GoldenReplayFileCase` values.

Case tuple order is authoritative and replay IDs must be unique within the batch. Cases are not sorted, discovered, or deduplicated.

## Execution

`run_golden_replay_batch(plan, base_directory=...)` calls `run_golden_replay_file_case` exactly once for each case in declared tuple order.

A replay mismatch is an ordinary completed case result and does not prevent later cases from running.

A file, path, loader, configuration, or other controlled exception prevents that case from producing a valid `GoldenReplayFileRunResult`. The exception therefore propagates immediately. No partial `GoldenReplayBatchResult` is returned and later cases are not executed.

The batch layer does not load traces, compare records, select divergences, or reinterpret case results.

## Complete result

`GoldenReplayBatchResult` is created only after every declared case produced a complete case result. It preserves:
- the original batch plan;
- the resolved common base directory;
- results in exact declared order.

Derived deterministic summary values are:
- `matches`;
- `matched_case_count`;
- `mismatched_case_count`;
- `first_mismatch_index`.

The first mismatch is a batch-level case index only. Each case retains its accepted first-divergence report from earlier pipeline stages.

## Text report

`render_golden_replay_batch_text` emits a fixed-order batch summary and embeds each accepted 001C file-case report in declared order.

## Out of scope

V1 does not add JSON/file manifest loading, directory discovery, parallel execution, retries, swallowed/aggregated operational errors, simulator auto-run, CLI/UI, video extraction, fuzzy comparison, repair, realignment, new HSR mechanics, or FIFO/LIFO changes.
