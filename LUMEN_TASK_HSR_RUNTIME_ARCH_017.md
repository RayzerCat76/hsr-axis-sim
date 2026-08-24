# HSR-RUNTIME-ARCH-017 — Reviewed Static End-to-End Golden Action Session Fixture

## Current confirmed state

- HSR-RUNTIME-ARCH-016 — PASS and merged to `main`.
- Confirmed baseline: 1029/1029 pytest, 20/20 locked regression, 2/2 trace evidence.
- Current blocker: none.

## Objective

Add one manually reviewed, static, canonical expected runtime-trace artifact and use accepted ARCH-016 to validate an explicit production Action session against it without generating expected bytes from the simulator under test at test runtime.

## Required implementation

1. Add one static expected runtime-trace JSON artifact under `hsr_axis_sim/data/runtime_golden_fixtures/`.
2. The expected artifact must be manually constructed from accepted contracts only:
   - two explicit `Action(..., ends_turn=False)` steps;
   - no effects;
   - each action visibly produces only `action_started` then `action_finished`;
   - accepted legacy adapter maps these to `ACTION_START` then `ACTION_END`;
   - contiguous runtime sequences 0..3;
   - no semantic gaps.
3. Keep the expected file in exact compact canonical JSON form with no trailing newline.
4. Pin its exact SHA-256 in the test and documentation.
5. Add one ARCH-016 PASS test that reads the static bytes from disk and executes the matching production Action session.
6. Add one controlled divergence test using the same static expected fixture but a deliberately different second action ID; verify accepted first-divergence provenance.
7. The test must not call runtime trace document/artifact builders, adapter helpers, ARCH-013/014/015 directly, or any helper that generates expected bytes at test runtime.
8. Do not add the new fixture to the locked regression manifest in this milestone.

## Reviewed fixture identity

- fixture id: `arch-017-reviewed-static-action-session`
- expected trace id: `arch-017-reviewed-static-expected`
- adapter stream id: `arch-017-reviewed-static`
- actor id: `reviewed-actor`
- action ids: `reviewed-action-a`, `reviewed-action-b`
- expected record sequence:
  1. sequence 0 — ACTION_START — reviewed-action-a
  2. sequence 1 — ACTION_END — reviewed-action-a
  3. sequence 2 — ACTION_START — reviewed-action-b
  4. sequence 3 — ACTION_END — reviewed-action-b
- expected byte size: 3013
- expected SHA-256: `f672ffaac9ef9296e4982a6fb61f4d0257b5c0506412bcf54eb1768334118c66`

## Acceptance criteria

- Static expected file is strict canonical runtime-trace schema v1 and digest-pinned.
- PASS test proves production Actions -> ARCH-016 actual trace matches the static expected record stream.
- Divergence test proves a changed production action ID reports the first mismatch at record index 2 without editing the expected fixture.
- Expected bytes are read, never generated, during test runtime.
- Existing accepted executable packages remain unchanged.
- Locked regression manifest remains byte-for-byte unchanged.
- Complete CI suite passes.

## Required tests

- fixture byte count and SHA-256 are exact;
- strict runtime loader accepts the static fixture with the pinned digest;
- ARCH-016 matching session returns Golden PASS;
- mismatching second action returns completed Golden failure with first divergence at record index 2 and `/event/action_id`;
- test source contains no expected-artifact builder/exporter/adapter generation path;
- regression manifest does not reference the new fixture;
- production LIFO remains unchanged.

## Files/areas that must remain unchanged

Do not modify executable behavior in `sim/**`, `search/**`, `regression/**`, `adapters/**`, `real_bindings/**`, accepted runtime packages, accepted Golden packages, existing data fixtures, `hsr_axis_sim/data/regression_manifest.json`, or reference artifacts.

## Explicit exclusions

No new wrapper package, no simulator behavior change, no adapter/exporter/loader/comparator/divergence change, no Golden validator change, no regression-manifest promotion, no automatic expected generation, no replay/turn/action selection, no file-writing runtime API, no video extraction, no new HSR mechanics, and no FIFO/LIFO change.

## Commands to run

```bash
python -m compileall -q hsr_axis_sim
python -m pytest -q
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --format text
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --only trace_evidence --format text
```

## Final report format

Report task ID, manual fixture derivation, exact fixture SHA/size, files added/modified, tests added, exact commands/results, warnings/errors, unresolved issues, exclusion confirmation, suggested next milestone, and update `hsr_axis_sim/LUMEN_RESULT.md`.

## Execution routing

ChatGPT: GPT-5.6 Sol.  
Codex: High if used; Codex is optional for this milestone.
