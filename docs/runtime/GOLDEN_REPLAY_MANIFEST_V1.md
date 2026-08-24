# Golden Replay Manifest Artifact V1

`HSR-AXIS-001E` defines a strict deterministic JSON artifact for an accepted `GoldenReplayBatchPlan`.

## Identity

- `schema_name`: `hsr_golden_replay_manifest`
- `schema_version`: `1.0`
- encoding: UTF-8
- byte form: compact canonical JSON only
- artifact identity: SHA-256 of exact manifest bytes

No pretty form is accepted in v1.

## Exact schema

Top-level fields are exactly:
- `schema_name`
- `schema_version`
- `batch_id`
- `cases`

Each ordered case object has exactly:
- `replay_id`
- `expected_sha256`
- `expected_relative_path`
- `actual_relative_path`
- `canonical_form_policy`
- `max_bytes`

Unknown and missing fields are rejected. Duplicate JSON object keys and non-standard JSON constants such as `NaN` are rejected.

## Reconstruction

The loader does not create a parallel semantic model. Each case is reconstructed through the already accepted:
- `GoldenReplayValidationConfig`;
- `GoldenReplayFileCase`;
- `GoldenReplayBatchPlan`.

Therefore SHA format, canonical-form policy, byte limits, relative path rules, non-empty batch rules, ordered case semantics, and unique replay IDs reuse the accepted contracts.

## Canonicality

After strict JSON/schema validation, the reconstructed plan is serialized again through the deterministic canonical JSON helper. Input bytes must exactly equal those reconstructed compact canonical bytes. Whitespace changes, pretty formatting, alternate key order, trailing newlines, or other equivalent-but-different encodings are rejected rather than normalized.

## Digest and size

`load_golden_replay_manifest_bytes` requires an explicit positive `max_bytes`. An optional expected SHA-256 may be supplied; when supplied, the exact input bytes must match it before decoding.

`GoldenReplayManifestArtifact` preserves the reconstructed plan, exact payload bytes, byte count, and computed SHA-256.

## Scope boundary

V1 performs no file I/O, batch execution, directory discovery, repair, migration, default insertion, metadata extension, simulator auto-run, CLI/UI, video extraction, fuzzy comparison, new HSR mechanics, or FIFO/LIFO changes.
