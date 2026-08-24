# HSR-RUNTIME-ARCH-005 — Expected vs Actual Trace Comparator

## Status

PASS — proceed

## Implementation summary

- Added a standard-library-only `hsr_axis_sim.runtime_comparators` sidecar.
- Added exact position-by-position comparison for two `RuntimeTraceDocument`
  record streams.
- Added deterministic recursive field differences using the existing canonical
  data projection.
- Added strict JSON-type comparison, so values such as `1` and `1.0` remain
  distinct.
- Added stable JSON-pointer-style difference paths with `~0` / `~1` escaping.
- Added explicit `MATCH`, `MISMATCH`, `EXPECTED_ONLY`, and `ACTUAL_ONLY`
  outcomes.
- Added frozen comparison result/record/difference models and deep-frozen
  captured difference values.
- Kept `trace_id` and metadata as provenance rather than independent trace
  equality axes; loader/exporter invariants remain responsible for document
  wrapper integrity.
- Added no heuristic realignment, repair, tolerance, simulator integration, or
  first-divergence reporting.

## Files added

- `hsr_axis_sim/runtime_comparators/__init__.py`
- `hsr_axis_sim/runtime_comparators/enums.py`
- `hsr_axis_sim/runtime_comparators/model.py`
- `hsr_axis_sim/runtime_comparators/compare.py`
- `hsr_axis_sim/tests/test_runtime_trace_comparator.py`
- `hsr_axis_sim/tests/test_runtime_arch_005_preservation.py`
- `docs/runtime/RUNTIME_TRACE_COMPARE_V1.md`
- `LUMEN_TASK_HSR_RUNTIME_ARCH_005.md`

## Files modified

- `docs/HSR_AXIS_SIM_MASTER_BIBLE.md`
- `hsr_axis_sim/LUMEN_RESULT.md`

No production simulator, runtime contract, adapter, exporter, loader, regression,
search, binding, data, fixture, or accepted runtime reference file was modified.

## Tests added

Comparator tests cover:

- identical record streams;
- differing document provenance with identical records;
- event-field mismatch paths;
- nested missing keys and JSON-pointer escaping;
- strict integer-vs-float differences;
- expected-only and actual-only tail records;
- no middle-record repair/realignment;
- deep immutability of captured values and frozen results;
- empty traces;
- invalid input types;
- deterministic repeated comparisons and field ordering.

Preservation tests cover:

- no existing runtime/production area imports `runtime_comparators`;
- prior trace-pipeline documentation remains present;
- production LIFO compatibility behavior remains unchanged.

## Exact validation commands and real results

GitHub Actions workflow: `HSR Axis Sim Validation`, PR #3, run #5,
job `validate` (`97325780443`).

1. `python -m compileall -q hsr_axis_sim`
   - PASS.
2. `python -m pytest -q`
   - PASS: `805 passed in 5.17s`.
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
- GitHub-hosted Actions emitted a platform deprecation warning that
  `actions/checkout@v4` and `actions/setup-python@v5` target Node.js 20 and are
  currently forced to run on Node.js 24. This is unrelated to simulator or
  comparator correctness and did not fail validation.

## Acceptance review

- Comparison is deterministic and read-only.
- Every runtime record field is compared strictly at its existing tuple
  position.
- Missing nested values preserve explicit presence flags, so missing and JSON
  null are not conflated.
- Difference ordering is deterministic.
- No tolerance, normalization, repair, deduplication, renumbering, edit-distance
  alignment, event-ID alignment, or semantic guessing is present.
- Document provenance differences do not create false combat-trace divergence.
- Existing trace schema v1 and loader/exporter contracts are unchanged.
- Existing production LIFO behavior is unchanged.
- Actual HSR same-priority FIFO/LIFO semantics remain unresolved and were not
  altered.
- ARCH-006 first-divergence selection/reporting was not implemented early.

## Unresolved issues

None blocking ARCH-005 acceptance.

The existing project-level unresolved HSR semantic questions remain tracked in
`docs/runtime/UNRESOLVED_SEMANTICS_V1.json` and are outside this milestone.

## Suggested next milestone

`HSR-RUNTIME-ARCH-006 — First Divergence Reporter`

ARCH-006 is READY / NOT STARTED.
