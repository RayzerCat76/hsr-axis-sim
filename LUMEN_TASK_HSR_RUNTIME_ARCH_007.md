# HSR-RUNTIME-ARCH-007 — Explicit Legacy Event Stream -> Runtime Trace Artifact Bridge

Baseline: HSR-AXIS-001G PASS; pytest 903/903; locked regression 20/20; trace evidence 2/2.

Objective: provide one explicitly invoked deterministic composition boundary from a caller-supplied legacy simulator `Event` stream to the accepted runtime trace artifact format.

Required implementation:
- new downstream `hsr_axis_sim.runtime_trace_bridges` package only;
- immutable bridge config containing accepted `LegacyEventAdapterConfig`, non-negative `start_sequence`, accepted `TraceExportConfig`, and explicit `pretty` bool;
- consume the caller-supplied legacy event iterable once through accepted `adapt_legacy_event_stream`;
- pass the adapted `RuntimeEvent` tuple unchanged to accepted `build_runtime_trace_document`;
- pass that document unchanged to accepted `build_runtime_trace_artifact`;
- immutable result preserves bridge config and the complete `RuntimeTraceArtifact` and validates record/sequence alignment;
- preserve adapter unknown/ambiguous policies, export empty/sequence policies, metadata, semantic-gap reporting, and exact artifact SHA semantics without reinterpretation.

Acceptance criteria:
- deterministic known-event artifact output and repeatability;
- unknown/ambiguous events retain accepted adapter policy behavior;
- empty stream follows accepted export empty policy;
- nonzero start sequence preserved exactly;
- one-pass source iterable is not consumed twice;
- no simulator state access, queue inspection/draining, file I/O, automatic hooks, new event mappings, semantic guessing, or schema changes;
- all prior tests/regressions remain green and production LIFO unchanged.

Protected: `sim/**`, existing runtime contracts/adapters/exports/loaders/comparators/divergence/Golden Replay packages, regression/search/bindings/data/fixtures.

Excluded: `BattleState.pending_events` capture lifecycle, automatic event hooks, trace file writes, Golden manifest changes, simulator semantics, video extraction, new HSR mechanics, FIFO/LIFO changes.

Validation uses the standard compile, full pytest, locked regression, and trace-evidence commands. Update `hsr_axis_sim/LUMEN_RESULT.md` after real CI.
