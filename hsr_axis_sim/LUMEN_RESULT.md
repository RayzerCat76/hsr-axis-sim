# HSR-RUNTIME-ARCH-008 — Explicit BattleState Pending-Event Slice Trace Capture

## Status

PASS — proceed

## Implementation summary

- Added downstream package `hsr_axis_sim.runtime_state_captures`.
- Added immutable `BattleStatePendingEventSliceCaptureConfig` containing an accepted ARCH-007 `LegacyEventTraceBridgeConfig` plus explicit non-negative `start_index` and `end_index`.
- Capture requires `start_index <= end_index <= len(state.pending_events)` at capture time.
- Added `capture_battle_state_pending_event_slice`, which records the current pending-event count, snapshots exactly `tuple(state.pending_events[start_index:end_index])`, and delegates that snapshot once to accepted ARCH-007 `build_legacy_event_trace_artifact`.
- Capture never drains, clears, reorders, removes, writes back to, or otherwise mutates `BattleState.pending_events` or its source `Event` values.
- Added immutable `BattleStatePendingEventSliceCaptureResult` preserving the exact capture config, capture-time pending-event count, and complete ARCH-007 bridge result.
- Result construction validates end-index bounds, bridge-config identity, and trace-record-count/slice-length alignment.
- Derived `next_index` is exactly the explicit `end_index`; ARCH-008 does not persist or automatically advance a cursor and does not claim `pending_events` is permanent history.
- Added decision D-018: pending-event capture is an explicit non-mutating current-list slice.

## Files added

- `LUMEN_TASK_HSR_RUNTIME_ARCH_008.md`
- `docs/runtime/BATTLE_STATE_PENDING_EVENT_SLICE_CAPTURE_V1.md`
- `hsr_axis_sim/runtime_state_captures/__init__.py`
- `hsr_axis_sim/runtime_state_captures/model.py`
- `hsr_axis_sim/runtime_state_captures/pending_events.py`
- `hsr_axis_sim/tests/test_runtime_battle_state_event_slice_capture.py`
- `hsr_axis_sim/tests/test_runtime_arch_008_preservation.py`

## Files modified

- `docs/DECISION_LOG.md`
- `hsr_axis_sim/LUMEN_RESULT.md`

No existing simulator, runtime contract, adapter, exporter, bridge, loader, comparator, divergence, Golden Replay, regression, search, binding, data, or fixture executable behavior was modified.

## Tests added

Capture behavior tests cover:
- exact middle-slice capture in current list order;
- explicit end index excluding later current events;
- no pending-event mutation on success;
- immutable trace snapshot after later source `Event.data` mutation and later state append;
- no pending-event mutation when delegated ARCH-007 adaptation fails;
- unknown-event preserve/reject policy delegation;
- empty-slice ALLOW/REJECT behavior through accepted export policy;
- invalid negative/bool/reversed indexes;
- end index beyond current list length;
- invalid state/config/pending-event container shape;
- frozen config/result models and strict result alignment.

Preservation tests confirm:
- accepted upstream packages do not import `runtime_state_captures`;
- capture delegates only through ARCH-007 rather than calling lower adapter/exporter layers directly;
- no action/replay execution hook, queue draining/clearing, implicit current-end selection, cursor persistence, file I/O, Golden Replay logic, or gameplay semantics were added;
- production LIFO compatibility behavior remains unchanged.

Before PR creation, two test assertions were corrected from nonexistent `payload["legacy_type"]` to the accepted ARCH-002 field `payload["adapter"]["legacy_event_type"]`. Production capture code was unchanged by this correction.

## Exact validation commands and real results

GitHub Actions workflow: `HSR Axis Sim Validation`, PR #12, run #42, job `validate` (`97341447097`).

1. `python -m compileall -q hsr_axis_sim`
   - PASS.
2. `python -m pytest -q`
   - PASS: `934 passed in 7.54s`.
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
- Existing GitHub Actions platform warning remains: `actions/checkout@v4` and `actions/setup-python@v5` target Node.js 20 and are currently forced onto Node.js 24. This is unrelated to ARCH-008 correctness and is nonblocking.

## Acceptance review

- Capture indexes are caller-explicit; there is no hidden current-end default.
- The exact current list slice is snapshotted without source-state mutation.
- Both success and delegated failure leave the source list unchanged.
- Runtime trace immutability is established by the accepted ARCH-007/ARCH-002 contracts; later mutable source changes cannot alter the returned artifact.
- Unknown and ambiguous event semantics remain delegated to accepted adapter policy.
- `next_index` is only a returned boundary and carries no automatic lifecycle behavior.
- `pending_events` is not upgraded to permanent-history semantics.
- No simulator execution hook, new event mapping, trace-schema change, Golden Replay change, file I/O, new HSR mechanic, or FIFO/LIFO change was introduced.
- Existing production LIFO behavior remains unchanged.

## Unresolved issues

None blocking HSR-RUNTIME-ARCH-008 acceptance.

`BattleState.pending_events` retention remains an implementation detail rather than a guaranteed permanent-history contract. Any reusable cursor/session must explicitly handle list growth/truncation and runtime sequence continuity without mutating the simulator queue.

Existing unresolved HSR game semantics remain tracked separately and were not changed.

## Suggested next milestone

`HSR-RUNTIME-ARCH-009 — Explicit Pending-Event Capture Cursor Contract`

ARCH-009 should add an immutable caller-owned cursor/checkpoint for sequential ARCH-008 captures. It should explicitly carry the next pending-event index and next runtime sequence, require a caller-supplied end index for each capture, detect incompatible/truncated current lists, and derive the next bridge start sequence without clearing or modifying simulator state. It must not introduce automatic action/replay hooks or claim permanent-history semantics.
