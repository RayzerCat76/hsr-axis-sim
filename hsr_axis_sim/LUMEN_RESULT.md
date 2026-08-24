# HSR-RUNTIME-ARCH-013 — Explicit Multi-Action Capture Session

## Status

PASS — proceed

## Implementation summary

- Added downstream package `hsr_axis_sim.runtime_action_sessions`.
- Added frozen `ExplicitActionCaptureStep` containing one caller-supplied production `Action` and optional caller-supplied production `TurnContext`.
- Step construction validates non-empty action/actor IDs before any session execution so failure provenance cannot become invalid after state mutation.
- Added frozen `MultiActionCaptureSessionConfig` containing one initial caller-owned ARCH-009 cursor, one common accepted `LegacyEventAdapterConfig`, one explicit `TraceExportConfig` per action, and one explicit segment-artifact `pretty` flag.
- Added `run_multi_action_capture_session`, which executes only the declared tuple order and delegates each state-mutating step exactly once to accepted ARCH-012.
- Every step constructs its bridge from the current accepted cursor runtime sequence and its caller-declared segment export config; cursor advancement occurs only from a completed ARCH-012 result's `next_cursor`.
- Added frozen `MultiActionCaptureSessionResult` with strict action/order/cursor/adapter/export-config/TurnContext provenance validation and exact final-cursor alignment.
- Added controlled `MultiActionCaptureSessionFailure` for first-step failure. It preserves exact failed action index/ID, completed ARCH-012 results before failure, and the last successful cursor while chaining the original exception as `__cause__`.
- Session failure is explicitly non-transactional: later actions are not executed, no rollback/retry/queue cleanup/cursor repair occurs, and the last successful cursor is not claimed retry-safe because the failed action/capture may have appended uncaptured events or mutated simulator state.
- Added decision D-023: multi-action sessions stop at first failure and preserve only confirmed capture boundaries.

## Files added

- `LUMEN_TASK_HSR_RUNTIME_ARCH_013.md`
- `docs/runtime/MULTI_ACTION_CAPTURE_SESSION_V1.md`
- `hsr_axis_sim/runtime_action_sessions/__init__.py`
- `hsr_axis_sim/runtime_action_sessions/model.py`
- `hsr_axis_sim/runtime_action_sessions/run.py`
- `hsr_axis_sim/tests/test_runtime_multi_action_capture_session.py`
- `hsr_axis_sim/tests/test_runtime_action_session_input_provenance.py`
- `hsr_axis_sim/tests/test_runtime_arch_013_preservation.py`

## Files modified

- `docs/DECISION_LOG.md`
- `docs/HSR_AXIS_SIM_MASTER_BIBLE.md`
- `hsr_axis_sim/LUMEN_RESULT.md`

No existing simulator, runtime contract, adapter, exporter, bridge, state-capture, cursor, stitcher, stitched-Golden, single-action capture, loader, comparator, divergence, Golden Replay, regression, search, binding, data, or fixture executable behavior was modified.

## Tests added

Session tests cover:
- successful three-action execution in exact declared order;
- exact ARCH-009 pending-event index and runtime-sequence cursor chaining across action boundaries;
- exact per-segment trace IDs, metadata, and record sequences from caller-declared export configs;
- final cursor provenance;
- explicit reuse of one caller-owned production `TurnContext` object across two non-ending actions with existing `actions_taken` mutation preserved;
- failure on the second production action after partial state/event mutation, retaining only the first completed result, exact failed index/action ID, original exception as `__cause__`, and no execution of the third action;
- post-action adaptation/capture failure on the second action after successful production mutation with the same stop/provenance behavior;
- evidence that `last_successful_cursor` can remain behind the actual pending-event list after failure and therefore is not a recovery guarantee;
- empty-step and export-config-count mismatch rejection before any action execution;
- action/actor ID provenance preflight;
- strict/frozen step, config, and result shells plus invalid-input/result-alignment rejection.

Preservation tests confirm:
- accepted upstream packages do not import `runtime_action_sessions`;
- the runner delegates state-mutating execution only through accepted ARCH-012;
- no direct `Action.execute`, `Timeline.next_turn`, replay, raw capture, adaptation/export, stitch, Golden, comparator, queue-drain/clear, file-write, sorting, or event-construction semantics are duplicated;
- production LIFO compatibility behavior remains unchanged.

## Exact validation commands and real results

GitHub Actions workflow: `HSR Axis Sim Validation`, PR #17, run #63, job `validate` (`97450335196`).

1. `python -m compileall -q hsr_axis_sim`
   - PASS.
2. `python -m pytest -q`
   - PASS: `998 passed in 7.67s`.
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
- Existing GitHub Actions Node 20 deprecation warning remains nonblocking and unrelated to ARCH-013 correctness.

## Acceptance review

- Caller-declared action order is authoritative; no turn/action selection or sorting was added.
- Session-level input shape and action identity are validated before execution where required to keep failure provenance representable.
- Cursor progression is derived only from accepted completed ARCH-012 results.
- Per-step trace artifact identity/metadata stays caller-controlled and ordered.
- Caller-provided `TurnContext` identity is preserved rather than implicitly reused or replaced.
- First failure is visible and stops the session; prior completed results remain inspectable and the original error remains chained.
- Failure provenance does not pretend that state mutation was transactional or that the last completed cursor is safe for retry/resume.
- No simulator modifications, `Timeline.next_turn`, automatic action generation/selection, replay execution, simulator hooks, queue draining/clearing, rollback, retry, file I/O, trace stitching, Golden validation, schema/event mapping change, new HSR mechanic, or FIFO/LIFO change was introduced.
- Existing production LIFO behavior remains unchanged.

## Unresolved issues

None blocking HSR-RUNTIME-ARCH-013 acceptance.

ARCH-013 intentionally does not stitch a successful session, run Golden validation, choose turns/actions, or define recovery/resume after a state-mutating failed step. Failed sessions are not complete deterministic actual traces.

Existing unresolved HSR game semantics remain tracked separately and were not changed.

## Suggested next milestone

`HSR-RUNTIME-ARCH-014 — Explicit Successful Session Trace Stitch Handoff`

ARCH-014 should accept only a completed successful `MultiActionCaptureSessionResult`, extract the accepted ARCH-009 capture result from each completed ARCH-012 result in exact session order, and delegate them unchanged to accepted ARCH-010 stitching under one caller-supplied final `TraceExportConfig` and explicit pretty flag. It must preserve complete session + stitch provenance and must not execute actions, accept partial session failures, or perform Golden validation yet.
