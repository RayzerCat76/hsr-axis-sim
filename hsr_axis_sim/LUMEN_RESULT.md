# HSR-RUNTIME-ARCH-011 — Explicit Stitched Actual Trace Golden Validation Handoff

## Status

PASS — proceed

## Implementation summary

- Added downstream package `hsr_axis_sim.runtime_stitched_golden_validation`.
- Added `validate_stitched_actual_against_golden`, accepting one completed ARCH-010 `CapturedTraceStitchResult`, caller-supplied expected golden bytes, and accepted `GoldenReplayValidationConfig`.
- The handoff calls accepted `validate_golden_replay_bytes` exactly once and passes exactly `stitch_result.artifact.payload_bytes` as actual bytes.
- Actual trace bytes are not rebuilt, reserialized, encoded/decoded, or round-tripped through a file boundary before Golden validation.
- Added immutable `StitchedActualGoldenValidationResult` preserving the complete stitch result and complete accepted `GoldenReplayValidationResult`.
- Result construction requires Golden actual loaded bytes, SHA-256, and document to exactly match the stitched artifact provenance.
- Added deterministic text that reports stitched trace ID/SHA/segment count before the complete accepted Golden Replay report.
- Added decision D-021: stitched actual Golden validation passes exact artifact bytes unchanged.

## Files added

- `LUMEN_TASK_HSR_RUNTIME_ARCH_011.md`
- `docs/runtime/STITCHED_ACTUAL_GOLDEN_VALIDATION_HANDOFF_V1.md`
- `hsr_axis_sim/runtime_stitched_golden_validation/__init__.py`
- `hsr_axis_sim/runtime_stitched_golden_validation/model.py`
- `hsr_axis_sim/runtime_stitched_golden_validation/validate.py`
- `hsr_axis_sim/tests/test_runtime_stitched_actual_golden_validation.py`
- `hsr_axis_sim/tests/test_runtime_arch_011_preservation.py`

## Files modified

- `docs/DECISION_LOG.md`
- `docs/HSR_AXIS_SIM_MASTER_BIBLE.md`
- `hsr_axis_sim/LUMEN_RESULT.md`

No existing simulator, capture, stitcher, loader, comparator, divergence, Golden Replay, regression, search, binding, data, or fixture executable behavior was modified.

## Tests added

Handoff tests cover:
- matching stitched actual -> Golden PASS with exact actual SHA provenance;
- exact Python `payload_bytes` object passed into accepted Golden validator;
- mismatching expected trace using accepted comparison and first-divergence reporting;
- expected digest failure propagation from accepted Golden validator;
- constructed result rejecting validation performed against different actual bytes;
- deterministic wrapper text;
- strict input types and frozen result.

Preservation tests confirm:
- accepted upstream packages do not import `runtime_stitched_golden_validation`;
- validation semantics are delegated only to accepted `validate_golden_replay_bytes`;
- no direct loader/comparator/divergence/build/capture/stitch execution is duplicated;
- no actual-trace reserialization or file I/O was introduced;
- production LIFO compatibility behavior remains unchanged.

## Exact validation commands and real results

Final validated head: GitHub Actions workflow `HSR Axis Sim Validation`, PR #15, run #56, job `validate` (`97345844469`).

1. `python -m compileall -q hsr_axis_sim`
   - PASS.
2. `python -m pytest -q`
   - PASS: `975 passed in 5.69s`.
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
- Existing GitHub Actions Node 20 deprecation warning remains nonblocking and unrelated to ARCH-011 correctness.

## Acceptance review

- The stitched actual artifact's exact byte identity enters Golden validation unchanged.
- Golden loader/comparator/first-divergence semantics remain exclusively owned by accepted HSR-AXIS-001B and its lower layers.
- Golden validation errors propagate rather than becoming fake mismatch results.
- Wrapper result cannot claim provenance over a Golden actual artifact that differs from the stitched artifact.
- No simulator execution/capture, action/replay hook, file I/O, reserialization, Golden semantic change, schema/event mapping change, new HSR mechanic, or FIFO/LIFO change was introduced.
- Existing production LIFO behavior remains unchanged.

## Unresolved issues

None blocking HSR-RUNTIME-ARCH-011 acceptance.

The explicit actual-trace pipeline is now closed from caller-selected simulator event slices through stitching and Golden validation. The next integration step would execute one caller-selected simulator action inside a tightly bounded capture window; that is a higher-risk state-mutating boundary and must remain a separate milestone.

Existing unresolved HSR game semantics remain tracked separately and were not changed.

## Suggested next milestone

`HSR-RUNTIME-ARCH-012 — Explicit Single-Action Event Capture Orchestrator`

ARCH-012 should define one explicit sidecar orchestration boundary that starts from a caller-owned ARCH-009 cursor aligned to the current pending-event end, executes exactly one caller-supplied legacy simulator action through the existing production API, records the post-action pending-event end, and captures exactly the newly appended event slice through accepted ARCH-009/ARCH-008 semantics. It must document partial-failure behavior because simulator action execution is state-mutating and is not transactionally rolled back. It should not modify `sim/**`, auto-select actions, or alter gameplay semantics.
