# Reference — Read-Only Runtime Trace Export for HSR-RUNTIME-ARCH-003

## Starting boundary

Accepted starting package:

```text
hsr_axis_001a_package(4).zip
```

Confirmed baseline:

```text
HSR-RUNTIME-ARCH-002 — PASS
746/746 tests passed
locked regression 20/20 passed
trace-evidence-only 2/2 passed
```

`runtime_contracts` already defines:

```text
RuntimeEvent
RuntimeTraceRecord
TraceNumericValue
canonical_json_bytes
```

`runtime_adapters` already provides a manual, one-way conversion:

```text
legacy Event
→ immutable RuntimeEvent
```

ARCH-003 begins only after that boundary.

## Allowed direction

```text
Iterable[RuntimeEvent]
→ tuple[RuntimeTraceRecord]
→ immutable RuntimeTraceDocument
→ deterministic JSON bytes
→ optional explicitly requested file write
```

The exporter must never read, clear, mutate, subscribe to, or hook:

```text
BattleState.pending_events
BattleState.emit_event
legacy trigger dispatch
```

The caller may manually pass the immutable RuntimeEvents created by ARCH-002.

## Trace record projection

Each RuntimeEvent becomes exactly one RuntimeTraceRecord:

```text
record.sequence = event.sequence
record.event = event
record.action_context = null
record.attack_context = null
record.hit_context = null
record.numeric_values = {}
record.notes = []
```

ARCH-003 must not reconstruct hierarchy that ARCH-002 intentionally left
unknown.

It must also not convert legacy `amount`, `formula_parts`, HP, Shield,
Toughness, Energy, or AV values into `TraceNumericValue`. Quantization and raw
numeric semantics remain unresolved.

## Required document shape

```text
schema_name = hsr_runtime_trace
schema_version = 1.0
trace_id
sequence_policy
record_count
first_sequence
last_sequence
event_type_counts
semantic_gap_ids
records
metadata
```

`event_type_counts` uses stable RuntimeEventType string values.

`semantic_gap_ids` is the sorted unique union of validated
`payload.adapter.semantic_gap_ids` values. Events with no adapter metadata
contribute no semantic gaps.

If an `adapter` object exists but `semantic_gap_ids` is malformed, export must
fail with a controlled schema error rather than silently ignoring it.

## Explicit policies

No defaults:

```text
TraceSequencePolicy:
  CONTIGUOUS
  STRICTLY_INCREASING

EmptyTracePolicy:
  ALLOW
  REJECT
```

The exporter preserves original sequence numbers and never renumbers events.

`CONTIGUOUS` requires:

```text
next.sequence = previous.sequence + 1
```

`STRICTLY_INCREASING` requires:

```text
next.sequence > previous.sequence
```

Duplicate event IDs are rejected in both modes.

## Deterministic artifact

Compact and pretty JSON are both canonical:

```text
UTF-8
ensure_ascii = false
sort_keys = true
no NaN or Infinity
compact separators for compact mode
2-space indentation plus final newline for pretty mode
```

The artifact SHA-256 is computed over the exact exported bytes. It is not
embedded into the document, avoiding self-referential hashing.

Reference sample:

```text
compact SHA-256:
d9a123ccc03b1eec9a816ec0d55bf024998d3b656b27fa4f807439d7e34ad6bd

pretty SHA-256:
71fa9c77239c30c2aa694a2a8e16f84538b37e3191db4318cf20c09154834d8f
```

## File output

File writing is an explicit boundary call.

Required behavior:

```text
overwrite = false → fail if target exists
overwrite = true  → replace exact target contents
```

The writer must not invent a default overwrite policy.

It must not create or modify any simulator or fixture file automatically.

## Explicit exclusions

Do not implement:

```text
trace loading
trace parsing
trace validation from disk
first-divergence comparison
JSONL
streaming append
automatic battle observation
Action/Attack/Hit reconstruction
numeric extraction
formula execution
lifecycle binding
LIFO/FIFO changes
```
