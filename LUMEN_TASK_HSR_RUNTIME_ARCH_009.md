# HSR-RUNTIME-ARCH-009 — Explicit Pending-Event Capture Cursor Contract

Baseline: HSR-RUNTIME-ARCH-008 PASS; pytest 934/934; locked regression 20/20; trace evidence 2/2.

Objective: add one immutable caller-owned cursor/checkpoint for sequential ARCH-008 captures without mutating simulator state or assigning permanent-history semantics to `BattleState.pending_events`.

Required implementation:
- new downstream `hsr_axis_sim.runtime_capture_cursors` package only;
- immutable cursor with explicit non-negative `pending_event_index` and `next_runtime_sequence`;
- immutable capture request containing cursor, caller-supplied explicit `end_index`, and accepted ARCH-007 `LegacyEventTraceBridgeConfig`;
- require `end_index >= cursor.pending_event_index` and `bridge_config.start_sequence == cursor.next_runtime_sequence`;
- before capture, explicitly reject a cursor whose pending-event index is greater than the current list length as stale/incompatible;
- otherwise construct exactly one ARCH-008 capture config using `[cursor.pending_event_index:end_index)` and the supplied bridge config, then delegate exactly once to ARCH-008;
- immutable result preserves request, complete ARCH-008 result, and next cursor;
- next cursor must be exactly `(end_index, cursor.next_runtime_sequence + captured_event_count)`;
- caller remains responsible for choosing `end_index` and for retaining/reusing the returned cursor.

Acceptance criteria:
- sequential captures preserve event-list boundaries and runtime sequence continuity;
- empty captures leave both cursor coordinates unchanged except pending index remains explicit end index;
- stale cursor (`pending_event_index > len(state.pending_events)`) is rejected before capture;
- caller-supplied end beyond current list remains rejected by ARCH-008;
- bridge start-sequence mismatch is rejected before capture;
- no automatic current-end choice, no cursor persistence inside state, no queue draining/clearing, and no simulator mutation;
- no claim that arbitrary truncate/refill cycles can be detected when current list length still satisfies the cursor;
- all prior tests/regressions remain green and production LIFO unchanged.

Protected: all existing `sim/**` code and all accepted runtime/Golden/regression/search/binding/data/fixture executable behavior.

Excluded: action/replay auto-hooks, hidden current-end capture, queue/history identity inference, queue mutation, file I/O, Golden Replay changes, event mappings, video extraction, new HSR mechanics, FIFO/LIFO changes.

Validation uses the standard compile, full pytest, locked regression, and trace-evidence commands. Update `hsr_axis_sim/LUMEN_RESULT.md` after real CI.
