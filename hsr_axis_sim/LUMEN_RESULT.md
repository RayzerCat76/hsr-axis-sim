# HSR-RUNTIME-ARCH-024 — Skill-Point Static Golden Regression Promotion

## Status

PASS — proceed

## Implementation summary

- Promoted the accepted ARCH-023 reviewed clamped Skill-Point fixture into the standalone runtime action-session Golden regression lane as the third reviewed case.
- Evolved the runtime regression manifest to explicit version `1.2` while preserving the earlier grammars:
  - v1.0: original six case fields, no `setup`;
  - v1.1: required `setup`, only `EMPTY` and `ENERGY_GAIN`;
  - v1.2: required `setup`, `EMPTY`, `ENERGY_GAIN`, or new `SKILL_POINT_GAIN`.
- Added explicit constants for v1.0, v1.1, and latest v1.2. A v1.1 manifest using `SKILL_POINT_GAIN` is rejected with a controlled version error rather than interpreted under v1.2 semantics.
- Preserved `EMPTY` and `ENERGY_GAIN` parsing and runner behavior unchanged.
- Added frozen `RuntimeActionSessionRegressionSkillPointGainSetup` with exact fields:
  - `initial_skill_points`;
  - `max_skill_points`;
  - `action_index`;
  - `amount`.
- `SKILL_POINT_GAIN` requires exact integer SP values/amount with booleans rejected; `action_index` is an exact nonnegative integer and must address a declared action. No additional SP sign/range rule was invented.
- Runner support remains deliberately narrow:
  - constructs only `BattleState([], skill_points=..., max_skill_points=...)`;
  - injects exactly one production `GainSkillPoint(amount=...)` on the selected action;
  - all other actions remain effect-free.
- No generic effect list, effect class/type field, reflection/import path, free-form kwargs, script/eval path, target DSL, character ID, or skill ID was introduced.
- Locked manifest `HSR_RUNTIME_ACTION_SESSION_REGRESSION_001` now contains exactly three reviewed cases in declared order:
  1. ARCH-017 `EMPTY` — 4 records;
  2. ARCH-021 `ENERGY_GAIN` — 3 records;
  3. ARCH-023 `SKILL_POINT_GAIN` — 3 records.
- The ARCH-023 reviewed fixture remains exactly 2744 bytes at SHA-256 `fc359b367c2922ed39e059f89ad16845ba215508292cfa43ca2ab6031c4c9ba9`.
- Updated the ARCH-023 stage-boundary test only for the explicitly authorized promotion: the fixture remains absent from the legacy regression manifest and must now appear exactly once in the standalone runtime manifest.
- Added version 1.2 manifest documentation.
- No static expected fixture bytes were modified.

## Files added

- `LUMEN_TASK_HSR_RUNTIME_ARCH_024.md`
- `docs/runtime/RUNTIME_ACTION_SESSION_REGRESSION_V1_2.md`
- `hsr_axis_sim/tests/test_runtime_arch_024_skill_point_regression_promotion.py`

## Files modified

- `hsr_axis_sim/data/runtime_action_session_regression_manifest.json`
- `hsr_axis_sim/runtime_action_session_regression/manifest.py`
- `hsr_axis_sim/runtime_action_session_regression/runner.py`
- `hsr_axis_sim/tests/test_runtime_arch_018_standalone_regression.py`
- `hsr_axis_sim/tests/test_runtime_arch_022_resource_regression_promotion.py`
- `hsr_axis_sim/tests/test_runtime_arch_023_static_skill_point_golden_fixture.py`
- `hsr_axis_sim/LUMEN_RESULT.md`

No `sim/**` implementation, runtime adapter, runtime trace schema/loader/exporter/comparator/divergence implementation, Golden validator, legacy regression manifest, static expected fixture, AV/timeline implementation, character/research evidence, or extra-turn/LIFO implementation was modified.

## Tests added / updated

ARCH-024 coverage proves:

- supported versions are exactly `1.0`, `1.1`, `1.2`;
- v1.0 still accepts its original no-setup grammar and rejects `setup`;
- v1.1 still accepts exactly `EMPTY` and the existing typed `ENERGY_GAIN` contract;
- v1.1 explicitly rejects `SKILL_POINT_GAIN` as requiring v1.2;
- v1.2 requires `setup` and accepts all three closed setup kinds;
- `SKILL_POINT_GAIN` exact fields only; unknown/missing fields are rejected;
- SP initial/max/amount reject bool, float, string, and null values;
- action index rejects bool, negative, float, string, null, and out-of-range values;
- locked manifest has exactly ARCH-017 -> ARCH-021 -> ARCH-023;
- locked standalone runtime lane passes exactly 3/3 with record counts 4/3/3;
- controlled ARCH-023 setup change `amount=3 -> 2` reports Golden mismatch at record index 1 and `/event/payload/legacy_data/requested_delta`;
- ARCH-017 remains 3013 bytes at SHA-256 `f672ffaac9ef9296e4982a6fb61f4d0257b5c0506412bcf54eb1768334118c66`;
- ARCH-021 remains 2759 bytes at SHA-256 `4fe2c8b3c9c22821a49ff380c9635828e36f3c4a3bbbc13d2cc077dd4d97e605`;
- ARCH-023 remains 2744 bytes at SHA-256 `fc359b367c2922ed39e059f89ad16845ba215508292cfa43ca2ab6031c4c9ba9`;
- harness source remains closed and contains no generic import/eval/exec/effect-class/free-kwargs path;
- legacy regression remains 20/20;
- trace evidence remains 2/2;
- production LIFO remains `third, second, first`.

Historical ARCH-018 and ARCH-022 tests were changed only where the current locked lane intentionally grew to three cases. ARCH-018 continues using a synthetic v1.0 manifest for backward-compatibility coverage. ARCH-022 now explicitly asserts v1.1 remains available and unchanged while checking that the first two reviewed cases preserve their accepted identity under the current v1.2 lane.

## Exact validation commands and real results

### Initial validated PR CI

GitHub Actions workflow `HSR Axis Sim Validation`, PR #29, run #137, job `validate` (`97647979176`).

1. `python -m compileall -q hsr_axis_sim`
   - PASS.
2. `python -m pytest -q`
   - PASS: `1195 passed in 6.11s`.
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
   - PASS `3/3` runtime action-session Golden regression:
     - ARCH-017: action_count=2, record_count=4, expected SHA `f672ffaac9ef9296e4982a6fb61f4d0257b5c0506412bcf54eb1768334118c66`;
     - ARCH-021: action_count=1, record_count=3, expected SHA `4fe2c8b3c9c22821a49ff380c9635828e36f3c4a3bbbc13d2cc077dd4d97e605`;
     - ARCH-023: action_count=1, record_count=3, expected SHA `fc359b367c2922ed39e059f89ad16845ba215508292cfa43ca2ab6031c4c9ba9`.

The first ARCH-024 PR CI was green; no implementation correction was required before finalization.

## Warnings / errors

- No compile, version-compatibility, setup-parser, runner, Golden comparison, legacy-regression, trace-evidence, or runtime-regression error was observed.
- Existing GitHub Actions Node 20 deprecation warning remains nonblocking and unrelated to ARCH-024 correctness.

## Acceptance review

- Manifest schema evolution is explicitly versioned rather than silently changing v1.1.
- v1.0 and v1.1 remain strict historical grammars.
- `SKILL_POINT_GAIN` is a narrow reviewed v1.2 addition, not a generic effect DSL.
- ARCH-023 is now repeatable in the standalone runtime Golden lane.
- All three reviewed static fixture identities remain unchanged.
- Trace schema v1 and production resource emission/adapter semantics remain unchanged.
- Legacy regression remains 20/20 and trace evidence remains 2/2.
- No hidden HSR value or release-game semantic was inferred; all setup values are explicit reviewed test inputs.
- No AV/speed/advance/delay/immediate-action/extra-turn semantics were added.
- Production LIFO compatibility remains unchanged.

## Unresolved issues

None blocking HSR-RUNTIME-ARCH-024 acceptance.

The regression setup vocabulary intentionally stops at `EMPTY`, `ENERGY_GAIN`, and `SKILL_POINT_GAIN`. Consume-resource behavior and future timeline observations require separate reviewed milestones rather than generic schema broadening.

AV/speed/advance/delay/immediate-action/extra-turn state changes still lack equivalent runtime observation events.

## Suggested next milestone

`HSR-RUNTIME-ARCH-025 — Reviewed Static Energy Consume Observation Golden Fixture`

ARCH-025 should return to fixture-first discipline and add one manually constructed static schema-v1 Golden expectation for a successful production `ConsumeEnergy` action. It should lock the signed negative `requested_delta`, exact applied delta, unit scope/provenance, and `ACTION_START -> ENERGY_CHANGED -> ACTION_END` order through accepted ARCH-016. Keep it outside both regression manifests initially, do not change the v1.2 regression setup grammar, and do not combine successful consume with insufficient-resource failure semantics in the same milestone.
