# HSR-RUNTIME-ARCH-018 — Reviewed Static End-to-End Golden Fixture Regression Integration

## Status

PASS — proceed

## Implementation summary

- Promoted the accepted ARCH-017 reviewed static runtime-trace Golden fixture into a locked repeatable CI regression path.
- The first attempted design added a `runtime_action_sessions` group directly to legacy `hsr_axis_sim/regression/**` and `regression_manifest.json`. CI correctly rejected that design because accepted preservation tests require runtime sidecars to remain downstream of the legacy regression package, and existing research evidence pins the legacy runner/manifest bytes and counts.
- Fully reverted the rejected direct-integration changes instead of weakening preservation tests or rewriting historical evidence pins.
- Added a separate downstream package: `hsr_axis_sim.runtime_action_session_regression`.
- Added a separate strict manifest: `hsr_axis_sim/data/runtime_action_session_regression_manifest.json`.
- Kept legacy `hsr_axis_sim/regression/**` and `hsr_axis_sim/data/regression_manifest.json` byte-for-byte unchanged from `main`; legacy locked identity remains exactly 20/20.
- The new runtime lane reconstructs only explicitly declared simple production `Action` objects with no targets/effects and calls accepted ARCH-016 exactly once per case.
- The locked case reuses the unchanged ARCH-017 expected artifact at 3013 bytes with SHA-256 `f672ffaac9ef9296e4982a6fb61f4d0257b5c0506412bcf54eb1768334118c66`.
- Added deterministic PASS/failure reporting, controlled first-divergence provenance on Golden mismatch, fail-fast support, strict manifest validation, and a dedicated GitHub Actions step.
- Removed a newly introduced `runpy` warning by keeping package `__init__` from eagerly importing the CLI runner.
- Added decision D-028: reviewed runtime action-session Golden checks use a separate locked regression lane rather than extending the legacy regression runner.

## Files added

- `LUMEN_TASK_HSR_RUNTIME_ARCH_018.md`
- `hsr_axis_sim/data/runtime_action_session_regression_manifest.json`
- `hsr_axis_sim/runtime_action_session_regression/__init__.py`
- `hsr_axis_sim/runtime_action_session_regression/manifest.py`
- `hsr_axis_sim/runtime_action_session_regression/runner.py`
- `hsr_axis_sim/tests/test_runtime_arch_018_standalone_regression.py`

## Files modified

- `.github/workflows/tests.yml`
- `docs/DECISION_LOG.md`
- `docs/HSR_AXIS_SIM_MASTER_BIBLE.md`
- `hsr_axis_sim/LUMEN_RESULT.md`

The rejected intermediate edits to legacy `hsr_axis_sim/regression/**`, legacy `regression_manifest.json`, and ARCH-017 tests were reverted before acceptance and are not part of the final intended diff.

## Tests added

ARCH-018 tests cover:

- strict standalone manifest schema/version/root fields;
- non-empty ordered cases and duplicate case-ID rejection;
- canonical repo-relative existing expected path requirements;
- exact lowercase SHA-256 validation;
- strict simple Action schema with no arbitrary effects/targets extension;
- invalid `ends_turn` types;
- locked one-case manifest identity and declared action order;
- standalone runtime regression PASS 1/1;
- deterministic text and JSON reporting;
- standalone CLI behavior without legacy runner output;
- controlled second-action mismatch exposing accepted ARCH-006 first divergence at record index 2 and `/event/action_id`;
- fail-fast behavior across multiple runtime cases;
- wrong-but-well-formed expected digest producing a failed operational check through the accepted loader;
- exact ARCH-017 fixture size/digest preservation;
- proof that the legacy regression manifest still does not reference the runtime fixture;
- legacy locked regression remains exactly 20/20;
- trace-evidence lane remains exactly 2/2;
- production LIFO compatibility behavior remains unchanged.

## Exact validation commands and real results

Final clean implementation CI before governance-only closeout:
GitHub Actions workflow `HSR Axis Sim Validation`, PR #23, run #108, job `validate` (`97476853631`).

1. `python -m compileall -q hsr_axis_sim`
   - PASS.
2. `python -m pytest -q`
   - PASS: `1052 passed in 5.95s`.
3. `python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --format text`
   - PASS: legacy locked regression remains exactly `20/20`:
     - 12/12 golden replays;
     - 2/2 manual checks;
     - 2/2 search scenarios;
     - 2/2 action-sequence trace checks;
     - 2/2 trace-evidence checks.
4. `python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --only trace_evidence --format text`
   - PASS: `2/2` trace-evidence checks.
5. `python -m hsr_axis_sim.runtime_action_session_regression.runner --manifest hsr_axis_sim/data/runtime_action_session_regression_manifest.json --format text`
   - PASS: `1/1` runtime action-session Golden checks.
   - Locked expected SHA-256: `f672ffaac9ef9296e4982a6fb61f4d0257b5c0506412bcf54eb1768334118c66`.
   - Deterministic actual SHA-256 in the accepted case: `452d52be7dec07ddebe0ca5ec0ca3cf58d695bd2312ada684d70aa22891435d0`.
   - Record count: `4`.

## Rejected intermediate CI and fixes

### Run #90

The original direct legacy-regression integration failed before regression execution:

- compile: PASS;
- pytest: `19 failed, 1032 passed`.

The failures were meaningful architecture protection signals: legacy regression imported runtime sidecar packages, sidecar preservation tests failed, and existing Tingyun research/reference evidence reported stale pinned source SHA/counts because the legacy regression files/manifest had changed.

Resolution: reject the design, fully restore legacy regression files/manifest and ARCH-017 preservation expectations, and move ARCH-018 into a separate downstream runtime regression lane. No preservation test or historical research pin was weakened to make the change pass.

### Run #106

After the architecture correction:

- compile: PASS;
- pytest: `1 failed, 1051 passed`.

The sole failure was a test expecting the word `digest` while the accepted loader correctly reported `runtime trace SHA-256 mismatch`. Only the test assertion was corrected to match the accepted error contract; runtime behavior was not changed.

### Run #107

Core implementation passed:

- pytest: `1052 passed in 7.97s`;
- legacy regression: 20/20;
- trace evidence: 2/2;
- runtime action-session regression: 1/1.

It exposed one new `runpy` warning caused by the package `__init__` eagerly importing the CLI runner. That warning was removed before acceptance.

### Run #108

Clean implementation validation passed with no ARCH-018 runtime warning. Only the repository's pre-existing GitHub Actions Node 20 deprecation warning remains.

## Warnings / errors

- No compile, pytest, legacy regression, trace-evidence, runtime-Golden, or standalone regression errors remain.
- The ARCH-018-created `runpy` warning was fixed before acceptance.
- Existing GitHub Actions warning remains: `actions/checkout@v4` and `actions/setup-python@v5` target deprecated Node 20 and are currently forced onto Node 24 by GitHub. This is nonblocking and unrelated to simulator/runtime correctness.

## Acceptance review

- ARCH-017 expected artifact remains byte-for-byte unchanged at 3013 bytes and the accepted SHA-256.
- New runtime regression invokes accepted ARCH-016 rather than reimplementing action capture, stitching, Golden comparison, or first-divergence semantics.
- Manifest action declarations remain intentionally minimal: `action_id`, `name`, `ends_turn`; no generic target/effect serialization framework was introduced.
- Runtime Golden mismatch remains a completed accepted validation result with existing first-divergence provenance.
- Legacy regression implementation, manifest identity, categories, and 20/20 count remain unchanged.
- Existing research/reference artifacts and their pinned legacy sources remain valid because their protected inputs were restored rather than repinned.
- No `sim/**` mechanics changed.
- No accepted runtime adapter/exporter/loader/comparator/divergence/Golden/ARCH-016 semantics changed.
- No automatic expected generation, turn/action selection, video parsing, AI optimization, or FIFO/LIFO semantic change was introduced.
- Production LIFO compatibility behavior remains unchanged.

## Unresolved issues

None blocking HSR-RUNTIME-ARCH-018 acceptance.

The legacy regression lane and runtime action-session regression lane intentionally remain separate. A future milestone may add more reviewed runtime cases, but must not silently merge the two baselines or broaden the runtime manifest into arbitrary action/effect serialization without a new explicit contract.

## Suggested next milestone

No exact post-ARCH-018 task ID is assigned yet. After ARCH-018 merges, inspect the remaining accepted runtime frontier before defining the next milestone. The safest likely direction is adding another independently reviewed runtime regression case only when it exercises already-accepted production semantics; do not invent new mechanics or generalize the manifest prematurely.
