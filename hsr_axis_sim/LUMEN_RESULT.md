# HSR-RUNTIME-ARCH-022 — Clamped Resource Static Golden Regression Promotion

## Status

PASS — proceed

## Implementation summary

- Promoted the accepted ARCH-021 reviewed static clamped-Energy Golden fixture into the existing standalone `runtime_action_session_regression` lane as the second reviewed case.
- Evolved the locked runtime regression manifest to strict version `1.1` while preserving exact parser compatibility for version `1.0`.
- Version `1.0` retains the original ARCH-018 case schema exactly and rejects the new `setup` field.
- Version `1.1` requires one strict `setup` object per case.
- Added only two closed setup kinds:
  - `EMPTY`: exact `{ "kind": "EMPTY" }`, reconstructing the original empty-state/effect-free ARCH-017 case;
  - `ENERGY_GAIN`: one explicit Unit plus one production `GainEnergy` effect at one explicit declared action index.
- `ENERGY_GAIN` accepts only the exact reviewed fields `target_id`, `target_name`, `team`, `base_speed`, `initial_energy`, `max_energy`, `action_index`, and `amount` in addition to `kind`.
- Numeric setup fields require finite non-boolean numbers. `base_speed > 0` mirrors the existing `Unit` constructor requirement. `action_index` must be an exact nonnegative integer addressing a declared action.
- No additional Energy sign/range assumptions were introduced; production `Unit` and `GainEnergy` behavior remains authoritative.
- The runner remains narrow:
  - `EMPTY` constructs `BattleState([])` and effect-free actions;
  - `ENERGY_GAIN` constructs exactly one declared Unit and injects exactly one `GainEnergy(target_ids=[target_id], amount=amount)` on the selected action;
  - all other actions remain effect-free.
- No generic effect list, effect-name registry, reflection/import path, free-form kwargs, script/eval path, character ID, or skill ID was added.
- Locked manifest `HSR_RUNTIME_ACTION_SESSION_REGRESSION_001` now contains exactly two cases in declared order:
  1. `arch-017-reviewed-static-action-session` using `EMPTY`;
  2. `arch-021-reviewed-static-clamped-energy` using `ENERGY_GAIN` with target Energy `90/100` and requested gain `25`.
- Standalone runtime regression lane now passes exactly `2/2`.
- Updated the ARCH-021 stage-boundary test so the fixture remains forbidden from the legacy regression manifest but is now required exactly once in the standalone runtime regression manifest, which is the explicit purpose of ARCH-022.
- Added runtime regression manifest v1.1 documentation.
- Neither reviewed static fixture was modified.
- Legacy `hsr_axis_sim/data/regression_manifest.json` was not modified.

## Files added

- `LUMEN_TASK_HSR_RUNTIME_ARCH_022.md`
- `docs/runtime/RUNTIME_ACTION_SESSION_REGRESSION_V1_1.md`
- `hsr_axis_sim/tests/test_runtime_arch_022_resource_regression_promotion.py`

## Files modified

- `hsr_axis_sim/data/runtime_action_session_regression_manifest.json`
- `hsr_axis_sim/runtime_action_session_regression/manifest.py`
- `hsr_axis_sim/runtime_action_session_regression/runner.py`
- `hsr_axis_sim/tests/test_runtime_arch_018_standalone_regression.py`
- `hsr_axis_sim/tests/test_runtime_arch_021_static_resource_golden_fixture.py`
- `hsr_axis_sim/LUMEN_RESULT.md`

No `sim/**` production implementation, runtime adapter, runtime trace contract/schema, loader, exporter, comparator, divergence reporter, Golden validator, legacy regression manifest, static expected fixture, AV/timeline implementation, character/research evidence, or extra-turn/LIFO implementation was modified.

## Tests added / updated

ARCH-022 focused coverage proves:

- explicit supported manifest versions `1.0` and `1.1`;
- original version `1.0` exact case schema still parses without `setup`;
- version `1.0` rejects `setup` rather than silently accepting a newer field;
- version `1.1` requires `setup`;
- `EMPTY` accepts only its exact discriminator field;
- `ENERGY_GAIN` loads into a frozen typed setup model with exact reviewed fields;
- unknown setup kinds, unknown fields, and missing fields are rejected;
- bool, string, null, NaN, positive infinity, and negative infinity are rejected for numeric setup fields where applicable;
- nonpositive `base_speed` is rejected;
- boolean, negative, float, string, null, and out-of-range `action_index` values are rejected;
- setup string fields must be non-empty strings;
- locked manifest contains exactly ARCH-017 then ARCH-021 in declared order;
- locked standalone runtime lane passes exactly `2/2`;
- ARCH-017 result remains `action_count=2`, `record_count=4`;
- ARCH-021 result is `action_count=1`, `record_count=3`;
- controlled regression-harness mutation `amount=25 -> 20` reports a Golden mismatch at record index `1` with first path `/event/payload/legacy_data/requested_delta`;
- ARCH-017 fixture remains exactly 3013 bytes at SHA-256 `f672ffaac9ef9296e4982a6fb61f4d0257b5c0506412bcf54eb1768334118c66`;
- ARCH-021 fixture remains exactly 2759 bytes at SHA-256 `4fe2c8b3c9c22821a49ff380c9635828e36f3c4a3bbbc13d2cc077dd4d97e605`;
- regression harness source contains the explicit `ENERGY_GAIN`/`GainEnergy` path and excludes generic import/eval/exec/effect-class/kwargs mechanisms;
- legacy regression remains 20/20;
- trace evidence remains 2/2;
- production LIFO remains `third, second, first`.

The ARCH-018 historical standalone tests were updated only where the locked lane intentionally changed from one reviewed case to two. Its synthetic `_valid_manifest_data()` intentionally remains version `1.0`, providing direct backward-compatibility coverage for the old exact schema.

The ARCH-021 stage-boundary test was updated only for the explicitly authorized promotion: the resource fixture must remain absent from the legacy regression manifest but must now appear exactly once in the standalone runtime manifest. Its static fixture identity and runtime expected-generation guard remain unchanged.

## Exact validation commands and real results

### Initial PR CI

GitHub Actions workflow `HSR Axis Sim Validation`, PR #27, run #130, job `validate` (`97644954544`):

1. `python -m compileall -q hsr_axis_sim`
   - PASS.
2. `python -m pytest -q`
   - `1 failed, 1152 passed in 7.66s`.
3. Later validation lanes were skipped after pytest failure.

The only failure was the accepted ARCH-021 stage-boundary assertion that the fixture was not yet present in either regression manifest. ARCH-022 explicitly promotes that fixture into the standalone runtime manifest, so this was a stale stage-boundary test rather than a production or regression-harness failure. The correction retained the prohibition on legacy-manifest promotion and changed the standalone assertion to require exactly one reviewed ARCH-021 entry. No fixture bytes or production implementation were changed.

### Validated implementation CI

GitHub Actions workflow `HSR Axis Sim Validation`, PR #27, run #131, job `validate` (`97645194999`).

1. `python -m compileall -q hsr_axis_sim`
   - PASS.
2. `python -m pytest -q`
   - PASS: `1153 passed in 7.82s`.
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
   - PASS `2/2` runtime action-session Golden regression:
     - ARCH-017: `action_count=2`, `record_count=4`, expected SHA `f672ffaac9ef9296e4982a6fb61f4d0257b5c0506412bcf54eb1768334118c66`;
     - ARCH-021: `action_count=1`, `record_count=3`, expected SHA `4fe2c8b3c9c22821a49ff380c9635828e36f3c4a3bbbc13d2cc077dd4d97e605`.

## Warnings / errors

- No compile, manifest-parser, runtime-harness, Golden comparison, legacy-regression, trace-evidence, or runtime-regression error remains after the authorized ARCH-021 stage-boundary update.
- Existing GitHub Actions Node 20 deprecation warning remains nonblocking and unrelated to ARCH-022 correctness.

## Acceptance review

- ARCH-021 is now a repeatable standalone runtime Golden regression without entering the legacy regression suite.
- Runtime lane is exactly `2/2` and preserves declared order.
- Manifest schema evolution is explicit: old v1.0 remains strict and accepted; v1.1 is a separate exact schema requiring setup.
- The new setup surface is deliberately narrow and cannot express arbitrary simulator effects.
- ARCH-017 and ARCH-021 reviewed expected bytes remain unchanged.
- Production Energy mutation/emission and adapter behavior remain unchanged.
- Trace schema v1 remains unchanged.
- Legacy regression remains 20/20 and trace evidence 2/2.
- No SP, AV, speed, advance, delay, immediate-action, extra-turn, character, or release-game semantic was added.
- No hidden HSR values were inferred; all new regression setup values are explicit reviewed test inputs.
- Production LIFO compatibility remains unchanged.

## Unresolved issues

None blocking HSR-RUNTIME-ARCH-022 acceptance.

The standalone regression setup language intentionally supports only `EMPTY` and the one reviewed `ENERGY_GAIN` construction. Future resource or timeline fixtures must receive separate narrow schema review rather than extending this into a generic effect DSL.

AV/speed/advance/delay/immediate-action/extra-turn state changes still lack equivalent runtime observation events and remain separate work.

## Suggested next milestone

`HSR-RUNTIME-ARCH-023 — Reviewed Static Skill-Point Observation Golden Fixture`

ARCH-023 should add one manually constructed static schema-v1 Golden expectation for a clamped production `GainSkillPoint` action, locking `ACTION_START -> SKILL_POINTS_CHANGED -> ACTION_END`, team scope, `unit_id=null`, and requested-versus-applied delta. It should validate through accepted ARCH-016 but remain outside the standalone regression manifest initially, mirroring the reviewed fixture-first discipline used by ARCH-021. No runtime regression schema extension, simulator semantic change, AV/timeline observation, arbitrary effect DSL, or video automation should be included in ARCH-023.
