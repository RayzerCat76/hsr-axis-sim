# HSR-AXIS-001C — File-backed Golden Replay Case Runner

## Status

PASS — proceed

## Implementation summary

- Added the standard-library-only downstream package `hsr_axis_sim.runtime_golden_cases`.
- Added immutable `GoldenReplayFileCase` and `GoldenReplayFileRunResult` models.
- File cases use canonical relative POSIX expected/actual paths under one explicit base directory.
- Absolute paths, parent traversal, backslash separators, noncanonical spellings, and resolved symlink escape are rejected.
- Both case files must resolve to regular files inside the base directory.
- Reads are bounded by the accepted `GoldenReplayValidationConfig.max_bytes` limit.
- All trace loading, digest, comparison, and first-divergence semantics are delegated to HSR-AXIS-001B `validate_golden_replay_bytes`.
- Added deterministic file-case text rendering with resolved path provenance followed by the accepted 001B report.
- Added decision D-012: file-backed Golden Replay cases are base-directory bounded.

## Files added

- `LUMEN_TASK_HSR_AXIS_001C.md`
- `docs/runtime/GOLDEN_REPLAY_FILE_CASE_V1.md`
- `hsr_axis_sim/runtime_golden_cases/__init__.py`
- `hsr_axis_sim/runtime_golden_cases/model.py`
- `hsr_axis_sim/runtime_golden_cases/run.py`
- `hsr_axis_sim/tests/test_runtime_golden_file_case_runner.py`
- `hsr_axis_sim/tests/test_hsr_axis_001c_preservation.py`

## Files modified

- `docs/DECISION_LOG.md`
- `docs/HSR_AXIS_SIM_MASTER_BIBLE.md`
- `hsr_axis_sim/LUMEN_RESULT.md`

No existing production simulator, runtime contract, adapter, exporter, loader, comparator, divergence reporter, Golden Replay validator, regression, search, binding, data, or locked fixture executable behavior was modified.

## Tests added

File-case tests cover:
- matching file case with resolved absolute path provenance;
- diverged case preserving the accepted first divergence;
- deterministic text wrapping the 001B report;
- canonical relative POSIX path validation;
- missing base directory and missing file failures;
- symlink escape rejection;
- bounded read forwarding size enforcement to the accepted strict validator;
- frozen case/result models;
- invalid runner/renderer input rejection.

Preservation tests cover:
- no protected upstream package imports `runtime_golden_cases`;
- file runner delegates trace semantics only through `validate_golden_replay_bytes`;
- no comparator or divergence logic is duplicated in the file runner;
- production LIFO compatibility behavior remains unchanged.

## Exact validation commands and real results

GitHub Actions workflow: `HSR Axis Sim Validation`, PR #6, run #17, job `validate` (`97331493850`).

1. `python -m compileall -q hsr_axis_sim`
   - PASS.
2. `python -m pytest -q`
   - PASS: `843 passed in 5.20s`.
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
- Existing GitHub Actions platform warning remains: `actions/checkout@v4` and `actions/setup-python@v5` target Node.js 20 and are currently forced onto Node.js 24. This is unrelated to file-case correctness and is nonblocking.

## Acceptance review

- File identity is explicit and portable relative to one supplied base directory.
- Path traversal and symlink escape are rejected before trace validation.
- File reads are bounded and do not introduce normalization or repair.
- Runtime trace semantics are reused from the accepted 001B validator rather than duplicated.
- Resolved path, digest, comparison, and first-divergence provenance remain inspectable.
- No directory scanning, batch manifest, simulator auto-run, CLI/UI, automatic video extraction, fuzzy comparison, repair/realignment, new HSR mechanics, or FIFO/LIFO change was introduced.
- Existing production LIFO behavior remains unchanged.

## Unresolved issues

None blocking HSR-AXIS-001C acceptance.

Existing unresolved HSR game semantics remain tracked separately and were not changed.

## Suggested next milestone

`HSR-AXIS-001D — Deterministic Golden Replay Batch Runner`

001D should execute an explicit immutable ordered tuple of already-validated `GoldenReplayFileCase` definitions under one base directory. It should not add JSON manifest loading or directory discovery yet.
