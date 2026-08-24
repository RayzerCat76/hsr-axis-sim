# HSR-AXIS-001D — Deterministic Golden Replay Batch Runner

## Status

PASS — proceed

## Implementation summary

- Added the standard-library-only downstream package `hsr_axis_sim.runtime_golden_batches`.
- Added immutable non-empty `GoldenReplayBatchPlan` values with unique replay IDs and authoritative declared tuple order.
- Added immutable complete `GoldenReplayBatchResult` values with exact case/result alignment and one resolved common base directory.
- Each declared case executes exactly once through HSR-AXIS-001C `run_golden_replay_file_case`.
- Replay mismatches are completed results and do not stop later declared cases.
- File/config/loader and other operational exceptions propagate immediately at the exact case; no partial batch result is returned.
- Added deterministic derived summary values: `matches`, matched/mismatched case counts, and `first_mismatch_index`.
- Added deterministic batch text that wraps accepted 001C reports in declared case order.
- Added decision D-013: preserve declared order; mismatch continues; operational errors fail fast.

## Files added

- `LUMEN_TASK_HSR_AXIS_001D.md`
- `docs/runtime/GOLDEN_REPLAY_BATCH_V1.md`
- `hsr_axis_sim/runtime_golden_batches/__init__.py`
- `hsr_axis_sim/runtime_golden_batches/model.py`
- `hsr_axis_sim/runtime_golden_batches/run.py`
- `hsr_axis_sim/tests/test_runtime_golden_batch_runner.py`
- `hsr_axis_sim/tests/test_hsr_axis_001d_preservation.py`

## Files modified

- `docs/DECISION_LOG.md`
- `docs/HSR_AXIS_SIM_MASTER_BIBLE.md`
- `hsr_axis_sim/LUMEN_RESULT.md`

No existing production simulator, runtime trace layer, Golden Replay validator, file-case runner, regression, search, binding, data, or locked fixture executable behavior was modified.

## Tests added

Batch tests cover:
- declared-order execution;
- mismatch continuing to later cases;
- all-match summary;
- non-empty tuple validation;
- wrong case type rejection;
- duplicate replay-ID rejection;
- operational fail-fast behavior at the exact case;
- deterministic text and declared report order;
- frozen plan/result models;
- strict complete-result alignment;
- invalid runner/renderer input rejection.

Preservation tests cover:
- no protected upstream package imports `runtime_golden_batches`;
- batch runner delegates only to the accepted 001C file-case boundary;
- no trace loading/comparison/divergence logic is duplicated;
- production LIFO compatibility behavior remains unchanged.

## Exact validation commands and real results

GitHub Actions workflow: `HSR Axis Sim Validation`, PR #7, run #21, job `validate` (`97332387296`).

1. `python -m compileall -q hsr_axis_sim`
   - PASS.
2. `python -m pytest -q`
   - PASS: `853 passed in 7.16s`.
3. `python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --format text`
   - PASS 20/20 total checks:
     - 12/12 golden replays;
     - 2/2 manual checks;
     - 2/2 search scenarios;
     - 2/2 action-sequence trace checks;
     - 2/2 trace-evidence checks.
4. `python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --only trace_evidence --format text`
   - PASS 2/2 trace-evidence checks.

## Warnings / errors

- No compile, test, or regression errors.
- Existing GitHub Actions platform warning remains: `actions/checkout@v4` and `actions/setup-python@v5` target Node.js 20 and are currently forced onto Node.js 24. This is unrelated to batch correctness and is nonblocking.

## Acceptance review

- Batch order is explicit and stable; there is no sorting, discovery, deduplication, parallelism, or retry.
- Comparison mismatch and inability to validate a case remain distinct states.
- A returned batch result is always complete for every declared case.
- Batch summary values are derived only from accepted case results.
- Lower trace, comparison, divergence, validation, and path semantics are reused rather than duplicated.
- No JSON/file manifest loader, simulator auto-run, CLI/UI, automatic video extraction, fuzzy comparison, repair/realignment, new HSR mechanics, or FIFO/LIFO change was introduced.
- Existing production LIFO behavior remains unchanged.

## Unresolved issues

None blocking HSR-AXIS-001D acceptance.

Existing unresolved HSR game semantics remain tracked separately and were not changed.

## Suggested next milestone

`HSR-AXIS-001E — Strict Golden Replay Manifest Artifact`

001E should define and strictly load a deterministic canonical JSON manifest that reconstructs an accepted `GoldenReplayBatchPlan`; it should not execute the batch yet.
