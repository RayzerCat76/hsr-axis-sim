# HSR-RUNTIME-ARCH-009 — Explicit Pending-Event Capture Cursor Contract

## Status

PASS — proceed

## Implementation summary

- Added downstream package `hsr_axis_sim.runtime_capture_cursors`.
- Added immutable `PendingEventCaptureCursor` with explicit non-negative `pending_event_index` and `next_runtime_sequence` coordinates.
- Added immutable `PendingEventCursorCaptureRequest` containing one cursor, caller-supplied explicit `end_index`, and accepted ARCH-007 `LegacyEventTraceBridgeConfig`.
- Requests require `end_index >= cursor.pending_event_index` and `bridge_config.start_sequence == cursor.next_runtime_sequence`.
- Added `capture_battle_state_pending_events_from_cursor`, which rejects a cursor whose index is beyond the current pending-event list length, constructs exactly one ARCH-008 `[cursor.pending_event_index:end_index)` capture, and delegates exactly once to ARCH-008.
- Added immutable `PendingEventCursorCaptureResult` preserving the exact request, complete ARCH-008 capture result, and next cursor.
- Successful next cursor is exactly `(end_index, previous next_runtime_sequence + captured_event_count)`.
- Empty accepted captures therefore leave both coordinates unchanged when `end_index == cursor.pending_event_index`.
- No cursor is persisted or mutated inside `BattleState`; the caller owns the returned checkpoint.
- Added decision D-019: pending-event capture cursors are caller-owned coordinate checkpoints.

## Files added

- `LUMEN_TASK_HSR_RUNTIME_ARCH_009.md`
- `docs/runtime/PENDING_EVENT_CAPTURE_CURSOR_V1.md`
- `hsr_axis_sim/runtime_capture_cursors/__init__.py`
- `hsr_axis_sim/runtime_capture_cursors/model.py`
- `hsr_axis_sim/runtime_capture_cursors/capture.py`
- `hsr_axis_sim/tests/test_runtime_pending_event_capture_cursor.py`
- `hsr_axis_sim/tests/test_runtime_arch_009_preservation.py`

## Files modified

- `docs/DECISION_LOG.md`
- `hsr_axis_sim/LUMEN_RESULT.md`

No existing simulator, runtime contract, adapter, exporter, trace bridge, state-capture, loader, comparator, divergence, Golden Replay, regression, search, binding, data, or fixture executable behavior was modified.

## Tests added

Cursor behavior tests cover:
- two sequential captures preserving explicit list-index boundaries and runtime sequence continuity;
- caller-selected trace configs for separate slices while sequence coordinates remain continuous;
- empty accepted capture with unchanged cursor coordinates;
- explicit stale-cursor rejection when cursor index exceeds current list length;
- caller end index beyond current list remaining rejected by ARCH-008;
- bridge start-sequence mismatch rejection before capture;
- delegated adapter failure leaving state and original cursor unchanged;
- unknown-event preserve policy delegation through ARCH-008/ARCH-007;
- invalid cursor/request coordinate and type validation;
- invalid state/request/pending-event container shape;
- frozen cursor/request/result models and strict next-cursor alignment.

Preservation tests confirm:
- accepted upstream packages do not import `runtime_capture_cursors`;
- state capture is delegated only through ARCH-008 rather than lower adapter/export layers;
- no implicit current-end capture, simulator cursor persistence, queue mutation, action/replay hook, or gameplay behavior was added;
- production LIFO compatibility behavior remains unchanged.

## Exact validation commands and real results

GitHub Actions workflow: `HSR Axis Sim Validation`, PR #13, run #46, job `validate` (`97342638847`).

1. `python -m compileall -q hsr_axis_sim`
   - PASS.
2. `python -m pytest -q`
   - PASS: `952 passed in 7.19s`.
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
- Existing GitHub Actions platform warning remains: `actions/checkout@v4` and `actions/setup-python@v5` target Node.js 20 and are currently forced onto Node.js 24. This is unrelated to ARCH-009 correctness and is nonblocking.

## Acceptance review

- Cursor state is explicit, immutable, and caller-owned.
- Runtime sequence continuity is enforced before capture rather than inferred afterward.
- List-index advancement is exactly the caller-selected end boundary; there is no hidden current-end default.
- Stale detection is intentionally limited to the observable condition `cursor.pending_event_index > len(state.pending_events)`.
- The contract does not claim it can detect arbitrary external truncate/refill cycles that restore a satisfying list length.
- ARCH-008 remains authoritative for actual slice capture and current end-bound validation.
- Source simulator state is never drained, cleared, rewritten, or assigned cursor metadata.
- No action/replay auto-hook, file I/O, trace-schema change, Golden Replay change, new event mapping, new HSR mechanic, or FIFO/LIFO change was introduced.
- Existing production LIFO behavior remains unchanged.

## Unresolved issues

None blocking HSR-RUNTIME-ARCH-009 acceptance.

ARCH-009 creates deterministic sequential capture segments but does not yet combine multiple segment artifacts into one full actual runtime trace artifact. That composition should remain explicit and preserve RuntimeEvent identity/order without re-adapting source legacy events.

Existing unresolved HSR game semantics remain tracked separately and were not changed.

## Suggested next milestone

`HSR-RUNTIME-ARCH-010 — Deterministic Captured Trace Segment Stitcher`

ARCH-010 should accept an explicit ordered tuple of completed ARCH-009 capture results, require cursor-chain and runtime-sequence continuity, preserve accepted RuntimeEvent identity/order, and build one deterministic final runtime trace artifact through the existing exporter without re-adapting legacy events. It should not execute simulator actions, auto-capture current state, modify source segments, or perform Golden Replay validation.
