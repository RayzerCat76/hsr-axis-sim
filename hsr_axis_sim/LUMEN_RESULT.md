# HSR-RUNTIME-ARCH-007 — Explicit Legacy Event Stream -> Runtime Trace Artifact Bridge

## Status

PASS — proceed

## Implementation summary

- Added downstream package `hsr_axis_sim.runtime_trace_bridges`.
- Added immutable `LegacyEventTraceBridgeConfig` containing an accepted `LegacyEventAdapterConfig`, non-negative `start_sequence`, accepted `TraceExportConfig`, and explicit `pretty` flag.
- Added `build_legacy_event_trace_artifact`, which consumes one caller-supplied legacy `Event` iterable through the accepted `adapt_legacy_event_stream`, passes the adapted tuple unchanged to `build_runtime_trace_document`, and serializes the accepted document through `build_runtime_trace_artifact`.
- Added immutable `LegacyEventTraceBridgeResult` preserving the exact bridge config and complete `RuntimeTraceArtifact`.
- Result construction validates export trace ID, sequence policy, metadata, pretty flag, contiguous bridge sequence provenance, and adapter-generated `legacy:<stream_id>:<sequence>` event IDs.
- Existing adapter policies remain authoritative for known, unknown, and ambiguous legacy event types; existing export policies remain authoritative for sequence validation, empty streams, semantic-gap collection, canonical bytes, and SHA-256.
- Added decision D-017: legacy-event trace bridging is explicit and source-owned; simulator queue capture lifecycle remains separate.

## Files added

- `LUMEN_TASK_HSR_RUNTIME_ARCH_007.md`
- `docs/runtime/LEGACY_EVENT_TRACE_BRIDGE_V1.md`
- `hsr_axis_sim/runtime_trace_bridges/__init__.py`
- `hsr_axis_sim/runtime_trace_bridges/model.py`
- `hsr_axis_sim/runtime_trace_bridges/legacy.py`
- `hsr_axis_sim/tests/test_runtime_legacy_trace_bridge.py`
- `hsr_axis_sim/tests/test_runtime_arch_007_preservation.py`

## Files modified

- `docs/DECISION_LOG.md`
- `docs/HSR_AXIS_SIM_MASTER_BIBLE.md`
- `hsr_axis_sim/LUMEN_RESULT.md`

No existing simulator, runtime contract, adapter, exporter, loader, comparator, divergence, Golden Replay, regression, search, binding, data, or fixture executable behavior was modified.

## Tests added

Bridge behavior tests cover:
- deterministic known legacy event stream -> runtime trace artifact output;
- nonzero start sequence and adapter event-ID provenance;
- unknown event preserve policy and semantic-gap propagation;
- unknown event reject policy;
- ambiguous `unit_defeated` preserve/reject behavior without lifecycle inference;
- empty stream behavior under accepted ALLOW/REJECT export policies;
- single-pass source iterable consumption;
- explicit pretty/compact artifact encoding;
- frozen config/result models and strict input validation;
- rejection of result provenance that conflicts with bridge/export configuration.

Preservation tests confirm:
- no accepted upstream package imports `runtime_trace_bridges`;
- bridge implementation only composes accepted adapter/exporter boundaries;
- no `BattleState`, `pending_events`, dispatch, file-write, Golden Replay, comparator, or divergence logic is present in the bridge;
- no legacy event mappings or runtime event types are redefined by the bridge;
- production LIFO compatibility behavior remains unchanged.

## Exact validation commands and real results

GitHub Actions workflow: `HSR Axis Sim Validation`, PR #11, run #38, job `validate` (`97337308272`).

1. `python -m compileall -q hsr_axis_sim`
   - PASS.
2. `python -m pytest -q`
   - PASS: `916 passed in 7.27s`.
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
- Existing GitHub Actions platform warning remains: `actions/checkout@v4` and `actions/setup-python@v5` target Node.js 20 and are currently forced onto Node.js 24. This is unrelated to bridge correctness and is nonblocking.

## Acceptance review

- The bridge is explicitly invoked and source-owned; it never reads simulator state implicitly.
- The caller-supplied legacy iterable is consumed once by the already accepted adapter.
- Adapted runtime events are not remapped or normalized again before export.
- Unknown and ambiguous event policies remain explicit; `unit_defeated` lifecycle uncertainty remains unresolved rather than guessed.
- Export metadata and policies are preserved exactly and are not amended by the bridge.
- Artifact canonical bytes and SHA-256 remain owned by the accepted exporter.
- No simulator event queue is inspected, copied implicitly, drained, cleared, or hooked.
- No trace file I/O, schema change, Golden Replay change, new event mapping, new HSR mechanic, or FIFO/LIFO change was introduced.
- Existing production LIFO behavior remains unchanged.

## Unresolved issues

None blocking HSR-RUNTIME-ARCH-007 acceptance.

Simulator `BattleState.pending_events` capture lifecycle is intentionally not assigned permanent-history semantics by ARCH-007. Current code appends dispatched events, but a later explicit capture milestone must define any snapshot/cursor behavior without assuming more than the current list state.

Existing unresolved HSR game semantics remain tracked separately and were not changed.

## Suggested next milestone

`HSR-RUNTIME-ARCH-008 — Explicit BattleState Pending-Event Slice Trace Capture`

ARCH-008 should explicitly snapshot a caller-selected `[start_index:end_index)` slice of the current `BattleState.pending_events` list, without draining or clearing it, and pass that snapshot through ARCH-007. The result should preserve slice indexes and next cursor position while avoiding any claim that `pending_events` is a permanent full-history store.
