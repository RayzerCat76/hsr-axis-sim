# HSR-RUNTIME-ARCH-006 — First Divergence Reporter

## Status

PASS — proceed

## Implementation summary

- Added a standard-library-only `hsr_axis_sim.runtime_divergence` downstream sidecar.
- Added mechanical first-divergence selection over an existing
  `RuntimeTraceComparisonResult`.
- Selection uses the first non-`MATCH` record in existing ARCH-005 tuple order.
- For `MISMATCH`, selection uses the first already-ordered ARCH-005 field
  difference without re-sorting or recomputing it.
- `EXPECTED_ONLY` and `ACTUAL_ONLY` are reported directly without fabricated
  field differences.
- Added frozen structured report models preserving trace provenance, record
  counts, total mismatch count, record index/status, expected/actual record
  references, sequence, event ID/type, first field difference, and per-record
  difference count.
- Added deterministic text rendering with fixed line ordering and canonical JSON
  values.
- Added explicit `ABSENT` rendering so missing values remain distinguishable
  from present JSON `null`.
- Added no comparison logic, tolerance, realignment, repair, simulator wiring,
  Golden Replay orchestration, or HSR semantic changes.

## Files added

- `hsr_axis_sim/runtime_divergence/__init__.py`
- `hsr_axis_sim/runtime_divergence/model.py`
- `hsr_axis_sim/runtime_divergence/report.py`
- `hsr_axis_sim/tests/test_runtime_first_divergence_reporter.py`
- `hsr_axis_sim/tests/test_runtime_arch_006_preservation.py`
- `docs/runtime/RUNTIME_TRACE_FIRST_DIVERGENCE_V1.md`
- `LUMEN_TASK_HSR_RUNTIME_ARCH_006.md`

## Files modified

- `docs/DECISION_LOG.md`
- `docs/HSR_AXIS_SIM_MASTER_BIBLE.md`
- `hsr_axis_sim/LUMEN_RESULT.md`

No production simulator, runtime contract, adapter, exporter, loader, comparator,
regression, search, binding, data, fixture, or accepted runtime reference file
was modified.

## Tests added

Reporter tests cover:

- fully matching comparison and stable MATCH text;
- first divergence after preceding matching records;
- later divergences do not replace the first divergence;
- first field difference preserves ARCH-005 comparator ordering;
- EXPECTED_ONLY reporting without fabricated fields;
- ACTUAL_ONLY reporting without fabricated fields;
- missing-vs-present-null distinction;
- deterministic canonical nested JSON and Unicode rendering;
- frozen report and divergence models;
- invalid input rejection;
- read-only repeatable reporting.

Preservation tests cover:

- no protected upstream area imports `runtime_divergence`;
- reporter source does not call `compare_runtime_trace_documents`;
- prior trace-pipeline contracts remain present;
- production LIFO compatibility behavior remains unchanged.

## Exact validation commands and real results

GitHub Actions workflow: `HSR Axis Sim Validation`, PR #4, run #9,
job `validate` (`97329068220`).

1. `python -m compileall -q hsr_axis_sim`
   - PASS.
2. `python -m pytest -q`
   - PASS: `819 passed in 7.18s`.
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

- No test, compile, or regression errors.
- GitHub-hosted Actions emitted the existing platform deprecation warning that
  `actions/checkout@v4` and `actions/setup-python@v5` target Node.js 20 and are
  currently forced to run on Node.js 24. This is unrelated to simulator or
  reporter correctness and did not fail validation.

## Acceptance review

- Reporter consumes a validated ARCH-005 comparison result instead of
  recomputing comparison.
- First record selection preserves existing comparison tuple order exactly.
- First field selection preserves existing difference order exactly.
- No semantic priority ranking was introduced.
- Later divergences remain represented by `total_mismatch_count`; the reporter
  does not imply that the first divergence is the only divergence.
- Missing and present JSON null values remain distinct in structured and text
  output.
- Text rendering is deterministic, fixed-order, and canonical for JSON values.
- Structured report models are immutable.
- No fuzzy equality, tolerance, normalization, repair, deduplication,
  renumbering, event-ID/sequence/edit-distance realignment, or semantic guessing
  is present.
- Existing comparator, trace schema v1, loader/exporter contracts, and
  production simulator behavior are unchanged.
- Existing production LIFO behavior is unchanged.
- Actual HSR same-priority FIFO/LIFO semantics remain unresolved and were not
  altered.
- Golden Replay orchestration was not implemented early.

## Unresolved issues

None blocking ARCH-006 acceptance.

The existing project-level unresolved HSR semantic questions remain tracked in
`docs/runtime/UNRESOLVED_SEMANTICS_V1.json` and are outside this milestone.

## Suggested next milestone

`Deterministic Golden Replay Validator`

This next milestone is READY / NOT STARTED. Its first replay must be manually
constructed and deterministic; automatic video-to-trace extraction remains out
of scope.
