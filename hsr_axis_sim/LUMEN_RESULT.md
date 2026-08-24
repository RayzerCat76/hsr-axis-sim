# HSR-AXIS-001B — Deterministic Golden Replay Validator

## Status

PASS — proceed

## Implementation summary

- Added the standard-library-only downstream sidecar `hsr_axis_sim.runtime_golden_replays`.
- Added immutable `GoldenReplayValidationConfig` and `GoldenReplayValidationResult` models.
- Expected golden canonical bytes are loaded with the existing strict loader and `TraceDigestPolicy.REQUIRE_MATCH` against a pinned SHA-256.
- Actual canonical bytes are loaded with the existing strict loader without a pre-known digest; their computed SHA-256 is retained as provenance.
- Record comparison is delegated only to ARCH-005 `compare_runtime_trace_documents`.
- First-divergence selection is delegated only to ARCH-006 `build_first_divergence_report`.
- Added deterministic replay-level text that embeds the accepted ARCH-006 text report rather than reimplementing divergence logic.
- Added a first Golden Replay test constructed manually from explicit `RuntimeEvent` values; it contains contract-only fixture identifiers and no inferred hidden HSR values.
- Added decision D-011: golden expected artifacts are digest-pinned.

## Files added

- `LUMEN_TASK_HSR_AXIS_001B.md`
- `docs/runtime/GOLDEN_REPLAY_VALIDATOR_V1.md`
- `hsr_axis_sim/runtime_golden_replays/__init__.py`
- `hsr_axis_sim/runtime_golden_replays/model.py`
- `hsr_axis_sim/runtime_golden_replays/validate.py`
- `hsr_axis_sim/tests/test_runtime_golden_replay_validator.py`
- `hsr_axis_sim/tests/test_hsr_axis_001b_preservation.py`

## Files modified

- `docs/DECISION_LOG.md`
- `docs/HSR_AXIS_SIM_MASTER_BIBLE.md`
- `hsr_axis_sim/LUMEN_RESULT.md`

No existing production simulator, runtime contract, adapter, exporter, loader, comparator, first-divergence reporter, regression, search, binding, data, or locked fixture executable behavior was modified.

## Tests added

Golden Replay tests cover:
- manually constructed deterministic matching replay;
- mismatch propagation through the accepted first-divergence report;
- expected SHA-256 mismatch rejection;
- noncanonical expected input rejection;
- noncanonical actual input rejection;
- strict config validation;
- frozen config and result models;
- repeatable deterministic text;
- expected/actual artifact SHA-256 provenance;
- invalid validator/renderer input rejection.

Preservation tests cover:
- no protected upstream area imports `runtime_golden_replays`;
- validator source composes accepted loader/comparator/reporter APIs without selecting field differences itself;
- prior trace-pipeline contract documents remain present;
- production LIFO compatibility behavior remains unchanged.

## Exact validation commands and real results

GitHub Actions workflow: `HSR Axis Sim Validation`, PR #5, run #13, job `validate` (`97330636238`).

1. `python -m compileall -q hsr_axis_sim`
   - PASS.
2. `python -m pytest -q`
   - PASS: `831 passed in 7.29s`.
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
- Existing GitHub Actions platform warning remains: `actions/checkout@v4` and `actions/setup-python@v5` target Node.js 20 and are currently forced onto Node.js 24. This is unrelated to Golden Replay correctness and is nonblocking.

## Acceptance review

- Golden expected bytes cannot drift silently because the expected loader requires an exact pinned SHA-256.
- Actual bytes remain strict canonical input and are not repaired, normalized, or pre-pinned.
- Comparison and first-divergence semantics are reused rather than duplicated.
- The result is immutable and preserves loader, comparator, reporter, and digest provenance.
- Matching/diverged text is deterministic.
- The first replay is manually constructed and deterministic.
- No automatic video extraction, tolerance, realignment, repair, simulator auto-wiring, new HSR mechanics, damage expansion, or FIFO/LIFO change was introduced.
- Existing production LIFO behavior remains unchanged.

## Unresolved issues

None blocking HSR-AXIS-001B acceptance.

Existing unresolved HSR game semantics remain tracked separately and were not changed.

## Suggested next milestone

`HSR-AXIS-001C — File-backed Golden Replay Case Runner`

This should add an explicit reviewed case definition and exact file-path handoff around the accepted in-memory validator without adding batch discovery or simulator auto-wiring.
