# Reference — Trace Document Loader and Integrity Validator

## Starting checkpoint

```text
HSR-RUNTIME-ARCH-003 — PASS
766/766 tests passed
locked regression 20/20 passed
trace-evidence-only 2/2 passed
```

ARCH-003 can emit an exact canonical `hsr_runtime_trace` document in compact or
pretty JSON form.

ARCH-004 performs the opposite boundary only:

```text
explicit bytes or explicit file
→ strict integrity validation
→ immutable RuntimeTraceDocument
→ RuntimeTraceArtifact preserving the exact source bytes
```

It does not compare two traces and does not repair malformed input.

## Exact accepted schema

```text
schema_name = hsr_runtime_trace
schema_version = 1.0
```

Only the exact ARCH-003 v1 document, record, and event fields are accepted.

For schema v1 every record must retain the ARCH-003 projection:

```text
action_context = null
attack_context = null
hit_context = null
numeric_values = {}
notes = []
```

A loader must not treat future context or numeric fields as valid v1 data.

## Explicit configuration

Required canonical-form policy:

```text
COMPACT_ONLY
PRETTY_ONLY
EITHER_CANONICAL
```

Required digest policy:

```text
REQUIRE_MATCH
VERIFY_IF_PROVIDED
SKIP
```

No policy has a default.

Digest coherence:

```text
REQUIRE_MATCH
→ expected_sha256 is required

VERIFY_IF_PROVIDED
→ expected_sha256 may be null
→ if present, it must match

SKIP
→ expected_sha256 must be null
```

`max_bytes` is mandatory and must be a positive integer.

## Validation order

```text
1. configuration
2. input byte type and size limit
3. SHA-256 policy
4. strict UTF-8 and no BOM
5. JSON parse with duplicate-key rejection
6. exact schema, field, enum, and primitive validation
7. immutable contract reconstruction
8. document-integrity validation
9. exact canonical compact/pretty comparison
```

The digest is computed over the original source bytes.

## JSON requirements

Reject:

```text
invalid UTF-8
UTF-8 BOM
NaN / Infinity / -Infinity
duplicate keys at any nesting level
non-object root
missing fields
extra fields
unknown enums
bool where integer is required
```

Python's default duplicate-key overwrite behavior is not acceptable.

## Document-integrity requirements

The loader must independently verify:

```text
record.sequence == record.event.sequence
all event IDs are unique
CONTIGUOUS or STRICTLY_INCREASING sequence policy
record_count
first_sequence / last_sequence
event_type_counts
semantic_gap_ids exact aggregate
```

The semantic-gap summary must equal the sorted unique union of validated:

```text
record.event.payload.adapter.semantic_gap_ids
```

No gap may be inferred from `CONTENT_DEFINED` alone.

## Canonicality

After reconstruction, generate both exact canonical forms using the existing
serializer.

Input is accepted only when it is byte-identical to one allowed form.

Reference hashes:

```text
compact:
d9a123ccc03b1eec9a816ec0d55bf024998d3b656b27fa4f807439d7e34ad6bd

pretty:
71fa9c77239c30c2aa694a2a8e16f84538b37e3191db4318cf20c09154834d8f
```

Equivalent JSON with different whitespace or key order is valid JSON but is not
a valid canonical trace artifact.

## Load result

The result should retain:

```text
RuntimeTraceArtifact
detected canonical form
digest status
expected SHA-256 or null
source byte size
```

The artifact's payload bytes must be the exact bytes that were supplied.

## File reading boundary

File reading must be explicit.

Requirements:

```text
existing regular file only
read-only binary access
max_bytes enforcement
no writes
no sidecars
no directory creation
no automatic file discovery
```

## Exclusions

Do not implement:

```text
trace repair
trace migration
future-version compatibility
expected-vs-actual comparison
first-divergence reporting
JSONL
append mode
automatic simulator observation
Action/Attack/Hit reconstruction
numeric extraction
formula execution
lifecycle binding
FIFO/LIFO changes
```
