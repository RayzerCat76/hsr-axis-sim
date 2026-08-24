# HSR-RUNTIME-ARCH-008 — Explicit BattleState Pending-Event Slice Trace Capture

Baseline: HSR-RUNTIME-ARCH-007 PASS; pytest 916/916; locked regression 20/20; trace evidence 2/2.

Objective: add one explicitly invoked, non-mutating capture boundary from a caller-selected slice of the current `BattleState.pending_events` list into the accepted ARCH-007 legacy-event trace bridge.

Required implementation:
- new downstream `hsr_axis_sim.runtime_state_captures` package only;
- immutable capture config containing accepted `LegacyEventTraceBridgeConfig`, explicit non-negative `start_index`, and explicit non-negative `end_index`;
- require `start_index <= end_index <= len(state.pending_events)` at capture time;
- snapshot exactly `tuple(state.pending_events[start_index:end_index])` without draining, clearing, reordering, or modifying the list or Event values;
- pass that tuple exactly once through accepted ARCH-007 `build_legacy_event_trace_artifact`;
- immutable result preserves config, `pending_event_count_at_capture`, and complete ARCH-007 bridge result;
- result validates captured count, bridge-config identity, and slice/count alignment;
- `next_index` is exactly the explicit `end_index`; do not infer permanent-history semantics.

Acceptance criteria:
- exact middle-slice capture and ordering;
- state pending-event list is unchanged after success and after delegated failure;
- later state append/mutation cannot change already-built immutable trace artifact;
- empty slice follows accepted bridge/export empty policy;
- invalid state/index/list shape is rejected explicitly;
- unknown/ambiguous adapter policies remain delegated to ARCH-007;
- no direct adapter/exporter calls below ARCH-007 and no simulator execution hooks;
- all prior tests/regressions remain green and production LIFO unchanged.

Protected: all existing `sim/**` code and all accepted runtime/Golden/regression/search/binding/data/fixture executable behavior.

Excluded: implicit current-end capture, automatic cursor advancement, queue draining/clearing, claiming `pending_events` is permanent history, action/replay auto-hooking, file I/O, Golden Replay changes, new event mappings, video extraction, new HSR mechanics, FIFO/LIFO changes.

Validation uses the standard compile, full pytest, locked regression, and trace-evidence commands. Update `hsr_axis_sim/LUMEN_RESULT.md` after real CI.
