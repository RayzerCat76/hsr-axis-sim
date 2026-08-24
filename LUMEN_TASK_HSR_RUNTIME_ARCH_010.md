# HSR-RUNTIME-ARCH-010 — Deterministic Captured Trace Segment Stitcher

Baseline: HSR-RUNTIME-ARCH-009 PASS; pytest 952/952; locked regression 20/20; trace evidence 2/2.

Objective: combine an explicit ordered tuple of completed ARCH-009 capture results into one deterministic runtime trace artifact without re-adapting legacy events or executing simulator behavior.

Required implementation:
- new downstream `hsr_axis_sim.runtime_trace_stitching` package only;
- immutable stitch config containing accepted final `TraceExportConfig` and explicit `pretty` flag;
- input must be a non-empty tuple of completed `PendingEventCursorCaptureResult` values;
- preserve tuple order exactly; no sorting or realignment;
- require cursor-chain continuity: each later request cursor must equal the previous segment's `next_cursor`;
- require every segment to use the same ARCH-002 `LegacyEventAdapterConfig`; segment-local trace IDs/metadata/pretty flags may differ;
- flatten only the already-adapted `RuntimeEvent` objects from each segment artifact's records, in record order; do not read source legacy Events and do not call ARCH-002/ARCH-007 again;
- require flattened runtime sequences to be exactly contiguous from the first segment request cursor sequence, including across segment boundaries; empty segments are allowed when already accepted and do not advance sequence;
- build the final document/artifact only through accepted ARCH-003 exporter functions and the explicit final export config;
- preserve RuntimeEvent object identity/order in the final document;
- immutable result preserves exact segment tuple, stitch config, and final artifact and validates provenance.

Acceptance criteria:
- two+ sequential segments stitch to one deterministic artifact with exact event identity/order/sequence;
- empty segment between non-empty segments is supported without sequence drift;
- all-empty explicit segments defer final empty behavior to final `TraceExportConfig`;
- broken cursor chain rejected;
- mixed legacy adapter configs/stream IDs rejected;
- wrong input tuple/type rejected;
- no re-adaptation, source state access, simulator execution, comparison, Golden Replay validation, file I/O, sorting, renumbering, or event mutation;
- all prior tests/regressions remain green and production LIFO unchanged.

Protected: all existing `sim/**` code and all accepted runtime/Golden/regression/search/binding/data/fixture executable behavior.

Excluded: action/replay auto-hooks, auto-capture, source queue access/mutation, trace comparison/Golden validation, repair/renumber/dedup, file writes, event mappings, video extraction, new HSR mechanics, FIFO/LIFO changes.

Validation uses the standard compile, full pytest, locked regression, and trace-evidence commands. Update `hsr_axis_sim/LUMEN_RESULT.md` after real CI.
