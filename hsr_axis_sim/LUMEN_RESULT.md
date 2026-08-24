# HSR-RUNTIME-ARCH-010 — Deterministic Captured Trace Segment Stitcher

## Status

PASS — proceed

## Implementation summary

- Added downstream package `hsr_axis_sim.runtime_trace_stitching`.
- Added immutable `CapturedTraceStitchConfig` containing the explicit final `TraceExportConfig` and final artifact `pretty` flag.
- Added deterministic validation/flattening for a non-empty ordered tuple of completed ARCH-009 `PendingEventCursorCaptureResult` values.
- Segment tuple order is authoritative and is never sorted or realigned.
- Every later segment request cursor must equal the previous segment's `next_cursor`.
- Every segment must use the same accepted ARCH-002 `LegacyEventAdapterConfig`, including common legacy stream ID and unknown/ambiguous policies; segment-local trace IDs/metadata/pretty flags may differ.
- The stitcher reads only existing already-adapted `RuntimeEvent` objects from completed segment artifact records, preserves exact record order, and requires exactly contiguous runtime sequences from the first segment cursor sequence.
- Empty accepted segments contribute zero events and do not shift sequence coordinates.
- The flattened existing RuntimeEvent tuple is passed only through accepted ARCH-003 `build_runtime_trace_document` and `build_runtime_trace_artifact` using the explicit final export config.
- Added immutable `CapturedTraceStitchResult` preserving exact input segments, stitch config, and final artifact; result validation confirms final records reference the exact same RuntimeEvent objects as source segment records.
- Added decision D-020: captured trace stitching preserves adapted event identity and source stream.

## Files added

- `LUMEN_TASK_HSR_RUNTIME_ARCH_010.md`
- `docs/runtime/CAPTURED_TRACE_SEGMENT_STITCH_V1.md`
- `hsr_axis_sim/runtime_trace_stitching/__init__.py`
- `hsr_axis_sim/runtime_trace_stitching/model.py`
- `hsr_axis_sim/runtime_trace_stitching/stitch.py`
- `hsr_axis_sim/tests/test_runtime_captured_trace_segment_stitcher.py`
- `hsr_axis_sim/tests/test_runtime_arch_010_preservation.py`

## Files modified

- `docs/DECISION_LOG.md`
- `hsr_axis_sim/LUMEN_RESULT.md`

No existing simulator, runtime contract, adapter, exporter, trace bridge, state-capture, cursor, loader, comparator, divergence, Golden Replay, regression, search, binding, data, or fixture executable behavior was modified.

## Tests added

Stitcher behavior tests cover:
- two sequential capture segments -> one deterministic final runtime trace artifact;
- exact RuntimeEvent object identity/order preservation;
- exact contiguous runtime sequence preservation across segment boundaries;
- segment-local trace IDs/metadata remaining distinct from final trace identity/metadata;
- explicit final pretty encoding;
- an accepted empty segment between non-empty segments without sequence drift;
- all-empty explicit segments with final ALLOW/REJECT behavior delegated to final `TraceExportConfig`;
- broken cursor-chain rejection without realignment;
- mixed legacy adapter stream/policy rejection despite cursor continuity;
- invalid segment container, empty tuple, wrong item type, wrong config type;
- frozen and strict stitch config.

Preservation tests confirm:
- accepted upstream packages do not import `runtime_trace_stitching`;
- the stitcher reads only already-adapted `record.event` values and calls only accepted ARCH-003 exporter builders;
- no legacy re-adaptation, state/pending-event access, capture call, action/replay execution, comparator/Golden call, file write, sorting, renumbering, or RuntimeEvent reconstruction was added;
- production LIFO compatibility behavior remains unchanged.

## Exact validation commands and real results

GitHub Actions workflow: `HSR Axis Sim Validation`, PR #14, run #50, job `validate` (`97344131278`).

1. `python -m compileall -q hsr_axis_sim`
   - PASS.
2. `python -m pytest -q`
   - PASS: `964 passed in 6.95s`.
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
- Existing GitHub Actions platform warning remains: `actions/checkout@v4` and `actions/setup-python@v5` target Node.js 20 and are currently forced onto Node.js 24. This is unrelated to ARCH-010 correctness and is nonblocking.

## Acceptance review

- Captured segment order, cursor chain, and runtime sequence continuity are explicit and strictly validated.
- One legacy adapter source contract is required across all stitched segments; different legacy observation streams cannot be silently merged.
- Segment-local artifact identity is not mistaken for final trace identity.
- Existing adapted RuntimeEvent objects are reused exactly; no source Event reread, re-adaptation, renumbering, repair, deduplication, sorting, or realignment occurs.
- Final canonical bytes and SHA-256 remain governed by accepted ARCH-003 exporter behavior.
- Empty segments are explicit and do not alter sequence continuity; all-empty behavior remains controlled by final export policy.
- No simulator state/queue access, action/replay execution, comparison, Golden Replay validation, file I/O, trace-schema change, event mapping, new HSR mechanic, or FIFO/LIFO change was introduced.
- Existing production LIFO behavior remains unchanged.

## Unresolved issues

None blocking HSR-RUNTIME-ARCH-010 acceptance.

ARCH-010 now produces one deterministic actual runtime trace artifact from sequential explicit captures. It does not yet provide a direct typed handoff from that stitched result into the accepted HSR-AXIS-001B Golden Replay validator; callers could manually pass artifact bytes, but that provenance composition should be explicit before any action/replay auto-hook work.

Existing unresolved HSR game semantics remain tracked separately and were not changed.

## Suggested next milestone

`HSR-RUNTIME-ARCH-011 — Explicit Stitched Actual Trace Golden Validation Handoff`

ARCH-011 should accept one completed `CapturedTraceStitchResult`, caller-supplied expected golden trace bytes, and accepted `GoldenReplayValidationConfig`; pass the stitch artifact's exact `payload_bytes` as actual bytes to accepted `validate_golden_replay_bytes`; preserve stitch and Golden validation provenance in one immutable result; and add no file I/O, auto-capture, simulator execution, comparison reimplementation, or Golden semantic changes.
