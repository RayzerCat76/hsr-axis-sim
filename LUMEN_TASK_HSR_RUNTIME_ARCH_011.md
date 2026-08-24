# HSR-RUNTIME-ARCH-011 — Explicit Stitched Actual Trace Golden Validation Handoff

Baseline: HSR-RUNTIME-ARCH-010 PASS; pytest 964/964; locked regression 20/20; trace evidence 2/2.

Objective: add one explicit typed handoff from a completed ARCH-010 stitched actual trace artifact into the accepted HSR-AXIS-001B Golden Replay validator without reserializing or reimplementing validation semantics.

Required implementation:
- new downstream `hsr_axis_sim.runtime_stitched_golden_validation` package only;
- input: one completed `CapturedTraceStitchResult`, caller-supplied expected golden trace bytes, and accepted `GoldenReplayValidationConfig`;
- validate stitch/config input types before delegation;
- call accepted `validate_golden_replay_bytes` exactly once with caller expected bytes and exactly `stitch_result.artifact.payload_bytes` as actual bytes;
- do not reserialize/rebuild/reload actual bytes before the accepted Golden validator;
- immutable result preserves complete stitch result and complete `GoldenReplayValidationResult`;
- result must reject any validation result whose actual loaded artifact bytes/SHA do not exactly equal the stitched artifact bytes/SHA;
- optional deterministic text may wrap stitch provenance plus accepted Golden validation text without changing semantics.

Acceptance criteria:
- matching expected bytes produce Golden PASS and exact actual SHA provenance;
- mismatching expected trace produces accepted deterministic first-divergence output;
- actual payload object passed to the Golden validator is the exact stitch artifact `payload_bytes` object;
- expected digest/load errors propagate unchanged from accepted Golden validator;
- constructed result rejects mismatched actual provenance;
- no loader/comparator/divergence logic is duplicated;
- no simulator execution/capture, file I/O, reserialization, schema changes, event mapping, new HSR mechanics, or FIFO/LIFO changes;
- all prior tests/regressions remain green and production LIFO unchanged.

Protected: all existing `sim/**` code and all accepted runtime/Golden/regression/search/binding/data/fixture executable behavior.

Excluded: auto-capture, action/replay hooks, source queue access, direct loader/comparator/divergence calls, Golden semantic changes, file writes, repair/migration, video extraction, new HSR mechanics, FIFO/LIFO changes.

Validation uses the standard compile, full pytest, locked regression, and trace-evidence commands. Update `hsr_axis_sim/LUMEN_RESULT.md` after real CI.
