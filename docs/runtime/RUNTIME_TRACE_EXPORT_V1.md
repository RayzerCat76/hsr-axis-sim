# Runtime Trace Export v1

## Manual read-only boundary

`hsr_axis_sim.runtime_exports` accepts only an explicitly supplied iterable of
immutable `RuntimeEvent` objects. Its direction is:

```text
Iterable[RuntimeEvent]
→ RuntimeTraceRecord per event
→ immutable RuntimeTraceDocument
→ deterministic UTF-8 JSON bytes and SHA-256
→ optional explicit file write
```

It does not read `BattleState`, inspect or clear `pending_events`, hook
`emit_event`, subscribe to battles, or alter production dispatch. The active
simulator, ARCH-002 adapter, runtime contracts, and existing LIFO behavior are
unchanged.

## Document and record projection

The fixed document identity is `hsr_runtime_trace` version `1.0`. A document
records its caller-supplied trace ID and metadata, sequence policy, record
count, first/last sequence, event-type counts, sorted semantic gaps, and an
ordered tuple of records.

Each event produces exactly one record containing the original event object
and its original sequence. Action, Attack, and Hit contexts are always null;
numeric values and notes are always empty. Legacy `amount`, `formula_parts`,
HP, Shield, Toughness, Energy, and AV values are not extracted or quantized.

`CONTIGUOUS` requires every next sequence to equal the previous sequence plus
one. `STRICTLY_INCREASING` permits gaps but requires every next sequence to be
greater. Original sequences are never renumbered. Empty traces require an
explicit `ALLOW` or `REJECT` policy, and duplicate event IDs are rejected.

Semantic gaps come only from validated
`event.payload.adapter.semantic_gap_ids`. A malformed adapter object or gap
sequence fails export. The global document value is the sorted unique union;
no gap is inferred from an event type or legacy payload.

## Bytes, digest, and files

Compact and two-space-indented pretty output both use the existing canonical
serializer; pretty output ends with a newline. SHA-256 is lowercase hexadecimal
over those exact bytes and is not embedded in the document.

Writing occurs only through `write_runtime_trace_artifact`, with an explicit
boolean overwrite policy. Its parent directory must already exist. It writes
only the requested file and creates no hash sidecar or directories.

ARCH-003 provides no trace loader, parser, external schema validator,
comparison, first-divergence analysis, JSONL/append writer, replay validation,
automatic observation, hierarchy reconstruction, lifecycle binding, or
numeric conversion.
