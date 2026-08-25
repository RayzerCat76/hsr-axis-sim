# HSR-RUNTIME-ARCH-028 — Skill-Point Consume Static Golden Regression Promotion

## Status

PASS — proceed

## Implementation summary

- Promoted the accepted ARCH-027 successful Skill-Point-consume static Golden fixture into the standalone runtime action-session regression lane as the fifth reviewed case.
- Evolved the strict runtime regression manifest from v1.3 to explicit v1.4 while preserving historical grammars:
  - v1.0: no `setup`;
  - v1.1: `EMPTY | ENERGY_GAIN`;
  - v1.2: `EMPTY | ENERGY_GAIN | SKILL_POINT_GAIN`;
  - v1.3: `EMPTY | ENERGY_GAIN | SKILL_POINT_GAIN | ENERGY_CONSUME`;
  - v1.4: adds only `SKILL_POINT_CONSUME`.
- Added frozen `RuntimeActionSessionRegressionSkillPointConsumeSetup` with exact fields:
  - `initial_skill_points`;
  - `max_skill_points`;
  - `action_index`;
  - `amount`.
- `SKILL_POINT_CONSUME` is accepted only by v1.4; v1.3 explicitly rejects it as newer syntax.
- Skill-Point consume setup validation reuses the accepted exact-integer/action-index validation surface without merging gain and consume into a generic mode/effect model.
- Runner support is explicit:
  - construct `BattleState([], skill_points=initial_skill_points, max_skill_points=max_skill_points)`;
  - inject one production `ConsumeSkillPoint(amount=amount)` on the declared action;
  - leave other actions effect-free.
- Existing `EMPTY`, `ENERGY_GAIN`, `SKILL_POINT_GAIN`, and `ENERGY_CONSUME` runner paths remain behaviorally unchanged.
- Locked manifest now contains exactly five cases in order:
  1. ARCH-017 effect-free action session — 4 records;
  2. ARCH-021 clamped Energy gain — 3 records;
  3. ARCH-023 clamped Skill-Point gain — 3 records;
  4. ARCH-025 successful Energy consume — 3 records;
  5. ARCH-027 successful Skill-Point consume — 3 records.
- ARCH-027 fixture remains exactly 2796 bytes at SHA-256 `d0dcf128f3a28f691324f4e9295b7bcd66460598186f6059d4619f55e8ae39ec`.
- Historical stage-boundary tests were updated only where the current locked lane intentionally grew to five cases or latest version became v1.4. v1.1/v1.2/v1.3 semantic tests now use explicit version constants where needed.
- No reviewed static fixture bytes were modified.

## Files added

- `LUMEN_TASK_HSR_RUNTIME_ARCH_028.md`
- `docs/runtime/RUNTIME_ACTION_SESSION_REGRESSION_V1_4.md`
- `hsr_axis_sim/tests/test_runtime_arch_028_skill_point_consume_regression_promotion.py`

## Files modified

- `hsr_axis_sim/data/runtime_action_session_regression_manifest.json`
- `hsr_axis_sim/runtime_action_session_regression/manifest.py`
- `hsr_axis_sim/runtime_action_session_regression/runner.py`
- `hsr_axis_sim/tests/test_runtime_arch_018_standalone_regression.py`
- `hsr_axis_sim/tests/test_runtime_arch_022_resource_regression_promotion.py`
- `hsr_axis_sim/tests/test_runtime_arch_023_static_skill_point_golden_fixture.py`
- `hsr_axis_sim/tests/test_runtime_arch_024_skill_point_regression_promotion.py`
- `hsr_axis_sim/tests/test_runtime_arch_025_static_energy_consume_golden_fixture.py`
- `hsr_axis_sim/tests/test_runtime_arch_026_energy_consume_regression_promotion.py`
- `hsr_axis_sim/tests/test_runtime_arch_027_static_skill_point_consume_golden_fixture.py`
- `hsr_axis_sim/LUMEN_RESULT.md`

No `sim/**`, runtime adapter, runtime trace schema/contract, loader/exporter/comparator/divergence implementation, Golden validator, legacy regression manifest, reviewed static fixture, AV/timeline, or extra-turn/LIFO implementation was modified.

## Tests added / updated

ARCH-028 coverage proves:

- supported versions are exactly `1.0`, `1.1`, `1.2`, `1.3`, `1.4`;
- v1.0-v1.3 historical grammars remain strict;
- v1.3 rejects `SKILL_POINT_CONSUME` as requiring v1.4;
- v1.4 requires `setup` and accepts exactly five closed setup kinds;
- `RuntimeActionSessionRegressionSkillPointConsumeSetup` is frozen;
- unknown/missing Skill-Point consume fields are rejected;
- `initial_skill_points`, `max_skill_points`, and `amount` require exact integers and reject booleans/non-integers;
- `action_index` requires an exact nonnegative in-range integer and rejects booleans/non-integers;
- locked manifest order is ARCH-017 -> ARCH-021 -> ARCH-023 -> ARCH-025 -> ARCH-027;
- standalone runtime lane passes exactly `5/5` with record counts `4,3,3,3,3`;
- controlled fifth-case mutation `amount=2 -> 1` reports Golden mismatch at record index `1`, path `/event/payload/legacy_data/after`;
- all five reviewed fixture byte identities remain unchanged;
- source guards reject dynamic import/eval/exec/effect-class/free-kwargs generic effect mechanisms;
- legacy regression remains `20/20`;
- trace evidence remains `2/2`;
- production LIFO remains `third, second, first`.

## Exact validation commands and real results

### Initial validated PR CI

GitHub Actions workflow `HSR Axis Sim Validation`, PR #33, run #149, job `validate` (`97655857840`).

1. `python -m compileall -q hsr_axis_sim`
   - PASS.
2. `python -m pytest -q`
   - PASS: `1303 passed in 8.23s`.
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
   - PASS `5/5` runtime action-session Golden regression:
     - ARCH-017: record_count=4;
     - ARCH-021: record_count=3;
     - ARCH-023: record_count=3;
     - ARCH-025: record_count=3;
     - ARCH-027: record_count=3, expected SHA `d0dcf128f3a28f691324f4e9295b7bcd66460598186f6059d4619f55e8ae39ec`.

The first ARCH-028 PR CI was green; no implementation correction was required.

## Warnings / errors

- No compile, version-compatibility, setup-parser, runner, Golden comparison, legacy-regression, trace-evidence, or runtime-regression error was observed.
- Existing GitHub Actions Node 20 deprecation warning remains nonblocking and unrelated to ARCH-028 correctness.

## Acceptance review

- Manifest evolution is explicit and version-gated rather than silently broadening v1.3.
- Historical v1.0-v1.3 grammars remain strict and directly tested.
- `SKILL_POINT_CONSUME` is a separate narrow typed setup, not a generic effect DSL.
- ARCH-027 is now repeatable in the standalone runtime Golden lane.
- All five reviewed static fixture identities remain unchanged.
- Simulator Skill-Point consume behavior, runtime resource adapter semantics, and trace schema v1 remain unchanged.
- Insufficient-Skill-Point failure behavior remains out of scope.
- No hidden HSR value or release-game semantic was inferred; all regression inputs are explicit contract-only values.
- Production LIFO compatibility remains unchanged.

## Unresolved issues

None blocking HSR-RUNTIME-ARCH-028 acceptance.

The standalone successful-resource setup vocabulary now covers Energy gain, Skill-Point gain, Energy consume, and Skill-Point consume. Insufficient-resource failure behavior remains deliberately separate because it is an exception/partial-action path rather than a successful three-record resource observation.

AV/speed/advance/delay/immediate-action/extra-turn state changes still lack equivalent runtime observation events.

## Suggested next milestone

`HSR-RUNTIME-ARCH-029 — Insufficient Skill-Point Action Failure Contract`

ARCH-029 should inspect and lock the production `ConsumeSkillPoint` insufficient-resource failure path without changing successful resource semantics. It should document exactly which action events/state mutations exist before the exception, preserve the original exception and accepted non-transactional capture-session behavior, avoid inventing a successful Golden trace for a failed action, and keep insufficient Energy as a separate later milestone unless the exact production failure contracts prove structurally identical and combining them is explicitly justified.
