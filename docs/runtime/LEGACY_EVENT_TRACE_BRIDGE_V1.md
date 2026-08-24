# Legacy Event Stream -> Runtime Trace Artifact Bridge V1

## Status

HSR-RUNTIME-ARCH-007 contract.

## Purpose

Provide one explicitly invoked, read-only composition boundary from a caller-supplied legacy simulator `Event` stream to the accepted deterministic runtime trace artifact format.

This milestone does not capture events from simulator state. The caller owns the source event iterable and decides when it is supplied.

## Configuration

`LegacyEventTraceBridgeConfig` is immutable and contains:

- accepted `LegacyEventAdapterConfig`;
- non-negative `start_sequence`;
- accepted `TraceExportConfig`;
- explicit `pretty` boolean.

No policy is inferred or defaulted by the bridge.

## Composition order

The bridge performs exactly:

1. `adapt_legacy_event_stream(events, start_sequence=..., config=adapter_config)`;
2. `build_runtime_trace_document(runtime_events, config=export_config)`;
3. `build_runtime_trace_artifact(document, pretty=pretty)`.

The source iterable is handed once to the accepted adapter. The adapted tuple is passed unchanged to the accepted exporter.

## Preserved semantics

The bridge does not reinterpret:

- known legacy event mappings;
- unknown event policy;
- ambiguous event policy;
- `unit_defeated` lifecycle uncertainty;
- export sequence policy;
- export empty-trace policy;
- export metadata;
- semantic-gap collection;
- canonical JSON serialization or SHA-256 identity.

## Result

`LegacyEventTraceBridgeResult` is immutable and contains the exact bridge config and complete `RuntimeTraceArtifact`.

Result construction verifies:

- trace ID, sequence policy, metadata, and pretty flag match the config;
- every non-empty record sequence is `start_sequence + index`;
- every runtime event ID matches `legacy:<stream_id>:<sequence>`.

## Explicit non-goals

ARCH-007 does not:

- inspect, copy, drain, or clear `BattleState.pending_events` or any simulator queue;
- register simulator hooks or callbacks;
- mutate simulator state;
- write trace files;
- add or override legacy event mappings;
- change runtime trace schema;
- execute Golden Replay validation;
- infer unresolved HSR mechanics;
- change production FIFO/LIFO behavior.

A later explicit milestone may define simulator event-capture lifecycle after the source queue/history semantics are reviewed and tested.
