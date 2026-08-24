# Captured Trace Segment Stitch V1

## Status

HSR-RUNTIME-ARCH-010 contract.

## Purpose

Combine an explicit ordered tuple of completed ARCH-009 capture results into one deterministic runtime trace artifact without returning to mutable legacy `Event` sources or executing simulator behavior.

## Inputs

`CapturedTraceStitchConfig` is immutable and contains:

- one explicit final `TraceExportConfig`;
- explicit `pretty` artifact encoding flag.

The stitcher also requires a non-empty tuple of completed `PendingEventCursorCaptureResult` values.

Tuple order is authoritative and is never sorted or realigned.

## Segment continuity

For every later segment:

```text
segment.request.cursor == previous_segment.next_cursor
```

This preserves both caller-owned pending-event list boundaries and runtime sequence coordinates established by ARCH-009.

Every segment must also use the same ARCH-002 `LegacyEventAdapterConfig`. This includes the same legacy `stream_id` and unknown/ambiguous event policies.

Segment-local trace IDs, segment export metadata, sequence-policy declarations, and pretty/compact artifact encoding are not the identity of the final stitched trace and may differ.

## Runtime event preservation

The stitcher reads only the already-adapted `RuntimeEvent` objects present at:

```text
segment.capture_result.bridge_result.artifact.document.records[*].event
```

It does not read source legacy Events and does not invoke ARCH-002 or ARCH-007 again.

Events are flattened in exact segment tuple order and exact record order.

Flattened event sequences must be exactly contiguous starting at the first segment request cursor's `next_runtime_sequence`. Empty accepted segments contribute zero events and do not shift that sequence.

No event is renumbered, repaired, deduplicated, reordered, copied into a new `RuntimeEvent`, or otherwise normalized.

## Final artifact

The flattened existing `RuntimeEvent` tuple is passed to accepted ARCH-003:

1. `build_runtime_trace_document(events, config=final_export_config)`;
2. `build_runtime_trace_artifact(document, pretty=pretty)`.

Therefore final trace ID, metadata, sequence policy, empty-trace policy, canonical serialization, and SHA-256 remain governed by the accepted exporter.

The returned result preserves:

- exact stitch config;
- exact input segment tuple;
- complete final `RuntimeTraceArtifact`.

Result validation confirms that each final record refers to the exact same `RuntimeEvent` object as the corresponding source segment record.

## Empty behavior

The input segment tuple itself must be non-empty.

Individual segments may contain zero events when their accepted ARCH-007/ARCH-003 policy permitted that.

If every explicit segment is empty, final success/failure is determined only by the final `TraceExportConfig.empty_trace_policy`.

## Explicit non-goals

ARCH-010 does not:

- inspect `BattleState` or pending-event queues;
- capture new events;
- re-adapt legacy Events;
- execute simulator actions or replay steps;
- sort, realign, renumber, repair, or deduplicate events;
- compare expected/actual traces;
- execute Golden Replay validation;
- write files;
- change trace schema, event mappings, gameplay mechanics, or FIFO/LIFO behavior.
