# HSR-AXIS-001E — Strict Golden Replay Manifest Artifact

## Status

PASS — proceed

## Implementation summary

- Added downstream package `hsr_axis_sim.runtime_golden_manifests`.
- Added fixed schema `hsr_golden_replay_manifest` version `1.0`.
- Added deterministic compact canonical UTF-8 JSON serialization of accepted `GoldenReplayBatchPlan` values.
- Added immutable `GoldenReplayManifestArtifact` with exact payload bytes, byte count, plan, and SHA-256 identity.
- Added strict byte loading with explicit positive size limit and optional expected SHA-256 verification.
- Added duplicate-key, invalid UTF-8/JSON, non-standard constant, exact field-set, schema name/version, and canonical-byte enforcement.
- Reconstructed case semantics through accepted `GoldenReplayValidationConfig`, `GoldenReplayFileCase`, and `GoldenReplayBatchPlan` contracts.
- Equivalent but differently formatted JSON is rejected rather than normalized.
- Added decision D-014: Golden manifest v1 uses one exact compact canonical byte representation.

## Files added

- `LUMEN_TASK_HSR_AXIS_001E.md`
- `docs/runtime/GOLDEN_REPLAY_MANIFEST_V1.md`
- `hsr_axis_sim/runtime_golden_manifests/__init__.py`
- `hsr_axis_sim/runtime_golden_manifests/model.py`
- `hsr_axis_sim/runtime_golden_manifests/codec.py`
- `hsr_axis_sim/tests/test_runtime_golden_manifest_artifact.py`
- `hsr_axis_sim/tests/test_hsr_axis_001e_preservation.py`

## Files modified

- `docs/DECISION_LOG.md`
- `docs/HSR_AXIS_SIM_MASTER_BIBLE.md`
- `hsr_axis_sim/LUMEN_RESULT.md`

No existing production simulator, runtime trace layer, Golden Replay validator/case/batch layer, regression, search, binding, data, or locked fixture executable behavior was modified.

## Tests added

Manifest tests cover deterministic build/SHA, strict load/round-trip/order, noncanonical whitespace and pretty JSON rejection, duplicate keys, invalid JSON/UTF-8/NaN, digest mismatch, size limit, API input validation, exact top-level/case schemas, unsupported policies, invalid downstream path/config contracts, empty batches, duplicate replay IDs, invalid batch ID, and artifact immutability.

Preservation tests confirm the manifest layer is downstream-only, reconstructs accepted contracts without batch execution, and preserves production LIFO behavior.

## Exact validation commands and real results

GitHub Actions workflow: `HSR Axis Sim Validation`, PR #8, run #25, job `validate` (`97333338060`).

1. `python -m compileall -q hsr_axis_sim` — PASS.
2. `python -m pytest -q` — PASS: `866 passed in 7.32s`.
3. Locked regression runner — PASS `20/20` total checks: 12/12 golden replays, 2/2 manual, 2/2 search, 2/2 action-sequence, 2/2 trace evidence.
4. Trace-evidence-only runner — PASS `2/2`.

## Warnings / errors

- No compile, test, or regression errors.
- Existing GitHub Actions Node.js 20 deprecation warning remains nonblocking and unrelated to manifest correctness.

## Acceptance review

- Manifest byte identity is deterministic and SHA-addressed.
- The v1 parser is strict and non-permissive: duplicate/unknown/missing fields and alternate encodings are rejected.
- Case order is preserved exactly.
- Existing config/path/batch validation is reused rather than reimplemented.
- No file I/O or batch execution was introduced early.
- No repair, migration, defaults, metadata extension, simulator auto-run, video extraction, new HSR mechanics, or FIFO/LIFO change was introduced.
- Existing production LIFO behavior remains unchanged.

## Unresolved issues

None blocking HSR-AXIS-001E acceptance.

Existing unresolved HSR game semantics remain tracked separately and were not changed.

## Suggested next milestone

`HSR-AXIS-001F — Base-bounded Golden Replay Manifest File Loader`

001F should add one explicit base-bounded manifest file path and bounded raw read before delegating exact bytes to the accepted 001E loader. It should not execute the batch yet.
