# HSR-RUNTIME-ARCH-036 — Delay Static Golden Regression Promotion

## Status

PASS — proceed

## Implementation summary

- Promoted the accepted ARCH-035 reviewed static Delay Golden fixture into the dedicated standalone runtime action-session regression lane as the seventh locked case.
- Evolved the standalone runtime regression manifest grammar from v1.5 to v1.6 while preserving the previously accepted v1.0-v1.5 grammar explicitly.
- Added explicit historical constant `RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_5 = "1.5"` and set current `RUNTIME_ACTION_SESSION_REGRESSION_VERSION = "1.6"`.
- Supported manifest versions are now exactly `("1.0", "1.1", "1.2", "1.3", "1.4", "1.5", "1.6")`.
- Preserved closed version semantics:
  - `ACTION_ADVANCE` remains v1.5+ syntax and remains rejected in v1.4 and earlier;
  - new `ACTION_DELAY` is valid only in v1.6 and is rejected in v1.5 and earlier;
  - all prior ENERGY/SKILL_POINT setup version gates retain v1.5 explicitly after the current version moved to v1.6.
- Added frozen `RuntimeActionSessionRegressionActionDelaySetup` with only the reviewed explicit fields: target identity/name/team, base speed, initial AV, action index, and percent.
- Delay setup validation requires exact fields, non-empty identity strings, finite non-boolean numeric values, positive base speed, and an exact in-range nonnegative action index. It intentionally adds no positivity restriction on percent and no lower bound on initial AV.
- Kept Advance and Delay setup parsers independent. An intermediate shared action-axis helper was removed before review so this milestone does not introduce a generic action-axis/effect abstraction.
- Extended the standalone runner only enough to:
  - build the declared Unit for `ACTION_DELAY`;
  - inject exactly `DelayAction(target_ids=[setup.target_id], percent=setup.percent)` at the declared action index;
  - continue delegating execution/trace/Golden semantics to the accepted runtime action-session pipeline.
- Updated `hsr_axis_sim/data/runtime_action_session_regression_manifest.json` to v1.6 and appended exactly one seventh case:
  - id `arch-035-reviewed-static-action-delay`;
  - fixture `arch_035_reviewed_action_delay_expected.json`;
  - expected SHA-256 `9efbb65defb5eacc12150d31d0530d9a94b43a42e2303ebca643911f98094c4d`;
  - stream `arch-035-reviewed-axis`;
  - actor/target `delay-actor`;
  - base speed `100`;
  - initial AV `30`;
  - percent `0.25`;
  - real production Delay result `55.0`.
- Preserved all first six runtime regression case identities and order unchanged.
- Updated historical/current-state tests only where their prior fixed `v1.5`, `6/6`, or "ARCH-035 is unpromoted" assertions were intentionally superseded by ARCH-036. Historical grammar/prefix guarantees remain explicitly tested.
- Corrected one task/test assumption exposed by real CI: the generated actual trace artifact SHA is provenance and is not required to equal the static expected fixture SHA because accepted Golden comparison permits differing trace/document metadata while comparing the ordered runtime records. No comparator or production behavior was changed to force digest equality.

## Files added

- `LUMEN_TASK_HSR_RUNTIME_ARCH_036.md`
- `hsr_axis_sim/tests/test_runtime_arch_036_action_delay_regression_promotion.py`

## Files modified

- `hsr_axis_sim/data/runtime_action_session_regression_manifest.json`
- `hsr_axis_sim/runtime_action_session_regression/manifest.py`
- `hsr_axis_sim/runtime_action_session_regression/runner.py`
- `hsr_axis_sim/tests/test_runtime_arch_018_standalone_regression.py`
- `hsr_axis_sim/tests/test_runtime_arch_022_resource_regression_promotion.py`
- `hsr_axis_sim/tests/test_runtime_arch_024_skill_point_regression_promotion.py`
- `hsr_axis_sim/tests/test_runtime_arch_026_energy_consume_regression_promotion.py`
- `hsr_axis_sim/tests/test_runtime_arch_028_skill_point_consume_regression_promotion.py`
- `hsr_axis_sim/tests/test_runtime_arch_032_static_action_advance_golden_fixture.py`
- `hsr_axis_sim/tests/test_runtime_arch_033_action_advance_regression_promotion.py`
- `hsr_axis_sim/tests/test_runtime_arch_034_delay_action_observation.py`
- `hsr_axis_sim/tests/test_runtime_arch_035_static_action_delay_golden_fixture.py`
- `hsr_axis_sim/LUMEN_RESULT.md`

## Locked areas confirmed unchanged

- `hsr_axis_sim/data/regression_manifest.json` unchanged.
- Every file under `hsr_axis_sim/data/runtime_golden_fixtures/**` remains byte-identical, including ARCH-035 at exactly `2728` bytes and SHA-256 `9efbb65defb5eacc12150d31d0530d9a94b43a42e2303ebca643911f98094c4d`.
- No `hsr_axis_sim/sim/**` file changed.
- No `runtime_contracts/**` or `runtime_adapters/**` file changed.
- No trace schema, loader/exporter, comparator, divergence, or Golden implementation changed.
- `runtime_action_session_regression/__init__.py` remains unchanged.
- Production Advance and Delay formulas/events remain unchanged.
- ChangeSpeed, ImmediateAction, and GrantExtraTurn remain out of scope.
- Production extra-turn LIFO compatibility remains unchanged.

## Tests added / updated

Focused ARCH-036 coverage proves:

- exact version history through v1.6 with explicit v1.5 constant;
- v1.5 rejects `ACTION_DELAY` and v1.6 accepts it;
- v1.5/v1.6 both accept `ACTION_ADVANCE`, while v1.4 rejects it;
- Delay setup is frozen and exact-field strict;
- identity strings are non-empty;
- numeric fields are finite non-booleans;
- base speed is positive;
- action index is an exact in-range nonnegative integer;
- zero/negative Delay percent and zero/negative initial AV remain representable at the manifest layer;
- current manifest contains exactly seven cases with the accepted first-six prefix unchanged;
- seventh case uses the exact ARCH-035 fixture path/digest and explicit Delay setup;
- runtime lane passes `7/7` with record counts `[4, 3, 3, 3, 3, 3, 3]`;
- controlled Delay percent `0.25 -> 0.20` yields a normal Golden mismatch at record index `1`, first path `/event/payload/action_delay/after_av`;
- all seven reviewed static fixture byte identities remain exact;
- the runner remains a closed explicit setup grammar with no generic effect DSL/dynamic import/eval/exec;
- legacy regression remains `20/20`;
- trace evidence remains `2/2`;
- LIFO remains `third, second, first`.

Historical milestone tests were updated only to distinguish immutable historical guarantees from the intentionally evolving current standalone regression state. In particular, ARCH-033 still runs the first six accepted cases separately as `6/6`, and ARCH-032 still locks the first-six case prefix.

## Exact validation commands and real results

### Initial PR CI — expected correction cycle

GitHub Actions workflow `HSR Axis Sim Validation`, PR #41, run #194.

- Compile passed.
- Full pytest: `13 failed, 1490 passed in 9.56s`.
- The 13 failures were reviewed individually:
  - 12 were stale tests that intentionally still asserted current v1.5 / 6 cases / ARCH-035 unpromoted;
  - 1 was a new ARCH-036 test incorrectly asserting generated actual artifact SHA must equal the static expected fixture SHA.
- No production, fixture, adapter, runtime observation, comparator, or Golden implementation defect was found.
- The stale assertions were updated to preserve historical version/prefix semantics while recognizing the authorized v1.6/7-case promotion.
- The actual-SHA assertion and task wording were corrected to match the already accepted Golden semantics rather than changing production/Golden behavior.

### Corrected implementation CI

GitHub Actions workflow `HSR Axis Sim Validation`, PR #41, run #204, job `validate` (`97681421653`).

1. `python -m compileall -q hsr_axis_sim`
   - PASS.
2. `python -m pytest -q`
   - PASS: `1503 passed in 8.14s`.
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
   - PASS `7/7` runtime action-session Golden checks.
   - seventh case:
     - `expected_sha256=9efbb65defb5eacc12150d31d0530d9a94b43a42e2303ebca643911f98094c4d`;
     - `actual_sha256=c47754957a756bd03624aafdcd78e14ecbaed059cce0c99fddb0d116c88bde77`;
     - `record_count=3`;
     - PASS through accepted Golden comparison.

## Warnings / errors

- Corrected CI has no compile, pytest, legacy-regression, trace-evidence, or standalone-runtime-regression failure.
- Existing GitHub Actions warning remains nonblocking: `actions/checkout@v4` and `actions/setup-python@v5` target Node 20 and are being forced to run on Node 24.
- GitHub Actions also emits upstream Node deprecation notices for `punycode` / `url.parse()` during action setup; these are unrelated to simulator correctness.

## Acceptance review

- Manifest grammar evolution is explicit and version-closed; older versions were not silently broadened.
- Delay setup remains its own explicit typed contract; no generic action-axis/effect DSL was introduced.
- Runner executes the real production `DelayAction`, so the seventh case is not an empty-action false positive.
- Controlled percent mutation proves the structured Delay observation participates in Golden divergence reporting at the expected first record/path.
- Expected fixture identity remains pinned independently from actual generated artifact identity.
- Static expected bytes were not regenerated or modified.
- The legacy regression lane remains separate and unchanged at `20/20`.
- Standalone runtime regression is now exactly `7/7`.
- No adjacent action-axis mechanic was implemented early.
- No hidden HSR values or release-game semantics were inferred.
- Production LIFO compatibility remains unchanged.

## Unresolved issues

None blocking HSR-RUNTIME-ARCH-036 acceptance.

The current Master Bible / Decision Log governance summaries remain older than the recent small runtime milestones; this task intentionally did not turn a narrow regression-promotion PR into a broad governance rewrite.

ChangeSpeed, ImmediateAction, and GrantExtraTurn still lack equivalent runtime observation contracts.

## Suggested next milestone

`HSR-RUNTIME-ARCH-037 — ChangeSpeed Runtime Observation Contract`

ARCH-037 should first inspect and lock the existing production `ChangeSpeed` formula and edge conditions, then add only the smallest deterministic production event, dedicated typed runtime observation, strict legacy-adapter binding, trigger-order test, and ARCH-012 capture proof. Do not generalize Advance/Delay/ChangeSpeed into one axis-effect abstraction yet, and do not create a static Golden fixture in the same milestone.

Recommended execution routing: ChatGPT **GPT-5.6 Sol**; Codex reasoning **High** if Codex is used.