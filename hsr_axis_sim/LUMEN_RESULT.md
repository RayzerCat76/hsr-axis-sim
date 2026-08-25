# HSR-RUNTIME-ARCH-033 — Advance Static Golden Regression Promotion

## Status

PASS — proceed

## Implementation summary

- Promoted the accepted ARCH-032 reviewed static `AdvanceAction` Golden fixture into the standalone runtime action-session regression lane as the sixth locked case.
- Evolved the strict standalone manifest grammar from v1.4 to v1.5 while preserving historical v1.0-v1.4 grammars explicitly.
- Added `RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_4 = "1.4"` and made the current version `"1.5"` with supported versions exactly `1.0` through `1.5`.
- Added frozen `RuntimeActionSessionRegressionActionAdvanceSetup` with exact fields:
  - `target_id`;
  - `target_name`;
  - `team`;
  - `base_speed`;
  - `initial_av`;
  - `action_index`;
  - `percent`.
- Added only the new closed v1.5 setup kind `ACTION_ADVANCE`.
- Historical grammar remains strict:
  - v1.0: no `setup` field;
  - v1.1: `EMPTY | ENERGY_GAIN`;
  - v1.2 adds `SKILL_POINT_GAIN`;
  - v1.3 adds `ENERGY_CONSUME`;
  - v1.4 adds `SKILL_POINT_CONSUME`;
  - v1.5 adds `ACTION_ADVANCE` only.
- v1.4 explicitly rejects `ACTION_ADVANCE` as requiring v1.5.
- `ACTION_ADVANCE` setup validation requires non-empty identity/team strings, finite non-boolean `base_speed`, `initial_av`, and `percent`, positive `base_speed`, and an exact in-range nonnegative integer `action_index`.
- The regression grammar does not silently restrict `percent` to positive values and does not invent a new `initial_av` range rule.
- Runner support constructs one explicit production `Unit` with caller-declared `base_speed` and `current_av`, then injects exactly `AdvanceAction(target_ids=[setup.target_id], percent=setup.percent)` at the declared action index.
- Appended exact sixth locked case:
  - case id `arch-032-reviewed-static-action-advance`;
  - expected fixture `hsr_axis_sim/data/runtime_golden_fixtures/arch_032_reviewed_action_advance_expected.json`;
  - expected SHA-256 `ab73c224d06690b379d398a5bc2c4b38a1ed654dfd86866d564417432c29d3ce`;
  - stream `arch-032-reviewed-axis`;
  - actor/target `advance-actor`;
  - action `reviewed-action-advance`;
  - speed `100`;
  - initial AV `80`;
  - percent `0.5`.
- The locked standalone runtime lane is now exactly `6/6`, with record counts `4,3,3,3,3,3`.
- Controlled regression mutation `percent=0.5 -> 0.4` fails normally at record index `1`, first divergence `/event/payload/action_advance/after_av`.
- Existing historical tests were changed from stale current-count aliases into explicit historical grammar/prefix assertions. No historical behavior coverage was removed.
- During review, full-file replacement formatting noise in ARCH-025/026/027 tests was detected and removed before final validation; their final diffs contain only the intended append-safe assertion changes.
- No simulator `AdvanceAction` semantics, reviewed fixture bytes, legacy regression manifest, runtime observation contract, adapter, trace schema, or LIFO behavior changed.

## Files added

- `LUMEN_TASK_HSR_RUNTIME_ARCH_033.md`
- `hsr_axis_sim/tests/test_runtime_arch_033_action_advance_regression_promotion.py`

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
- `hsr_axis_sim/tests/test_runtime_arch_028_skill_point_consume_regression_promotion.py`
- `hsr_axis_sim/tests/test_runtime_arch_029_insufficient_skill_point_failure_contract.py`
- `hsr_axis_sim/tests/test_runtime_arch_030_insufficient_energy_failure_contract.py`
- `hsr_axis_sim/tests/test_runtime_arch_032_static_action_advance_golden_fixture.py`
- `hsr_axis_sim/LUMEN_RESULT.md`

No `hsr_axis_sim/sim/**`, reviewed static Golden fixture, `hsr_axis_sim/data/regression_manifest.json`, runtime adapter, runtime trace contract/schema, loader/exporter/comparator/divergence implementation, Golden validator, Delay/ChangeSpeed/ImmediateAction/GrantExtraTurn behavior, or extra-turn/LIFO implementation was modified.

## Tests added / updated

ARCH-033 coverage proves:

- supported standalone manifest versions are exactly `1.0` through `1.5`;
- v1.0-v1.4 historical setup grammars remain accepted/rejected exactly as previously locked;
- v1.4 rejects `ACTION_ADVANCE` as v1.5-only syntax;
- v1.5 requires `setup` and accepts the new closed `ACTION_ADVANCE` setup;
- `RuntimeActionSessionRegressionActionAdvanceSetup` is frozen;
- setup fields are exact and unknown fields/kinds are rejected;
- target identity/team values require non-empty strings;
- numeric fields require finite non-boolean numbers;
- `base_speed` must be positive;
- `action_index` must be an exact in-range nonnegative integer;
- zero/negative `percent` remains parseable because the regression grammar does not narrow accepted production input semantics;
- finite zero/negative `initial_av` is not newly range-restricted by this promotion layer;
- current manifest case order is exactly ARCH-017, ARCH-021, ARCH-023, ARCH-025, ARCH-027, ARCH-032;
- sixth case fields/setup/digest/path are exact;
- runtime regression passes exactly `6/6` with record counts `4,3,3,3,3,3`;
- controlled percent `0.4` mismatch reports record `1` and `/event/payload/action_advance/after_av`;
- all six reviewed fixture byte identities remain unchanged;
- runner uses an explicit target and remains a closed typed harness rather than a generic effect DSL;
- no Delay/ChangeSpeed/ImmediateAction/GrantExtraTurn support is introduced;
- historical milestone tests preserve their own prefix/grammar contracts without freezing the current lane count permanently;
- legacy regression remains `20/20`;
- trace evidence remains `2/2`;
- production LIFO remains `third, second, first`.

## Exact validation commands and real results

### First PR CI — stale historical count/version pins exposed

GitHub Actions workflow `HSR Axis Sim Validation`, PR #38, run #168, job `validate` (`97667940147`).

1. `python -m compileall -q hsr_axis_sim`
   - PASS.
2. `python -m pytest -q`
   - `1394 passed, 15 failed in 8.83s`.
   - All 15 failures were historical tests that had encoded an earlier milestone's then-current state as a permanent assertion, including `current version == 1.4`, `total == 5`, or text `PASS 5/5`.
   - The new sixth `ACTION_ADVANCE` regression case itself executed successfully in the failing run and produced a three-record actual trace.
   - No ARCH-033 parser, runner, fixture digest, production Advance behavior, or controlled mismatch test failed.
3. Later regression workflow steps were skipped only because the complete pytest step failed.

Corrections changed only historical test boundaries: each earlier milestone now locks its own historical version/prefix while allowing later reviewed cases to append. No production or fixture behavior was changed to satisfy these failures.

### Corrected clean-head PR CI

GitHub Actions workflow `HSR Axis Sim Validation`, PR #38, run #180, job `validate` (`97669992751`).

1. `python -m compileall -q hsr_axis_sim`
   - PASS.
2. `python -m pytest -q`
   - PASS: `1409 passed in 9.52s`.
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
   - PASS `6/6` runtime action-session Golden checks.
   - Record counts: `4,3,3,3,3,3`.
   - Sixth case expected SHA-256: `ab73c224d06690b379d398a5bc2c4b38a1ed654dfd86866d564417432c29d3ce`.
   - Sixth case actual SHA-256: `13d26b8efcb0db450445c036f49b31eec4ca346ca9d714f7e221bc084941a6ca`.
   - Sixth case record count: `3`.

## Warnings / errors

- First CI exposed 15 stale historical version/count assertions; all were corrected without altering production Advance semantics or reviewed fixture bytes.
- Review also caught temporary formatting-only diff noise in three historical test files; it was removed before the corrected clean-head validation.
- No remaining compile, manifest-v1.5, ActionAdvance setup, runner construction, fixture digest, Golden comparison, legacy-regression, trace-evidence, or runtime-regression error is known.
- Existing GitHub Actions Node 20 deprecation warning remains nonblocking and unrelated to ARCH-033 correctness.

## Acceptance review

- ARCH-032 fixture bytes and SHA remain unchanged.
- The sixth locked runtime case uses the accepted static fixture rather than generating expected bytes dynamically.
- Manifest evolution is explicit and versioned; old grammars remain strict rather than being silently broadened.
- Runner construction is deterministic and explicitly targeted.
- `ACTION_ADVANCE` is the only new setup kind; no adjacent action-axis mechanism was introduced early.
- Regression mutation proves first-divergence behavior at the typed structured observation field.
- Legacy regression remains separate and unchanged at `20/20`.
- Runtime action-session regression is now independently locked at `6/6`.
- No hidden HSR values or release-game semantics were inferred; speed `100`, AV `80`, and percent `0.5` are explicit reviewed fixture inputs.
- Production LIFO compatibility remains unchanged.

## Unresolved issues

None blocking HSR-RUNTIME-ARCH-033 acceptance.

The Advance observation path is now complete through production emission, typed adaptation, independently reviewed static Golden validation, and locked runtime regression promotion.

The next unobserved deterministic action-axis mutation should be handled as a separate mechanic rather than extending the Advance contract generically.

## Suggested next milestone

`HSR-RUNTIME-ARCH-034 — Delay Action Runtime Observation Contract`

ARCH-034 should inspect the existing production `DelayAction` formula and add the smallest dedicated typed runtime observation for one delay transition, preserving the current simulator formula/input semantics exactly. It should remain separate from ChangeSpeed, ImmediateAction, and GrantExtraTurn, and should not create a generic action-axis event DSL.

Recommended execution routing: ChatGPT **GPT-5.6 Sol**; Codex reasoning **High** if Codex is used, because this changes deterministic action-axis observation semantics and must preserve exact timeline behavior.
