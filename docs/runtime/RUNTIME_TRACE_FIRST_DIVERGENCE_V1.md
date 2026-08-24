# Runtime Trace First Divergence Reporting v1

## Purpose

`hsr_axis_sim.runtime_divergence` is a read-only downstream sidecar that
consumes an existing `RuntimeTraceComparisonResult` from ARCH-005. It does not
compare traces itself.

Direction:

```text
RuntimeTraceComparisonResult
-> first non-MATCH record in existing order
-> first existing field difference when record status is MISMATCH
-> immutable structured report
-> deterministic text rendering
```

## Selection rule

ARCH-006 adds no new semantic priority. Selection is mechanical:

1. Traverse `comparison.records` in its existing tuple order.
2. Select the first record whose status is not `MATCH`.
3. If that record is `MISMATCH`, select `differences[0]` exactly as ordered by
   ARCH-005.
4. If that record is `EXPECTED_ONLY` or `ACTUAL_ONLY`, do not fabricate a field
   difference.
5. Ignore later divergences for first-divergence selection, while preserving
   `total_mismatch_count` so the report does not imply no later differences.

The reporter never invokes `compare_runtime_trace_documents`, never re-sorts
field differences, and never realigns records.

## Structured report

The report preserves:

- expected and actual trace IDs;
- expected and actual record counts;
- total mismatch count from ARCH-005;
- first divergent record index and status;
- expected/actual record reference when present;
- derived expected/actual sequence, event ID, and event type;
- first field difference for `MISMATCH` only;
- total field-difference count at the selected record.

A matching comparison returns `divergence=None` and
`total_mismatch_count=0`.

## Deterministic text rendering

Text output uses a fixed line order. Strings, booleans, nulls, arrays, and
objects are rendered with the existing canonical JSON serializer. Mapping keys
therefore remain deterministically ordered.

The literal token `ABSENT` is reserved for a value that is not present because a
record or field is missing. A present JSON null is rendered as `null`. Presence
flags for field differences remain explicit, so missing and present-null cannot
be confused.

`TRACE_MATCH` and `TRACE_DIVERGED` are the stable first-line outcome tokens.

## Explicit exclusions

ARCH-006 adds no:

- trace comparison or comparator modification;
- new field/record priority ranking;
- fuzzy equality, tolerance, rounding tolerance, or ignore rules;
- edit-distance, sequence-ID, event-ID, or heuristic realignment;
- repair, normalization, migration, deduplication, or renumbering;
- file I/O, report artifact schema/hash, persistence, or CLI;
- Golden Replay orchestration;
- simulator observation or automatic production wiring;
- new HSR mechanics, hidden values, or FIFO/LIFO semantic changes.

Golden Replay orchestration remains the next separate milestone after ARCH-006
is accepted.
