# HSR-RUNTIME-ARCH-015 — Explicit Successful Session Golden Validation Handoff

## Status

PASS — proceed

## Implementation summary

- Added downstream package `hsr_axis_sim.runtime_session_golden_validation`.
- Added `validate_successful_session_against_golden`, accepting one completed ARCH-014 `SuccessfulSessionTraceStitchResult`, caller-supplied expected Golden payload bytes, and accepted `GoldenReplayValidationConfig`.
- The handoff passes exactly `session_stitch_result.stitch_result` to accepted ARCH-011 `validate_stitched_actual_against_golden` exactly once.
- The actual trace is not restitched, rebuilt, reserialized, reloaded, sorted, realigned, renumbered, or repaired.
- Added frozen `SuccessfulSessionGoldenValidationResult`, preserving the complete ARCH-014 session/stitch result and complete accepted ARCH-011 stitched-Golden validation result.
- Result construction requires the ARCH-011 `stitch_result` to be the exact same Python object as the ARCH-014 stitch result.
- Golden mismatch remains a completed accepted validation result with comparison/first-divergence provenance; ARCH-011 input/operational failures propagate unchanged.
- Added decision D-025: successful-session Golden handoff preserves exact accepted stitch provenance.

## Files added

- `LUMEN_TASK_HSR_RUNTIME_ARCH_015.md`
- `docs/runtime/SUCCESSFUL_SESSION_GOLDEN_VALIDATION_HANDOFF_V1.md`
- `hsr_axis_sim/runtime_session_golden_validation/__init__.py`
- `hsr_axis_sim/runtime_session_golden_validation/model.py`
- `hsr_axis_sim/runtime_session_golden_validation/validate.py`
- `hsr_axis_sim/tests/test_runtime_successful_session_golden_validation.py`
- `hsr_axis_sim/tests/test_runtime_arch_015_preservation.py`

## Files modified

- `docs/DECISION_LOG.md`
- `docs/HSR_AXIS_SIM_MASTER_BIBLE.md`
- `hsr_axis_sim/LUMEN_RESULT.md`

No existing simulator, runtime contract, adapter, exporter, bridge, state-capture, cursor, stitcher, stitched-Golden, action capture/session, session-stitch, loader, comparator, divergence, Golden Replay, regression, search, binding, data, or fixture executable behavior was modified.

## Tests added

Handoff tests cover:
- matching successful ARCH-014 session-stitch -> Golden PASS with complete provenance;
- mismatching expected action trace remains a completed Golden failure with accepted comparison and first-divergence provenance;
- exactly one ARCH-011 call with the exact ARCH-014 stitch Python object, exact expected bytes object, and exact config;
- invalid input types rejected before ARCH-011 invocation;
- unchanged propagation of underlying ARCH-011 failures;
- frozen wrapper behavior and rejection of equal-looking but different stitch-object provenance.

Preservation tests confirm:
- accepted upstream packages do not import `runtime_session_golden_validation`;
- the handoff delegates only to accepted ARCH-011;
- no direct Golden validator, loader, comparator, divergence, stitch, action/session execution, BattleState, Timeline, exporter, file write, encoding/decoding, sorting, runtime-event construction, or sequence rewriting is duplicated;
- production LIFO compatibility behavior remains unchanged.

## Exact validation commands and real results

GitHub Actions workflow: `HSR Axis Sim Validation`, PR #19, run #73, job `validate` (`97455673223`).

1. `python -m compileall -q hsr_axis_sim`
   - PASS.
2. `python -m pytest -q`
   - PASS: `1017 passed in 6.00s`.
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
- Existing GitHub Actions Node 20 deprecation warning remains nonblocking and unrelated to ARCH-015 correctness.

## Acceptance review

- Only completed ARCH-014 successful-session stitch provenance is accepted.
- The exact ARCH-014 stitch object is authoritative and enters ARCH-011 unchanged.
- ARCH-011 remains the sole owner of stitched-actual-to-Golden handoff semantics; lower Golden loader/comparator/divergence layers are not called directly.
- The wrapper rejects provenance substitution by Python object identity.
- Golden mismatch remains a valid completed result rather than being conflated with operational failure.
- ARCH-011 operational/input failures remain visible and are not converted into fake success.
- No production action/session execution, state access, turn/action/replay selection, retry/rollback, file I/O, restitching, actual-trace reserialization, direct Golden/comparison logic, schema/event mapping change, new HSR mechanic, or FIFO/LIFO change was introduced.
- Existing production LIFO behavior remains unchanged.

## Unresolved issues

None blocking HSR-RUNTIME-ARCH-015 acceptance.

ARCH-015 intentionally exposes the complete explicit successful-session path through Golden validation without adding a single-call end-to-end orchestrator, automatic turn/action selection, replay execution, recovery/resume, or video extraction.

Existing unresolved HSR game semantics remain tracked separately and were not changed.

## Suggested next milestone

`HSR-RUNTIME-ARCH-016 — Explicit End-to-End Action Session Validation Orchestrator`

ARCH-016 should add one explicit caller-controlled composition boundary over accepted ARCH-013 -> ARCH-014 -> ARCH-015. The caller must still supply the ordered actions/optional turn contexts, initial capture cursor, adapter/per-step trace configs, final stitch config, expected Golden bytes, and Golden validation config. It must preserve ARCH-013 first-failure/non-transactional semantics, must not retry or rollback state-mutating failures, and must not auto-select turns/actions or introduce new simulator/Golden semantics.
