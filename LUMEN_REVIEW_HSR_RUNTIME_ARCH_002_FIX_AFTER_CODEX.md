# LUMEN_REVIEW_HSR_RUNTIME_ARCH_002_FIX_AFTER_CODEX

## Decision

**PARTIAL — fixes required**

## Task reviewed

- Task ID: `HSR-RUNTIME-ARCH-002-FIX`
- Review date: 2026-07-12
- Submitted package: `hsr_axis_001a_package(3).zip`
- Reviewer: Luman

## Fixes that passed

### Empty-stream configuration validation

`adapt_legacy_event_stream()` now validates `LegacyEventAdapterConfig` before
validating `start_sequence` or consuming the iterable.

Confirmed behavior:

```python
adapt_legacy_event_stream([], start_sequence=0, config=object())
```

raises:

```text
LegacyEventSchemaError
```

The new single-pass-iterable test also confirms zero iterations occur when
configuration is invalid.

### ARCH-001 artifact restoration

The five previously missing ARCH-001 files are restored and match the required
SHA-256 values:

```text
7665b8214cdd8ad12f23735b2ad4e214d33b3feafd74d2b4199a71826bdd0539
docs/runtime/ARCHITECTURE_CONTRACT_V1.md

70b2e84706bf6fcb0c5e59a0d10fc0f223c5b217c8c2535595fb3c3884150bf5
docs/runtime/UNRESOLVED_SEMANTICS_V1.json

cf6b94fb29ce8ca2cf5e0dbcd125c87a65c026304bf8c68dfdd0a4e7b9074817
docs/runtime/research/HSR_RUNTIME_FRAMEWORK_BASELINE_V1_0.md

7adaeb30b38c70c9c32de39925561abdf64ef1415e9fdd57b56026feca6912d9
docs/runtime/research/HSR_RUNTIME_FORMULA_REGISTRY_V1_0.json

cf3e46a7a0a12db73f30bc96837a143061e1a012d66384c43eb20685d6a223b3
docs/runtime/research/HSR_RUNTIME_DEFENSE_TOUGHNESS_PRECISION_MODEL_V1_0.json
```

## Submitted-package test results

### Compilation

```text
PASS
```

### Focused tests

```text
28 passed / 2 failed
```

### Complete tests

All 56 test files were executed in non-overlapping groups.

```text
744 passed / 2 failed / 746 total
```

Both failures are caused only by missing ARCH-002 documentation/reference
files:

```text
docs/runtime/LEGACY_EVENT_MAPPING_V1.json
docs/runtime/research/REFERENCE_LEGACY_EVENT_SURFACE_HSR_RUNTIME_ARCH_002.md
```

The related companion files are also missing:

```text
docs/runtime/LEGACY_EVENT_ADAPTER_V1.md
docs/runtime/research/REFERENCE_LEGACY_EVENT_SURFACE_HSR_RUNTIME_ARCH_002.json
```

### Locked regression

```text
PASS 20/20
```

### Trace-evidence-only regression

```text
PASS 2/2
```

## Difference from the previous ARCH-002 package

Compared with `hsr_axis_001a_package(2).zip`, the submitted package contains
only the intended code/test change plus report/handoff files, but deletes these
four existing ARCH-002 artifacts:

```text
docs/runtime/LEGACY_EVENT_ADAPTER_V1.md
docs/runtime/LEGACY_EVENT_MAPPING_V1.json
docs/runtime/research/REFERENCE_LEGACY_EVENT_SURFACE_HSR_RUNTIME_ARCH_002.md
docs/runtime/research/REFERENCE_LEGACY_EVENT_SURFACE_HSR_RUNTIME_ARCH_002.json
```

Required hashes:

```text
4fbab876c3263c7bc0a6ef7ea9a890a9007f5da7b7974feba9448695f05ea958  docs/runtime/LEGACY_EVENT_ADAPTER_V1.md
c9a1ee54ea358cebebf205b20e55818ac5e935d80352e2fc0172d7ac659ffb39  docs/runtime/LEGACY_EVENT_MAPPING_V1.json
6d28569b81c11c6620c6bb69984e3cf9da1162f2169fc4b1022198519abbb7fe  docs/runtime/research/REFERENCE_LEGACY_EVENT_SURFACE_HSR_RUNTIME_ARCH_002.md
97142cfc8e8834c99f53ae9bf133e73b723e96fefe30b9c4649c92304e2d4b19  docs/runtime/research/REFERENCE_LEGACY_EVENT_SURFACE_HSR_RUNTIME_ARCH_002.json
```

## Isolated restoration verification

After copying those four exact files into an isolated review copy:

```text
focused adapter/research tests: 30/30 passed
exact affected full-suite group: 80/80 passed
```

Combining the already completed non-overlapping groups gives:

```text
746/746 passed
```

This confirms no further code change is required.

## Preservation review

Confirmed:

- no `sim/**` change;
- no `runtime_contracts/**` change;
- no mapping change;
- `unit_defeated` remains unresolved;
- no automatic production hook;
- no LIFO/FIFO change;
- no Action/Attack/Hit inference;
- locked regression remains green.

## Final requirement

Restore the four missing ARCH-002 files byte-for-byte and rebuild the submitted
ZIP without deleting any previously accepted files.

Do not modify code or tests again.

Do not start ARCH-003.
