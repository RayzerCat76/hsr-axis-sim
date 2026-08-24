# HSR-RUNTIME-ARCH-016 — Explicit End-to-End Action Session Validation Orchestrator

## Current confirmed state

- HSR-RUNTIME-ARCH-015 — PASS and merged to `main`.
- Confirmed baseline: 1017/1017 pytest, 20/20 locked regression, 2/2 trace evidence.
- Current blocker: none.

## Objective

Add one explicit caller-controlled orchestration boundary that composes accepted ARCH-013 -> ARCH-014 -> ARCH-015 without introducing new simulator, trace, stitching, or Golden validation semantics.

## Required implementation

1. Add one downstream package `hsr_axis_sim.runtime_action_session_validation`.
2. Public entry point accepts exactly:
   - caller-owned `BattleState`;
   - non-empty tuple of accepted `ExplicitActionCaptureStep` values;
   - accepted `MultiActionCaptureSessionConfig`;
   - accepted `CapturedTraceStitchConfig`;
   - caller-supplied expected Golden payload bytes;
   - accepted `GoldenReplayValidationConfig`.
3. Preflight all directly checkable input types/step shape/config count before any action execution.
4. Call accepted ARCH-013 `run_multi_action_capture_session` exactly once.
5. Only after ARCH-013 success, call accepted ARCH-014 `stitch_successful_action_session` exactly once with that exact session-result object.
6. Only after ARCH-014 success, call accepted ARCH-015 `validate_successful_session_against_golden` exactly once with that exact session-stitch-result object.
7. Return one frozen result preserving the exact ARCH-013, ARCH-014, and ARCH-015 result objects and their identity chain.
8. Golden mismatch remains a completed return value.
9. Any ARCH-013/014/015 operational failure propagates unchanged; no rollback/retry/cleanup/synthetic result is attempted.

## Acceptance criteria

- Caller-declared action order remains authoritative; no action/turn selection occurs.
- Directly checkable invalid downstream input is rejected before state mutation.
- Exact accepted result objects flow ARCH-013 -> ARCH-014 -> ARCH-015 without reconstruction.
- ARCH-013 first-failure semantics remain unchanged and prevent ARCH-014/015 invocation.
- ARCH-014 or ARCH-015 failures after successful actions propagate unchanged and do not imply rollback.
- Golden mismatch returns a complete result with accepted first-divergence provenance.
- No direct lower simulator/capture/stitch/Golden implementation is duplicated.
- Complete CI suite passes.

## Required tests

- successful multi-action end-to-end validation -> Golden PASS;
- expected-trace mismatch -> completed result with accepted first divergence;
- exact call order and identity across ARCH-013/014/015;
- invalid state/steps/session/stitch/expected-bytes/Golden inputs rejected before any action execution;
- real ARCH-013 state-mutating failure propagates unchanged and prevents later stage calls;
- ARCH-014 sentinel failure after successful actions propagates unchanged and prevents ARCH-015;
- ARCH-015 sentinel failure after successful actions/stitch propagates unchanged;
- frozen result rejects broken stage-object identity/provenance;
- preservation test confirms only accepted ARCH-013/014/015 are orchestrated and production LIFO remains unchanged.

## Files/areas that must remain unchanged

Do not modify executable behavior in `sim/**`, `search/**`, `regression/**`, `adapters/**`, `real_bindings/**`, `data/**`, accepted runtime packages, accepted Golden packages, fixtures, or reference artifacts.

## Explicit exclusions

No `Timeline.next_turn`, automatic action generation/selection, replay execution, simulator hooks, rollback, retry, queue draining/clearing, file I/O, direct ARCH-012/capture calls, direct ARCH-010 stitching, direct ARCH-011/Golden validator/loader/comparator/divergence calls, trace/event reconstruction, schema/event-map changes, new HSR mechanics, or FIFO/LIFO changes.

## Commands to run

```bash
python -m compileall -q hsr_axis_sim
python -m pytest -q
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --format text
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --only trace_evidence --format text
```

## Final report format

Report task ID, implementation summary, files added/modified, tests added, exact commands/results, warnings/errors, unresolved issues, exclusion confirmation, suggested next milestone, and update `hsr_axis_sim/LUMEN_RESULT.md`.

## Execution routing

ChatGPT: GPT-5.6 Sol.  
Codex: High if used; Codex is optional for this milestone.
