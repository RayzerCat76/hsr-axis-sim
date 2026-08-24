# Golden Replay Manifest File Boundary V1

## Status

HSR-AXIS-001F contract.

## Purpose

Provide one explicit filesystem boundary for a reviewed HSR-AXIS-001E Golden Replay manifest artifact without executing its reconstructed batch plan.

## Input

`GoldenReplayManifestFileSpec` is immutable and contains:

- `manifest_relative_path`: non-empty canonical relative POSIX path;
- `max_bytes`: positive integer read/manifest limit;
- `expected_sha256`: optional exact 64-character lowercase SHA-256.

Loading also requires one explicit `base_directory`.

## Path rules

The manifest path:

- must be relative;
- must use `/` separators;
- must not contain `.` or `..` segments;
- must already be in canonical `PurePosixPath.as_posix()` form;
- is resolved beneath the resolved base directory;
- must remain beneath that base after symlink resolution;
- must resolve to a regular file.

No working-directory discovery or directory scanning is performed.

## Read and manifest semantics

The loader reads at most `max_bytes + 1` bytes from the explicit file. The exact bytes are then passed unchanged to HSR-AXIS-001E `load_golden_replay_manifest_bytes` with the same `max_bytes` and optional expected digest.

Therefore schema, duplicate-key, UTF-8, JSON, canonicality, downstream contract, size, and digest semantics remain exclusively owned by HSR-AXIS-001E. HSR-AXIS-001F does not normalize or repair manifest bytes.

## Output

`GoldenReplayManifestFileLoadResult` is immutable and preserves:

- the exact file spec;
- resolved absolute base-directory provenance;
- resolved absolute manifest-file provenance;
- the complete accepted `GoldenReplayManifestArtifact`.

The deterministic text renderer reports only file/artifact provenance, batch ID, and case count.

## Explicit non-goals

HSR-AXIS-001F does not:

- execute the reconstructed Golden Replay batch;
- execute individual replay cases;
- scan or discover manifests;
- add manifest defaults, repair, migration, or alternate schema forms;
- modify simulator/runtime semantics;
- add CLI/UI or video extraction.
