# Pending-Event Capture Cursor V1

## Status

HSR-RUNTIME-ARCH-009 contract.

## Purpose

Provide an immutable caller-owned checkpoint for sequential ARCH-008 captures while preserving explicit list boundaries and runtime sequence continuity.

This contract does not persist anything inside `BattleState` and does not claim `pending_events` is a permanent history store.

## Cursor

`PendingEventCaptureCursor` is immutable and contains:

- `pending_event_index`: next caller-owned index in the current `BattleState.pending_events` list;
- `next_runtime_sequence`: next sequence value that ARCH-007 must assign to the first event of the next captured slice.

Both values are explicit non-negative integers.

## Capture request

`PendingEventCursorCaptureRequest` is immutable and contains:

- one cursor;
- caller-supplied explicit `end_index`;
- one accepted ARCH-007 `LegacyEventTraceBridgeConfig`.

The request requires:

- `end_index >= cursor.pending_event_index`;
- `bridge_config.start_sequence == cursor.next_runtime_sequence`.

There is no implicit `end_index = len(state.pending_events)` behavior.

## Capture semantics

`capture_battle_state_pending_events_from_cursor`:

1. validates the explicit state/request boundary;
2. requires the current `pending_events` container to remain a list;
3. rejects the cursor as stale if `cursor.pending_event_index > len(state.pending_events)`;
4. constructs exactly one ARCH-008 capture config using `[cursor.pending_event_index:end_index)` and the supplied bridge config;
5. delegates exactly once to ARCH-008;
6. returns the completed capture plus the next immutable cursor.

If caller `end_index` exceeds the current list length, accepted ARCH-008 validation remains authoritative and rejects the capture.

## Next cursor

After a successful capture:

```text
next.pending_event_index = request.end_index
next.next_runtime_sequence = request.cursor.next_runtime_sequence + captured_event_count
```

For an empty accepted slice, both coordinates therefore remain unchanged when `end_index == cursor.pending_event_index`.

The caller chooses whether and where to retain the returned cursor. No cursor is written into simulator state.

## Failure semantics

- stale cursor index beyond current list length fails before ARCH-008 capture;
- bridge start-sequence mismatch fails at request construction;
- invalid end bounds and adapter/export errors continue to propagate from accepted ARCH-008/ARCH-007 layers;
- source state and the original immutable cursor are unchanged on failure.

## Retention limits

ARCH-009 can observe current list length, not historical identity.

It can detect a cursor that points beyond the current list length. It cannot prove that an external caller did not truncate/rebuild/refill `pending_events` to a length that again satisfies the cursor. Such history identity is intentionally not inferred.

## Explicit non-goals

ARCH-009 does not:

- choose current list end automatically;
- persist or mutate a cursor inside `BattleState`;
- drain, clear, truncate, or rewrite `pending_events`;
- infer permanent-history or queue identity semantics;
- auto-hook action/replay execution;
- call adapter/export layers below ARCH-008 directly;
- write trace files or execute Golden Replay validation;
- add event mappings or gameplay mechanics;
- change FIFO/LIFO behavior.
