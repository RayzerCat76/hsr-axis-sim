# Golden Replay Manifest-backed Batch Run V1

## Status

HSR-AXIS-001G contract.

## Purpose

Compose the accepted HSR-AXIS-001F manifest-file boundary with the accepted HSR-AXIS-001D deterministic Golden Replay batch runner under one explicit common base directory.

## Input

The runner receives:

- one accepted `GoldenReplayManifestFileSpec`;
- one explicit `base_directory`.

No manifest discovery or implicit working-directory lookup is performed.

## Composition order

Execution is strictly:

1. call HSR-AXIS-001F `load_golden_replay_manifest_file` with the supplied spec and base directory;
2. take the exact reconstructed `manifest_load.artifact.plan`;
3. call HSR-AXIS-001D `run_golden_replay_batch` with that plan and the resolved absolute `manifest_load.base_directory`.

The composition layer does not reload manifest bytes, reconstruct cases itself, or reinterpret comparison/batch semantics.

## Common base directory

The resolved base directory returned by HSR-AXIS-001F is authoritative for the batch execution. Therefore:

- the manifest file is resolved under that base;
- every expected/actual replay file path reconstructed from the manifest is resolved under the same base through HSR-AXIS-001C/001D;
- returned results must prove exact base-directory alignment.

## Result

`GoldenReplayManifestBatchRunResult` is immutable and contains:

- the complete `GoldenReplayManifestFileLoadResult`;
- the complete `GoldenReplayBatchResult`.

Construction rejects any result whose batch plan differs from the loaded manifest plan or whose batch base directory differs from the manifest load base directory.

## Failure semantics

- Manifest file/path/digest/schema/canonicality failures propagate before batch execution begins.
- Replay comparison mismatches are completed batch results and do not stop later cases, exactly as defined by HSR-AXIS-001D.
- Operational replay failures propagate immediately and no partial composition result is returned.

## Text rendering

The deterministic renderer emits one composition PASS/FAIL line, then wraps the accepted HSR-AXIS-001F manifest-file text and accepted HSR-AXIS-001D batch text in fixed order.

## Explicit non-goals

HSR-AXIS-001G does not add:

- manifest scanning/discovery;
- simulator-generated actual artifacts;
- retry, parallelism, or partial-error aggregation;
- repair, migration, defaults, or alternate manifest schema handling;
- CLI/UI or video extraction;
- new HSR mechanics or FIFO/LIFO changes.
