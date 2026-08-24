# BattleState Pending-Event Slice Trace Capture V1

## Status

HSR-RUNTIME-ARCH-008 contract.

## Purpose

Provide one explicitly invoked, non-mutating capture boundary from a caller-selected slice of the current `BattleState.pending_events` list into the accepted ARCH-007 legacy-event trace bridge.

This contract deliberately does not call `pending_events` a permanent history store.

## Configuration

`BattleStatePendingEventSliceCaptureConfig` is immutable and contains:

- accepted `LegacyEventTraceBridgeConfig`;
- explicit non-negative `start_index`;
- explicit non-negative `end_index`.

The config requires `start_index <= end_index`.

At capture time the state additionally requires:

`end_index <= len(state.pending_events)`.

No current-end default or automatic cursor movement is introduced.

## Capture semantics

The capture boundary:

1. validates the explicit `BattleState` and current `pending_events` list shape;
2. records `pending_event_count_at_capture = len(state.pending_events)`;
3. creates exactly `tuple(state.pending_events[start_index:end_index])`;
4. passes that tuple once to ARCH-007 `build_legacy_event_trace_artifact`;
5. returns an immutable capture result.

It never drains, clears, reorders, removes, or writes back to `pending_events`.

## Result

`BattleStatePendingEventSliceCaptureResult` preserves:

- the exact capture config;
- `pending_event_count_at_capture`;
- the complete ARCH-007 bridge result.

It validates that:

- `end_index` was within the recorded pending-event count;
- the bridge config matches;
- trace record count equals `end_index - start_index`.

Derived values:

- `captured_event_count = end_index - start_index`;
- `next_index = end_index`.

`next_index` is only a returned slice boundary. ARCH-008 does not automatically store or advance a cursor.

## Snapshot stability

ARCH-007 snapshots legacy event payload data into immutable runtime contracts while building the artifact. Later changes to the mutable source `Event.data` or later appends to `BattleState.pending_events` do not change an already returned trace artifact.

## Failure semantics

Index/state-shape errors are rejected before delegation. Adapter/export failures propagate from ARCH-007. The source state/list is not modified on either success or failure.

## Explicit non-goals

ARCH-008 does not:

- claim `pending_events` is a complete or permanent event history;
- choose an implicit end index;
- persist or advance a capture cursor;
- clear/drain the source list;
- hook action/replay execution automatically;
- call adapters/exporters below ARCH-007 directly;
- write files or execute Golden Replay validation;
- add event mappings or gameplay semantics;
- change FIFO/LIFO behavior.

Cursor/session lifecycle, if needed, must be a separate reviewed milestone.
