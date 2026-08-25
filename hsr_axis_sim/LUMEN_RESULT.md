# HSR-RUNTIME-ARCH-021 — Reviewed Static Resource Observation Golden Fixture

## Status

PASS — proceed

## Implementation summary

- Added one independently reviewed static schema-v1 Golden expectation for the ARCH-020 clamped-energy production observation path.
- The fixture is manually specified and stored as compact canonical UTF-8 JSON under `hsr_axis_sim/data/runtime_golden_fixtures/arch_021_reviewed_clamped_energy_expected.json`.
- Exact fixture identity:
  - size: `2759` bytes;
  - SHA-256: `4fe2c8b3c9c22821a49ff380c9635828e36f3c4a3bbbc13d2cc077dd4d97e605`;
  - no trailing newline;
  - trace ID: `arch-021-reviewed-static-expected`;
  - fixture ID: `arch-021-reviewed-static-clamped-energy`.
- The reviewed production scenario is contract-only:
  - actor `resource-actor`;
  - target `resource-target`;
  - action `reviewed-clamped-energy`;
  - target starts at Energy `90` with max Energy `100`;
  - one `GainEnergy(target_ids=["resource-target"], amount=25)` effect;
  - `ends_turn=False`.
- The expected trace has exactly three records in order:
  1. `ACTION_START`;
  2. `ENERGY_CHANGED`;
  3. `ACTION_END`.
- The static resource observation explicitly locks the clamped distinction:
  - `before=90`;
  - `after=100`;
  - `requested_delta=25`;
  - `applied_delta=10`;
  - `cap=100`;
  - `resource_kind=ENERGY`;
  - `scope=UNIT`;
  - `unit_id=resource-target`.
- The production scenario is executed through accepted ARCH-016 using the existing action/session/capture/stitch/Golden chain and matches the static expected artifact exactly at the comparison layer.
- A deliberate actual-only input change from `GainEnergy.amount=25` to `20` keeps `after=100` and `applied_delta=10` unchanged but changes `requested_delta`. Against the same static expectation, accepted first-divergence reporting identifies record index `1` and path `/event/payload/legacy_data/requested_delta`, expected `25`, actual `20`.
- The fixture is deliberately not added to either the legacy regression manifest or the standalone runtime action-session regression manifest.
- The ARCH-021 test source includes an AST guard preventing simulator/adapter/exporter/canonical-serialization helpers from becoming an expected-artifact generation path at test runtime.
- No simulator, runtime adapter, contract, exporter, loader, comparator, divergence, Golden validator, regression implementation, manifest, or existing Golden fixture was changed.

## Files added

- `LUMEN_TASK_HSR_RUNTIME_ARCH_021.md`
- `hsr_axis_sim/data/runtime_golden_fixtures/arch_021_reviewed_clamped_energy_expected.json`
- `hsr_axis_sim/tests/test_runtime_arch_021_static_resource_golden_fixture.py`

## Files modified

- `hsr_axis_sim/LUMEN_RESULT.md`

## Tests added

ARCH-021 focused tests cover:

- exact static fixture byte size and SHA-256;
- no trailing newline;
- strict compact canonical loader acceptance with required digest match;
- exact schema-v1 trace identity and three-record sequence;
- exact `ACTION_START -> ENERGY_CHANGED -> ACTION_END` ordering;
- exact action/actor/target provenance;
- exact `resource_change` payload;
- exact defensive `legacy_data` payload;
- schema-v1 `RuntimeTraceRecord.numeric_values == {}` for every record;
- accepted ARCH-016 production action-session Golden PASS against the static fixture;
- final target Energy equals `100`;
- exact pending-event order and final cursor `(3, 3)`;
- deliberate requested-gain change from `25` to `20` produces a normal Golden mismatch;
- first divergence is record index `1`, `/event/payload/legacy_data/requested_delta`, expected `25`, actual `20`;
- deliberate mismatch still preserves equal `after=100` and `applied_delta=10`, isolating requested-versus-applied semantics;
- fixture absence from both regression manifests;
- AST guard against runtime expected-artifact generation helpers;
- ARCH-017 static fixture SHA remains unchanged;
- production LIFO compatibility remains `third, second, first`.

## Exact validation commands and real results

### Initial validated PR CI

GitHub Actions workflow `HSR Axis Sim Validation`, PR #26, run #127, job `validate` (`97642516451`).

1. `python -m compileall -q hsr_axis_sim`
   - PASS.
2. `python -m pytest -q`
   - PASS: `1096 passed in 6.05s`.
3. `python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --format text`
   - PASS legacy locked regression `20/20`:
     - 12/12 golden replays;
     - 2/2 manual checks;
     - 2/2 search scenarios;
     - 2/2 action-sequence trace checks;
     - 2/2 trace-evidence checks.
4. `python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --only trace_evidence --format text`
   - PASS `2/2` trace-evidence checks.
5. `python -m hsr_axis_sim.runtime_action_session_regression.runner --manifest hsr_axis_sim/data/runtime_action_session_regression_manifest.json --format text`
   - PASS `1/1` runtime action-session Golden regression.

The first ARCH-021 PR CI was green; no implementation correction was required before finalization.

## Warnings / errors

- No compile, fixture-integrity, strict-loader, ARCH-016, comparator/divergence, legacy-regression, trace-evidence, or runtime-regression error was observed.
- Existing GitHub Actions Node 20 deprecation warning remains nonblocking and unrelated to ARCH-021 correctness.

## Acceptance review

- Expected bytes are static, reviewed, compact, and digest-pinned.
- Authoritative expected bytes are not generated at test runtime from the simulator, legacy adapter, trace exporter, or canonical serialization helpers.
- Production resource observation matches the reviewed static artifact through accepted ARCH-016.
- The Golden locks requested-versus-applied clamp semantics explicitly rather than only checking final Energy.
- Deliberate divergence uses the same expected artifact and is surfaced by accepted comparator/first-divergence logic without custom comparison code.
- Trace schema v1 remains unchanged and record-level `numeric_values` remains empty.
- Both regression manifests are unchanged.
- ARCH-017 fixture is unchanged.
- No SP, trigger, AV, speed, advance, delay, immediate-action, extra-turn, or character semantic was added.
- No release-game resource value or hidden HSR rule was invented; fixture values are explicit contract-only test values.
- Production LIFO compatibility remains unchanged.

## Unresolved issues

None blocking HSR-RUNTIME-ARCH-021 acceptance.

The reviewed fixture is not yet part of the repeatable runtime regression lane. That promotion should remain a separate milestone because the current runtime regression manifest only reconstructs simple no-effect Actions; adding a resource case requires one narrowly reviewed effect schema rather than a generic arbitrary-effect manifest.

AV/speed/advance/delay/immediate-action/extra-turn state changes still lack equivalent runtime observation events and remain separate work.

## Suggested next milestone

`HSR-RUNTIME-ARCH-022 — Clamped Resource Static Golden Regression Promotion`

ARCH-022 should promote the accepted ARCH-021 fixture into the standalone `runtime_action_session_regression` lane as a second reviewed case. Extend that manifest/runner only enough to reconstruct the exact reviewed `GainEnergy` action and explicit initial target Energy/max-Energy state. Do not introduce a generic arbitrary-effects schema, SP case, trigger schema, AV/timeline observation, simulator semantic change, or legacy regression integration. The existing ARCH-017 case must remain unchanged and the runtime lane should become exactly `2/2` after promotion.
