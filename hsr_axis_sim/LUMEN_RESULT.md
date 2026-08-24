# HSR-RUNTIME-ARCH-012 — Explicit Single-Action Event Capture Orchestrator

## Status

PASS — proceed

## Implementation summary

- Added downstream package `hsr_axis_sim.runtime_action_captures`.
- Added immutable `SingleActionEventCaptureRequest` containing one caller-owned `PendingEventCaptureCursor` and accepted `LegacyEventTraceBridgeConfig` with exact runtime-sequence alignment.
- Added `execute_action_and_capture_pending_events` as one explicit non-transactional sidecar boundary around the existing production `Action.execute` API.
- Preflight requires `request.cursor.pending_event_index == len(state.pending_events)` before action execution so no pre-existing events can be silently included.
- The orchestrator calls `Action.execute(state, turn_context)` exactly once.
- After successful action execution, the concrete post-action `len(state.pending_events)` becomes the explicit ARCH-009 capture end index.
- Exact new events are delegated to accepted `capture_battle_state_pending_events_from_cursor`; no Event/RuntimeEvent reconstruction or trace semantics are duplicated.
- Added frozen `SingleActionEventCaptureResult` preserving caller request, action/actor IDs, pre/post pending-event counts, returned production `TurnContext`, and complete ARCH-009 result.
- Result invariants require exact pre/post append-window alignment and unchanged bridge/cursor provenance.
- Explicitly documented non-transactional partial failure: action or downstream capture exceptions propagate unchanged; no rollback, retry, queue cleanup, fake result, or cursor mutation is attempted.
- Added decision D-022: single-action capture is explicit and non-transactional.

## Files added

- `LUMEN_TASK_HSR_RUNTIME_ARCH_012.md`
- `docs/runtime/SINGLE_ACTION_EVENT_CAPTURE_V1.md`
- `hsr_axis_sim/runtime_action_captures/__init__.py`
- `hsr_axis_sim/runtime_action_captures/model.py`
- `hsr_axis_sim/runtime_action_captures/capture.py`
- `hsr_axis_sim/tests/test_runtime_single_action_event_capture.py`
- `hsr_axis_sim/tests/test_runtime_arch_012_preservation.py`

## Files modified

- `docs/DECISION_LOG.md`
- `docs/HSR_AXIS_SIM_MASTER_BIBLE.md`
- `hsr_axis_sim/LUMEN_RESULT.md`

No existing simulator, runtime contract, adapter, exporter, bridge, state-capture, cursor, stitcher, loader, comparator, divergence, Golden Replay, regression, search, binding, data, or fixture executable behavior was modified.

## Tests added

Single-action capture tests cover:
- exact successful capture of only newly appended `action_started` / `action_finished` events;
- exclusion and preservation of pre-existing pending events;
- exact runtime event sequence/event-ID/action-ID and ARCH-009 cursor advancement;
- pre-action cursor/list-end alignment rejection before production action execution;
- caller-supplied `TurnContext` passed through and returned by identity;
- production action failure after partial state/event mutation propagating unchanged and skipping capture;
- successful action followed by downstream adaptation/capture failure propagating unchanged without rollback;
- strict request/result provenance and frozen shells;
- invalid state/action/request/context input rejection.

Preservation tests confirm:
- accepted upstream packages do not import `runtime_action_captures`;
- orchestration uses only the existing `Action.execute` and accepted ARCH-009 capture boundary;
- no `Timeline.next_turn`, replay, Golden, comparator, stitcher, file-write, queue-drain/clear, retry, or exception swallowing behavior was introduced;
- no Event/RuntimeEvent construction or adaptation/export reimplementation was added;
- production LIFO compatibility behavior remains unchanged.

## Exact validation commands and real results

GitHub Actions workflow: `HSR Axis Sim Validation`, PR #16, run #59, job `validate` (`97447247384`).

1. `python -m compileall -q hsr_axis_sim`
   - PASS.
2. `python -m pytest -q`
   - PASS: `986 passed in 7.50s`.
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
- Existing GitHub Actions Node 20 deprecation warning remains nonblocking and unrelated to ARCH-012 correctness.

## Acceptance review

- The capture window is explicit and cannot silently include old pending events.
- Exactly one caller-selected production Action is executed through the existing API; no gameplay execution semantics were replaced.
- Runtime trace capture remains owned by accepted ARCH-009/ARCH-008/ARCH-007 layers.
- Successful results prove exact pre/post event-list boundaries and cursor/sequence continuity.
- The returned production `TurnContext` is preserved without redefining or deep-freezing its simulator semantics.
- Action failure and post-action capture failure are visibly non-transactional; real partial simulator mutation is not hidden or repaired.
- No simulator hooks, automatic action selection, turn selection, replay execution, rollback, retry, batching, file I/O, Golden validation, trace stitching, schema/event mapping change, new HSR mechanic, or FIFO/LIFO change was introduced.
- Existing production LIFO behavior remains unchanged.

## Unresolved issues

None blocking HSR-RUNTIME-ARCH-012 acceptance.

ARCH-012 intentionally does not decide multi-action/session control flow, automatic turn selection, replay orchestration, or recovery after partial failure. Those are separate higher-risk orchestration decisions.

Existing unresolved HSR game semantics remain tracked separately and were not changed.

## Suggested next milestone

`HSR-RUNTIME-ARCH-013 — Explicit Multi-Action Capture Session`

ARCH-013 should compose an explicit caller-supplied ordered action sequence through repeated accepted ARCH-012 calls while keeping the caller-owned cursor chain explicit. It must define stop/partial-result behavior for failures before implementation, must not auto-select turns/actions, and should not yet perform automatic Golden validation or replay execution.
