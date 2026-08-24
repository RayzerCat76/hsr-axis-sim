# Runtime Trace Load and Integrity Validation v1

## Explicit boundary

`hsr_axis_sim.runtime_loaders` accepts only caller-supplied bytes or a
caller-specified existing file. It performs no discovery, observation, or
write. Its direction is:

```text
exact bytes or existing regular file
→ digest policy
→ strict UTF-8 and JSON
→ exact schema-v1 reconstruction
→ independent integrity checks
→ exact canonical-form check
→ immutable document and artifact retaining source bytes
```

Only `hsr_runtime_trace` schema version `1.0` is supported. Top-level, record,
and event objects require exact field sets. Version 1 records require null
Action/Attack/Hit contexts, an empty numeric-value object, and an empty notes
array. Unknown versions, enums, missing fields, and extra fields are rejected.

## Strict decoding and integrity

Input must be exact bytes within the explicit positive byte limit. UTF-8 is
decoded strictly; a BOM is forbidden. Duplicate object keys at any depth,
NaN, Infinity, -Infinity, malformed JSON, and a non-object root are rejected.

The loader independently checks record/event sequence equality, unique event
IDs, the selected contiguous or strictly-increasing sequence rule, counts,
boundaries, event-type counts, empty projection fields, and the exact sorted
semantic-gap union from `event.payload.adapter.semantic_gap_ids`. It never
infers a gap from an event type.

`REQUIRE_MATCH`, `VERIFY_IF_PROVIDED`, and `SKIP` are explicit digest policies.
The SHA-256 is always calculated over the original bytes. Compact-only,
pretty-only, or either-canonical form is also explicit. After immutable
reconstruction, the document is serialized through the existing canonical
serializer; source bytes must equal an allowed canonical form exactly.
Equivalent JSON with different whitespace or key order is rejected.

## File boundary and exclusions

File reading validates configuration before filesystem access, accepts only an
existing regular file, opens it read-only, and reads at most `max_bytes + 1`.
It creates no output, sidecar, or directory.

ARCH-004 performs no repair, normalization, migration, future-version
compatibility, expected-vs-actual comparison, divergence reporting, JSONL,
append, simulator observation, context reconstruction, numeric extraction,
lifecycle binding, or FIFO/LIFO change. Simulator, adapter, contract, and
exporter behavior remain unchanged.
