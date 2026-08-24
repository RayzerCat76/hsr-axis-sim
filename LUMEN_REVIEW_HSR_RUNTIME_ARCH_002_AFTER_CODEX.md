# LUMEN_REVIEW_HSR_RUNTIME_ARCH_002_AFTER_CODEX

## Decision

**PARTIAL — fixes required**

## Task

- Task ID: `HSR-RUNTIME-ARCH-002`
- Title: Event Envelope Adapter Bridge
- Review date: 2026-07-12
- Reviewer: Luman

## What passed

### Compilation

```bash
python -m compileall -q hsr_axis_sim
```

Result: **PASS**

### Focused ARCH-002 tests

```text
27 / 27 passed in 0.22s
```

### Complete test collection

All 56 test files were run in non-overlapping groups.

Result:

```text
743 passed
2 failed
745 total
```

The two failures are both in:

```text
hsr_axis_sim/tests/test_runtime_research_artifacts.py
```

Failure cause:

```text
ARCH-001 research baseline files are missing from the submitted package.
```

### Locked regression

```text
PASS 20 / 20
```

### Trace-evidence-only regression

```text
PASS 2 / 2
```

### ARCH-002 reference integrity

```text
6d28569b81c11c6620c6bb69984e3cf9da1162f2169fc4b1022198519abbb7fe
docs/runtime/research/REFERENCE_LEGACY_EVENT_SURFACE_HSR_RUNTIME_ARCH_002.md

97142cfc8e8834c99f53ae9bf133e73b723e96fefe30b9c4649c92304e2d4b19
docs/runtime/research/REFERENCE_LEGACY_EVENT_SURFACE_HSR_RUNTIME_ARCH_002.json
```

### Adapter semantics

Confirmed:

- exactly seven immutable mappings;
- six `CONFIRMED + BOUND` mappings;
- `unit_defeated` remains `UNKNOWN + UNRESOLVED`;
- `unit_defeated` maps only to `CONTENT_DEFINED`;
- `killer_id` stays only in raw legacy payload;
- unknown and ambiguous policies have no default;
- no Action/Attack/Hit contexts are inferred;
- deterministic IDs use `legacy:{stream_id}:{sequence}`;
- raw nested payloads are defensively frozen;
- no production module imports `runtime_adapters`;
- existing LIFO behavior remains unchanged.

## Required fix 1 — restore deleted ARCH-001 artifacts

Compared with the accepted `hsr_axis_001a_package(1).zip`, the submitted package
deleted five existing files:

```text
docs/runtime/ARCHITECTURE_CONTRACT_V1.md
docs/runtime/UNRESOLVED_SEMANTICS_V1.json
docs/runtime/research/HSR_RUNTIME_FRAMEWORK_BASELINE_V1_0.md
docs/runtime/research/HSR_RUNTIME_FORMULA_REGISTRY_V1_0.json
docs/runtime/research/HSR_RUNTIME_DEFENSE_TOUGHNESS_PRECISION_MODEL_V1_0.json
```

Required exact SHA-256 values:

```text
7665b8214cdd8ad12f23735b2ad4e214d33b3feafd74d2b4199a71826bdd0539  docs/runtime/ARCHITECTURE_CONTRACT_V1.md
70b2e84706bf6fcb0c5e59a0d10fc0f223c5b217c8c2535595fb3c3884150bf5  docs/runtime/UNRESOLVED_SEMANTICS_V1.json
cf6b94fb29ce8ca2cf5e0dbcd125c87a65c026304bf8c68dfdd0a4e7b9074817  docs/runtime/research/HSR_RUNTIME_FRAMEWORK_BASELINE_V1_0.md
7adaeb30b38c70c9c32de39925561abdf64ef1415e9fdd57b56026feca6912d9  docs/runtime/research/HSR_RUNTIME_FORMULA_REGISTRY_V1_0.json
cf3e46a7a0a12db73f30bc96837a143061e1a012d66384c43eb20685d6a223b3  docs/runtime/research/HSR_RUNTIME_DEFENSE_TOUGHNESS_PRECISION_MODEL_V1_0.json
```

Restoring these five files in an isolated review copy immediately changed the
affected preservation/research tests to:

```text
6 / 6 passed
```

No regeneration is needed. Restore byte-for-byte.

## Required fix 2 — validate config for an empty stream

Current behavior:

```python
adapt_legacy_event_stream([], start_sequence=0, config=object())
```

returns:

```python
()
```

because `config` is validated only when at least one event reaches
`adapt_legacy_event()`.

The stream adapter should validate `config` at function entry, before consuming
the iterable, so invalid configuration is rejected even for an empty stream.

Expected controlled result:

```text
LegacyEventSchemaError
```

Add a focused regression test for this boundary.

## Preservation result

Compared byte-for-byte with the accepted ARCH-001 package:

- expected ARCH-002 files were added;
- `hsr_axis_sim/LUMEN_RESULT.md` changed;
- no existing production source file changed;
- no existing test file changed;
- five ARCH-001 documents were deleted.

The deletion violates ARCH-002's additions-only and preservation criteria.

## Final status

ARCH-002 implementation is substantially correct, but the submitted package is
not acceptable until:

1. the five ARCH-001 files are restored byte-for-byte;
2. empty-stream config validation is added;
3. the complete test collection passes;
4. locked regression remains 20/20.

Do not start ARCH-003.
