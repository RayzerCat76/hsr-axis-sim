# HSR-RUNTIME-ARCH-004 — Trace Document Loader and Integrity Validator

## Status

BLOCKED

Implementation, strict reference/tamper validation, compilation, preservation,
round-trip checks, and regressions pass. Final PASS is blocked because `python`
and pytest are unavailable and the workspace has no Git metadata. No dependency
was installed.

## Implementation summary

- Added a standard-library-only `hsr_axis_sim.runtime_loaders` sidecar.
- Added mandatory canonical-form and digest policies plus frozen config/result
  models and controlled loader-specific errors.
- Added strict JSON decoding with nested duplicate-key and non-finite rejection.
- Added exact schema-v1 reconstruction for RuntimeEvent, RuntimeTraceRecord,
  RuntimeTraceDocument, and RuntimeTraceArtifact.
- Added independent sequence, identity, count, boundary, projection, and
  semantic-gap integrity validation.
- Added ordered digest, UTF-8/BOM, JSON, schema, integrity, and canonicality
  checks while retaining exact source bytes.
- Added explicit bounded read-only file loading, deterministic schema/docs, and
  six focused test files.

## Files added

- `hsr_axis_sim/runtime_loaders/__init__.py`
- `hsr_axis_sim/runtime_loaders/enums.py`
- `hsr_axis_sim/runtime_loaders/model.py`
- `hsr_axis_sim/runtime_loaders/json_decode.py`
- `hsr_axis_sim/runtime_loaders/validation.py`
- `hsr_axis_sim/runtime_loaders/trace_load.py`
- `hsr_axis_sim/runtime_loaders/files.py`
- `docs/runtime/RUNTIME_TRACE_LOAD_VALIDATE_V1.md`
- `docs/runtime/RUNTIME_TRACE_LOAD_SCHEMA_V1.json`
- `docs/runtime/research/REFERENCE_RUNTIME_TRACE_LOAD_VALIDATE_HSR_RUNTIME_ARCH_004.md`
- `docs/runtime/research/REFERENCE_RUNTIME_TRACE_LOAD_VALIDATE_HSR_RUNTIME_ARCH_004.json`
- `hsr_axis_sim/tests/test_runtime_trace_loader_model.py`
- `hsr_axis_sim/tests/test_runtime_trace_loader_json.py`
- `hsr_axis_sim/tests/test_runtime_trace_loader_validation.py`
- `hsr_axis_sim/tests/test_runtime_trace_loader_bytes.py`
- `hsr_axis_sim/tests/test_runtime_trace_loader_file.py`
- `hsr_axis_sim/tests/test_runtime_arch_004_preservation.py`

The two supplied reference files were already at their final paths and were
retained byte-for-byte without rewriting.

## File modified

- `hsr_axis_sim/LUMEN_RESULT.md` only.

## Tests added

- Exact enums, mandatory/coherent config, digest syntax, max-byte validation,
  frozen config/result, and result consistency.
- Strict JSON roots, malformed JSON, all non-finite constants, and duplicate
  keys at top-level and nested levels.
- Exact document/record/event fields, schema/version/enums/primitives,
  projection constraints, sequences, duplicate IDs, counts, boundaries, and
  semantic-gap integrity.
- Digest-policy matrix, compact/pretty policy matrix, noncanonical rejection,
  size/type/UTF-8/BOM behavior, source-byte identity, and exporter round-trip.
- Explicit read-only compact/pretty file loading, missing/directory/overflow
  errors, config-first behavior, byte preservation, and no sidecars.
- Exact ARCH-004 reference hashes, all prior docs, unchanged accepted sidecar
  hashes, no protected imports, and unchanged LIFO behavior.

## Commands and real results

1. `python -m compileall -q hsr_axis_sim`
   - BLOCKED: `zsh: command not found: python`.
2. `python3 -m compileall -q hsr_axis_sim`
   - PASS, no output, `0.12s real` on final run.
3. Focused pytest command for all six ARCH-004 test files
   - BLOCKED before collection: `python` is unavailable.
4. `python3 -m pytest -q` with all six focused files
   - BLOCKED before collection: `/usr/local/bin/python3: No module named pytest`.
5. Complete `python -m pytest -q`
   - BLOCKED before collection: `python` is unavailable.
6. Supplied reference canonical/tamper harness
   - PASS 2/2 canonical samples and PASS 19/19 tamper cases with their exact
     expected controlled error classes.
7. Direct digest/canonical/file/exporter-round-trip harness
   - PASS: all digest modes, canonical policies, size/type ordering, bounded
     read-only files, exact source bytes, and reconstructed content.
8. `python3 -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --format text`
   - PASS 20/20 in `0.11s real`: 12/12 replays, 2/2 manual, 2/2 scenarios,
     2/2 action-sequence, and 2/2 trace-evidence checks.
9. `python3 -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --only trace_evidence --format text`
   - PASS 2/2 in `0.07s real`.
10. Required ARCH-004 reference `sha256sum`
    - PASS; exact hashes below.
11. `git diff --check`
    - BLOCKED: workspace is not a Git repository.
12. Preservation/static harness
    - PASS: 14/14 accepted contract/adapter/export source hashes unchanged,
      13/13 prior ARCH documents present, zero protected imports of
      `runtime_loaders`, and 15 new files passed whitespace/conflict checks.

Focused and complete pytest totals/timings are unavailable because collection
could not start. The supplied independent starting baseline is 766/766; it is
not reported as a new local execution.

## Reference and sample hashes

- `REFERENCE_RUNTIME_TRACE_LOAD_VALIDATE_HSR_RUNTIME_ARCH_004.md`:
  `09734938828c8cc44e0d9cd776b9ec8738ae39dd7a4d62a0df714c646bce5241`
- `REFERENCE_RUNTIME_TRACE_LOAD_VALIDATE_HSR_RUNTIME_ARCH_004.json`:
  `548313a263f05891b432b51d5833009341f481291f8a30d3a96108f24fcef4f4`
- Valid compact sample:
  `d9a123ccc03b1eec9a816ec0d55bf024998d3b656b27fa4f807439d7e34ad6bd`
- Valid pretty sample:
  `71fa9c77239c30c2aa694a2a8e16f84538b37e3191db4318cf20c09154834d8f`

## Contract and preservation confirmation

- Duplicate JSON keys at every depth, non-finite constants, BOM, invalid UTF-8,
  unknown schemas/enums, and equivalent but noncanonical JSON are rejected.
- Only exact `hsr_runtime_trace` schema version `1.0` is accepted.
- Source bytes are retained unchanged in the reconstructed artifact; no hash is
  embedded or rewritten.
- Schema-v1 contexts remain null and numeric values/notes remain empty.
- No repair, normalization, migration, renumbering, deduplication, comparison,
  divergence reporting, future-version compatibility, JSONL, append, automatic
  discovery/observation, simulator access, context reconstruction, numeric
  extraction, lifecycle binding, or FIFO/LIFO change was introduced.
- No existing production, runtime contract, adapter, exporter, test,
  documentation, manifest, fixture, README, or 002Q-FIX file changed.
- All prior ARCH-001/002/003 accepted documents remain present.

## Unresolved issues

- Focused and complete pytest require an environment that provides pytest.
- `git diff --check` requires the missing Git metadata.

## Suggested next milestone

`HSR-RUNTIME-ARCH-005 — Expected vs Actual Trace Comparator`

ARCH-005 was not started.
