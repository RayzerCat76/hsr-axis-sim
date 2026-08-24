# HSR-AXIS-001F — Base-bounded Golden Replay Manifest File Loader

## Status

PASS — proceed

## Implementation summary

- Added the downstream package `hsr_axis_sim.runtime_golden_manifest_files`.
- Added immutable `GoldenReplayManifestFileSpec` with one canonical relative POSIX manifest path, positive `max_bytes`, and optional pinned manifest SHA-256.
- Added immutable `GoldenReplayManifestFileLoadResult` preserving the exact spec, resolved absolute base directory, resolved absolute manifest path, and complete accepted HSR-AXIS-001E manifest artifact.
- Base directories are explicitly supplied and must resolve to directories.
- Manifest paths are relative, canonical POSIX paths only; absolute paths, traversal, backslash separators, and noncanonical spellings are rejected.
- Resolved manifest targets must remain inside the resolved base directory after symlink resolution and must be regular files.
- Reads are bounded to `max_bytes + 1`, then exact bytes are delegated unchanged to HSR-AXIS-001E `load_golden_replay_manifest_bytes` with the same byte limit and optional digest.
- Added deterministic text reporting only file/artifact provenance, manifest digest/size, batch ID, and case count.
- Added decision D-015: Golden manifest files are explicit and base-directory bounded.

## Files added

- `LUMEN_TASK_HSR_AXIS_001F.md`
- `docs/runtime/GOLDEN_REPLAY_MANIFEST_FILE_V1.md`
- `hsr_axis_sim/runtime_golden_manifest_files/__init__.py`
- `hsr_axis_sim/runtime_golden_manifest_files/model.py`
- `hsr_axis_sim/runtime_golden_manifest_files/load.py`
- `hsr_axis_sim/tests/test_runtime_golden_manifest_file_loader.py`
- `hsr_axis_sim/tests/test_hsr_axis_001f_preservation.py`

## Files modified

- `docs/DECISION_LOG.md`
- `docs/HSR_AXIS_SIM_MASTER_BIBLE.md`
- `hsr_axis_sim/LUMEN_RESULT.md`

No existing production simulator, runtime trace layer, Golden Replay validator/case/batch/manifest executable package, regression, search, binding, data, or locked fixture behavior was modified.

## Tests added

Manifest-file tests cover:
- successful explicit file load with resolved path provenance and pinned digest;
- optional unpinned manifest load while retaining computed SHA-256 identity;
- deterministic text without batch execution;
- rejection of absolute, traversal, backslash, repeated-separator, dot-segment, and trailing-separator paths;
- strict positive integer byte limits and optional SHA-256 validation;
- missing/non-directory bases and missing/directory manifest targets;
- symlink escape rejection after resolution;
- delegation of size, digest, and canonicality failures to HSR-AXIS-001E;
- frozen spec/result models and strict result provenance;
- invalid loader/renderer input rejection.

Preservation tests confirm:
- no accepted upstream package imports `runtime_golden_manifest_files`;
- the file loader delegates manifest semantics only through HSR-AXIS-001E;
- no batch execution, replay execution, comparison, or divergence logic is duplicated;
- prior Golden Replay pipeline contract documents remain present;
- production LIFO compatibility behavior remains unchanged.

## Exact validation commands and real results

GitHub Actions workflow: `HSR Axis Sim Validation`, PR #9, run #29, job `validate` (`97334634456`).

1. `python -m compileall -q hsr_axis_sim`
   - PASS.
2. `python -m pytest -q`
   - PASS: `892 passed in 7.11s`.
3. `python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --format text`
   - PASS 20/20 total checks:
     - 12/12 golden replays;
     - 2/2 manual checks;
     - 2/2 search scenarios;
     - 2/2 action-sequence trace checks;
     - 2/2 trace-evidence checks.
4. `python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --only trace_evidence --format text`
   - PASS 2/2 trace-evidence checks.

## Warnings / errors

- No compile, test, or regression errors.
- Existing GitHub Actions platform warning remains: `actions/checkout@v4` and `actions/setup-python@v5` target Node.js 20 and are currently forced onto Node.js 24. This is unrelated to manifest-file correctness and is nonblocking.

## Acceptance review

- File location and manifest byte identity remain separate explicit contracts.
- Manifest file lookup is deterministic and independent of the ambient working directory.
- Path traversal and resolved symlink escape are rejected before reading manifest bytes.
- File reads are bounded and do not normalize, repair, decode, or reinterpret bytes.
- Strict JSON/schema/canonicality/digest semantics remain exclusively owned by HSR-AXIS-001E.
- The result is immutable and preserves both file and manifest provenance.
- No batch execution was introduced early.
- No directory scanning/discovery, manifest repair/migration/defaults, simulator auto-run, CLI/UI, video extraction, new HSR mechanics, or FIFO/LIFO change was introduced.
- Existing production LIFO behavior remains unchanged.

## Unresolved issues

None blocking HSR-AXIS-001F acceptance.

Existing unresolved HSR game semantics remain tracked separately and were not changed.

## Suggested next milestone

`HSR-AXIS-001G — Manifest-backed Golden Replay Batch Runner`

001G should compose the accepted 001F manifest-file load result with the accepted 001D batch runner under the same explicit base directory. It should not add manifest discovery, simulator auto-generation, retry/parallel execution, CLI/UI, or new gameplay semantics.
