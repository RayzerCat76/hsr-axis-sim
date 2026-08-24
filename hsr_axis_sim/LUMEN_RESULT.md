# HSR-AXIS-001G — Manifest-backed Golden Replay Batch Runner

## Status

PASS — proceed

## Implementation summary

- Added downstream package `hsr_axis_sim.runtime_golden_manifest_runs`.
- Added immutable `GoldenReplayManifestBatchRunResult` preserving the complete accepted HSR-AXIS-001F manifest-file load result and complete accepted HSR-AXIS-001D batch result.
- Result construction rejects any batch plan that differs from the plan reconstructed by the loaded manifest.
- Result construction rejects any batch base directory that differs from the resolved base directory used to load the manifest.
- Added `run_golden_replay_manifest_batch`: load one reviewed manifest through HSR-AXIS-001F, then execute exactly `manifest_load.artifact.plan` through HSR-AXIS-001D using exactly `manifest_load.base_directory`.
- Manifest failures occur before the batch runner is called.
- Replay mismatches remain completed results and continue through later cases; operational replay failures retain HSR-AXIS-001D fail-fast behavior.
- Added deterministic text that wraps the accepted HSR-AXIS-001F manifest-file report and accepted HSR-AXIS-001D batch report in fixed order.
- Added decision D-016: manifest-backed batches share one resolved base directory.

## Files added

- `LUMEN_TASK_HSR_AXIS_001G.md`
- `docs/runtime/GOLDEN_REPLAY_MANIFEST_RUN_V1.md`
- `hsr_axis_sim/runtime_golden_manifest_runs/__init__.py`
- `hsr_axis_sim/runtime_golden_manifest_runs/model.py`
- `hsr_axis_sim/runtime_golden_manifest_runs/run.py`
- `hsr_axis_sim/tests/test_runtime_golden_manifest_batch_runner.py`
- `hsr_axis_sim/tests/test_hsr_axis_001g_preservation.py`

## Files modified

- `docs/DECISION_LOG.md`
- `docs/HSR_AXIS_SIM_MASTER_BIBLE.md`
- `hsr_axis_sim/LUMEN_RESULT.md`

No existing production simulator, runtime trace layer, Golden Replay validator/case/batch/manifest/file-loader executable package, regression, search, binding, data, or locked fixture behavior was modified.

## Tests added

Manifest-backed batch tests cover:
- declared plan execution under the exact resolved manifest base directory;
- a middle replay mismatch continuing through later cases;
- all-match summary behavior;
- deterministic composition text wrapping accepted 001F and 001D reports;
- manifest digest failure before any batch execution;
- replay operational failure propagation without a partial composition result;
- frozen result model;
- rejection of plan mismatch and base-directory mismatch in constructed results;
- invalid runner/renderer input rejection.

Preservation tests confirm:
- no accepted upstream package imports `runtime_golden_manifest_runs`;
- the composition layer calls only the accepted 001F load boundary and accepted 001D batch boundary;
- no manifest-byte loading, replay execution, validation, comparison, or divergence semantics are duplicated;
- no discovery, retry, or parallel execution hooks were added;
- production LIFO compatibility behavior remains unchanged.

## Exact validation commands and real results

Initial GitHub Actions run #33, job `97335677788`:
- compile PASS;
- pytest: `1 failed, 902 passed in 7.19s`;
- failure was only a test assertion using `first.index("BATCH")`, which matched the word `BATCH` inside the composition header before the actual `BATCH` section delimiter;
- production implementation was unchanged.

The test assertion was corrected to compare the full section delimiters `\nMANIFEST_FILE\n` and `\nBATCH\n`.

Final validated implementation run: GitHub Actions workflow `HSR Axis Sim Validation`, PR #10, run #34, job `validate` (`97335860386`).

1. `python -m compileall -q hsr_axis_sim`
   - PASS.
2. `python -m pytest -q`
   - PASS: `903 passed in 7.47s`.
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

- Final validated implementation has no compile, test, or regression errors.
- Existing GitHub Actions platform warning remains: `actions/checkout@v4` and `actions/setup-python@v5` target Node.js 20 and are currently forced onto Node.js 24. This is unrelated to manifest-backed batch correctness and is nonblocking.

## Acceptance review

- One resolved base directory is authoritative for both the reviewed manifest and every replay file referenced by its reconstructed plan.
- Manifest load occurs before batch execution; invalid manifest identity cannot start the batch.
- The exact accepted plan object semantics are reused rather than reconstructed by the composition layer.
- Existing batch mismatch and operational-failure semantics are preserved without reinterpretation.
- Returned provenance is complete and immutable, and plan/base misalignment cannot be represented as a valid result.
- No discovery/scanning, simulator auto-generation, retry, parallelism, partial-error aggregation, repair/migration/defaults, CLI/UI, video extraction, new HSR mechanics, or FIFO/LIFO change was introduced.
- Existing production LIFO behavior remains unchanged.

## Unresolved issues

None blocking HSR-AXIS-001G acceptance.

Existing unresolved HSR game semantics remain tracked separately and were not changed.

## Suggested next milestone

`HSR-RUNTIME-ARCH-007 — Explicit Legacy Event Stream -> Runtime Trace Artifact Bridge`

ARCH-007 should compose the already accepted explicit legacy `Event` stream adapter with the already accepted runtime trace exporter so callers can deliberately turn one observed legacy event stream into a deterministic runtime trace artifact. It must remain explicitly invoked and must not yet inspect, drain, clear, or automatically hook simulator event queues/state.
