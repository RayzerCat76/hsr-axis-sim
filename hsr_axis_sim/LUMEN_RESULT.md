# HSR-RUNTIME-ARCH-026 — Energy Consume Static Golden Regression Promotion

## Status

PASS — proceed

## Implementation summary

- Promoted the accepted ARCH-025 successful Energy-consume static Golden fixture into the standalone runtime action-session regression lane as the fourth reviewed case.
- Evolved the strict runtime regression manifest from v1.2 to explicit v1.3 while preserving historical grammars:
  - v1.0: no `setup`;
  - v1.1: `EMPTY | ENERGY_GAIN`;
  - v1.2: `EMPTY | ENERGY_GAIN | SKILL_POINT_GAIN`;
  - v1.3: adds only `ENERGY_CONSUME`.
- Added frozen `RuntimeActionSessionRegressionEnergyConsumeSetup` with explicit Unit fields, `action_index`, and `amount`.
- `ENERGY_CONSUME` is accepted only by v1.3; v1.2 explicitly rejects it as newer syntax.
- Energy consume setup validation uses the same accepted field validation surface as Energy gain without merging the two semantics into a generic resource-effect model.
- Runner support is explicit: construct one declared Unit and inject one production `ConsumeEnergy(target_ids=[target_id], amount=amount)` on the declared action.
- Existing `EMPTY`, `ENERGY_GAIN`, and `SKILL_POINT_GAIN` runner paths remain unchanged.
- Locked manifest now contains exactly four cases in order:
  1. ARCH-017 effect-free action session — 4 records;
  2. ARCH-021 clamped Energy gain — 3 records;
  3. ARCH-023 clamped Skill-Point gain — 3 records;
  4. ARCH-025 successful Energy consume — 3 records.
- The ARCH-025 reviewed fixture remains exactly 2750 bytes at SHA-256 `7d61528687a5a2f499249e0f914f6f2f50975c7c153165eddd5e116f3ed19a75`.
- Updated historical stage-boundary tests only where the current locked lane intentionally grew to four cases or latest version became v1.3. Their v1.0/v1.1/v1.2 semantic coverage remains explicit.
- No static expected fixture bytes were modified.

## Files added

- `LUMEN_TASK_HSR_RUNTIME_ARCH_026.md`
- `docs/runtime/RUNTIME_ACTION_SESSION_REGRESSION_V1_3.md`
- `hsr_axis_sim/tests/test_runtime_arch_026_energy_consume_regression_promotion.py`

## Files modified

- `hsr_axis_sim/data/runtime_action_session_regression_manifest.json`
- `hsr_axis_sim/runtime_action_session_regression/manifest.py`
- `hsr_axis_sim/runtime_action_session_regression/runner.py`
- `hsr_axis_sim/tests/test_runtime_arch_018_standalone_regression.py`
- `hsr_axis_sim/tests/test_runtime_arch_022_resource_regression_promotion.py`
- `hsr_axis_sim/tests/test_runtime_arch_023_static_skill_point_golden_fixture.py`
- `hsr_axis_sim/tests/test_runtime_arch_024_skill_point_regression_promotion.py`
- `hsr_axis_sim/tests/test_runtime_arch_025_static_energy_consume_golden_fixture.py`
- `hsr_axis_sim/LUMEN_RESULT.md`

No `sim/**`, runtime adapter, runtime trace schema/contract, loader/exporter/comparator/divergence implementation, Golden validator, legacy regression manifest, reviewed static fixture, AV/timeline, or extra-turn/LIFO implementation was modified.

## Tests added / updated

ARCH-026 coverage proves:

- supported versions are exactly `1.0`, `1.1`, `1.2`, `1.3`;
- v1.0/v1.1/v1.2 historical grammars remain strict;
- v1.2 rejects `ENERGY_CONSUME` as requiring v1.3;
- v1.3 requires setup and accepts exactly four closed setup kinds;
- `RuntimeActionSessionRegressionEnergyConsumeSetup` is frozen;
- consume fields are exact; unknown/missing fields are rejected;
- numeric fields must be finite and non-boolean;
- `base_speed > 0`;
- `action_index` must be an exact nonnegative in-range integer;
- string fields must be non-empty;
- locked manifest order is ARCH-017 -> ARCH-021 -> ARCH-023 -> ARCH-025;
- standalone runtime lane passes exactly `4/4` with record counts `4,3,3,3`;
- controlled consume setup mutation `amount=30 -> 25` reports Golden mismatch at record index `1`, path `/event/payload/legacy_data/after`;
- all four reviewed fixture byte identities remain unchanged;
- source guards reject generic import/eval/exec/effect-class/free-kwargs mechanisms;
- legacy regression remains `20/20`;
- trace evidence remains `2/2`;
- production LIFO remains `third, second, first`.

## Exact validation commands and real results

### Initial validated PR CI

GitHub Actions workflow `HSR Axis Sim Validation`, PR #31, run #143, job `validate` (`97651198857`).

1. `python -m compileall -q hsr_axis_sim`
   - PASS.
2. `python -m pytest -q`
   - PASS: `1261 passed in 8.52s`.
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
   - PASS `4/4` runtime action-session Golden regression:
     - ARCH-017: record_count=4;
     - ARCH-021: record_count=3;
     - ARCH-023: record_count=3;
     - ARCH-025: record_count=3, expected SHA `7d61528687a5a2f499249e0f914f6f2f50975c7c153165eddd5e116f3ed19a75`.

The first ARCH-026 PR CI was green; no implementation correction was required.

## Warnings / errors

- No compile, version-compatibility, setup-parser, runner, Golden comparison, legacy-regression, trace-evidence, or runtime-regression error was observed.
- Existing GitHub Actions Node 20 deprecation warning remains nonblocking and unrelated to ARCH-026 correctness.

## Acceptance review

- Manifest evolution is explicit and version-gated rather than silently broadening v1.2.
- Historical v1.0/v1.1/v1.2 grammars remain strict and directly tested.
- `ENERGY_CONSUME` is a separate narrow typed setup, not a generic effect DSL.
- ARCH-025 is now repeatable in the standalone runtime Golden lane.
- All reviewed static fixture identities remain unchanged.
- Simulator Energy consume behavior, runtime resource adapter semantics, and trace schema v1 remain unchanged.
- Insufficient-Energy failure behavior remains out of scope.
- No hidden HSR value or release-game semantic was inferred; all regression inputs are explicit contract-only values.
- Production LIFO compatibility remains unchanged.

## Unresolved issues

None blocking HSR-RUNTIME-ARCH-026 acceptance.

The standalone setup vocabulary intentionally stops at `EMPTY`, `ENERGY_GAIN`, `SKILL_POINT_GAIN`, and `ENERGY_CONSUME`. Additional resource operations require separate reviewed milestones rather than generic schema broadening.

Insufficient-Energy failure behavior remains separate from the successful consume observation contract.

AV/speed/advance/delay/immediate-action/extra-turn state changes still lack equivalent runtime observation events.

## Suggested next milestone

`HSR-RUNTIME-ARCH-027 — Reviewed Static Skill-Point Consume Observation Golden Fixture`

ARCH-027 should return to fixture-first discipline and add one manually constructed static schema-v1 Golden expectation for a successful production `ConsumeSkillPoint` action. It should lock signed negative team-resource deltas and `ACTION_START -> SKILL_POINTS_CHANGED -> ACTION_END` through accepted ARCH-016, remain outside both regression manifests initially, and avoid combining insufficient-SP failure semantics or regression schema promotion into the same milestone.
