# Runtime Trace Expected-vs-Actual Comparison v1

## Purpose

`hsr_axis_sim.runtime_comparators` is a read-only sidecar that compares two
already-constructed `RuntimeTraceDocument` values deterministically. It does
not load files, validate raw bytes, observe the simulator, repair traces, or
report a selected first divergence.

Direction:

```text
expected RuntimeTraceDocument + actual RuntimeTraceDocument
-> ordered record-by-record exact comparison
-> immutable RuntimeTraceComparisonResult
-> [ARCH-006 may later select/format the first divergence]
```

## Comparison projection

The comparison axis is exactly `RuntimeTraceDocument.records`, aligned by tuple
position. Every field of each `RuntimeTraceRecord` is converted through the
existing canonical-data projection and compared recursively and strictly.
JSON values with different Python JSON types remain different; for example,
`1` and `1.0` are not treated as equal.

The following document wrapper fields are not independent comparison axes:

- `trace_id` and `metadata` are provenance;
- `sequence_policy` is the validation policy under which the document was built;
- `record_count`, `first_sequence`, `last_sequence`, `event_type_counts`, and
  `semantic_gap_ids` are validated projections of the record stream.

Expected and actual trace IDs are retained in the result for provenance, and
record counts are retained to make length differences explicit.

## Alignment and difference rules

Comparison is position-by-position only. ARCH-005 does not use edit distance,
sequence-ID matching, event-ID matching, look-ahead, or any heuristic
realignment. If a record is inserted or removed in the middle, later positional
differences remain visible rather than being silently repaired.

For positions present on both sides:

- `MATCH` means no recursive field difference;
- `MISMATCH` contains every deterministic field difference for that position.

For unpaired tail positions:

- `EXPECTED_ONLY` means the expected trace has a record and actual does not;
- `ACTUAL_ONLY` means the actual trace has a record and expected does not.

Nested field differences use deterministic JSON-pointer-style paths. `~` is
escaped as `~0` and `/` as `~1`. Difference values are deeply frozen.

## Determinism and immutability

The result and all comparison records/differences are frozen dataclasses.
Mapping keys are traversed in sorted order and list elements in index order, so
the same inputs produce equal ordered results. Inputs are never modified.

## Explicit exclusions

ARCH-005 adds no:

- numeric tolerance, rounding tolerance, fuzzy equality, or configurable ignore list;
- trace repair, normalization, deduplication, renumbering, or realignment;
- file I/O, JSON output format, comparison artifact hash, or CLI;
- automatic simulator integration or observation;
- game-semantic inference or hidden HSR values;
- first-divergence selection, prioritization, prose formatting, or reporting;
- change to runtime trace schema v1, loader/exporter behavior, production LIFO,
  or unresolved actual HSR FIFO/LIFO semantics.

First-divergence selection/reporting remains reserved for
`HSR-RUNTIME-ARCH-006`.
