# HSR-RUNTIME-ARCH-039 — ChangeSpeed Static Golden Regression Promotion

## Status

PASS — proceed

## Task ID

`HSR-RUNTIME-ARCH-039`

## Implementation summary

- Promoted the already accepted ARCH-038 reviewed static ChangeSpeed Golden into the standalone runtime action-session regression lane as the eighth locked reviewed case.
- Evolved the runtime action-session regression manifest grammar from `1.6` to `1.7` while retaining an explicit historical `1.6` constant and preserving v1.0-v1.6 grammar semantics.
- Added one frozen, explicit `RuntimeActionSessionRegressionChangeSpeedSetup` with exactly:
  - `target_id`;
  - `target_name`;
  - `team`;
  - `base_speed`;
  - `initial_av`;
  - `action_index`;
  - `new_speed`.
- `CHANGE_SPEED` is accepted only by manifest v1.7. v1.6 and earlier reject it.
- `ACTION_ADVANCE` remains v1.5+ syntax; `ACTION_DELAY` remains v1.6+ syntax.
- The regression runner reconstructs the ChangeSpeed case with the real production `ChangeSpeed(target_ids=[setup.target_id], new_speed=setup.new_speed)` effect at the declared action index.
- Appended `arch-038-reviewed-static-change-speed` after the seven previously accepted runtime Golden cases; prior case order is unchanged.
- Preserved the accepted ARCH-038 fixture byte identity exactly:
  - file: `hsr_axis_sim/data/runtime_golden_fixtures/arch_038_reviewed_change_speed_expected.json`;
  - size: **2604 bytes**;
  - SHA-256: **`c23b34e0afffdfe4bee53d028e5ff21d946623300b169ba57e5ddfb69478df2a`**.
- Preserved existing comparator ordering. A controlled harness-only `new_speed=160` mutation still reports the accepted first divergence at record `1`, path `/event/payload/legacy_data/after_av`.
- Updated historical stage-boundary tests only where they had incorrectly frozen the global current manifest version or runtime-lane case count. Historical milestone semantics remain explicitly tested rather than forbidding later authorized promotions.

## Files added

- `LUMEN_TASK_HSR_RUNTIME_ARCH_039.md`
- `hsr_axis_sim/tests/test_runtime_arch_039_change_speed_regression_promotion.py`

## Files modified

- `hsr_axis_sim/LUMEN_RESULT.md`
- `hsr_axis_sim/data/runtime_action_session_regression_manifest.json`
- `hsr_axis_sim/runtime_action_session_regression/manifest.py`
- `hsr_axis_sim/runtime_action_session_regression/runner.py`
- `hsr_axis_sim/tests/test_runtime_arch_018_standalone_regression.py`
- `hsr_axis_sim/tests/test_runtime_arch_022_resource_regression_promotion.py`
- `hsr_axis_sim/tests/test_runtime_arch_024_skill_point_regression_promotion.py`
- `hsr_axis_sim/tests/test_runtime_arch_026_energy_consume_regression_promotion.py`
- `hsr_axis_sim/tests/test_runtime_arch_028_skill_point_consume_regression_promotion.py`
- `hsr_axis_sim/tests/test_runtime_arch_033_action_advance_regression_promotion.py`
- `hsr_axis_sim/tests/test_runtime_arch_034_delay_action_observation.py`
- `hsr_axis_sim/tests/test_runtime_arch_035_static_action_delay_golden_fixture.py`
- `hsr_axis_sim/tests/test_runtime_arch_036_action_delay_regression_promotion.py`
- `hsr_axis_sim/tests/test_runtime_arch_037_change_speed_observation.py`
- `hsr_axis_sim/tests/test_runtime_arch_038_static_change_speed_golden_fixture.py`

## Tests added / updated

Focused ARCH-039 coverage verifies:

- supported manifest versions are exactly v1.0 through v1.7;
- explicit historical v1.6 constant is retained;
- v1.6 rejects `CHANGE_SPEED`;
- v1.7 accepts the exact frozen ChangeSpeed setup;
- unknown, missing, or extra setup fields are rejected;
- target/name/team require non-empty strings;
- `base_speed`, `initial_av`, and `new_speed` require finite non-boolean numbers;
- `base_speed > 0` and `new_speed > 0`;
- finite zero/negative `initial_av` remains representable without a new floor;
- `action_index` is an exact in-range nonnegative integer;
- `ACTION_ADVANCE` and `ACTION_DELAY` retain their previously accepted version boundaries;
- current manifest is v1.7 with exactly eight ordered cases;
- the first seven case identities and fixture digests remain unchanged;
- eighth case is the exact ARCH-038 ChangeSpeed fixture and produces three records;
- the standalone runtime lane passes `8/8` with record counts `[4, 3, 3, 3, 3, 3, 3, 3]`;
- controlled `new_speed=160` reports the accepted first divergence at record 1, `/event/payload/legacy_data/after_av`;
- all eight reviewed static Golden fixture byte identities remain exact;
- the harness remains closed and explicit, with no generic effect DSL;
- legacy regression remains `20/20`;
- trace evidence remains `2/2`;
- production extra-turn LIFO remains `third, second, first`.

Historical stage-boundary tests were adjusted only to stop treating their then-current version/case count as a permanent global ceiling. Their original feature semantics and prefix identities remain covered.

## Exact commands executed by CI

```bash
python -m compileall -q hsr_axis_sim
python -m pytest -q
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --format text
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --only trace_evidence --format text
python -m hsr_axis_sim.runtime_action_session_regression.runner --manifest hsr_axis_sim/data/runtime_action_session_regression_manifest.json --format text
```

## Real validation results

GitHub Actions `HSR Axis Sim Validation`, PR #44, run **#230**, job **`97708546285`**, on branch head `a763d1b9982c44ab010eeea14438f028acc7c5d3`:

- compile: **PASS**;
- pytest: **1601 passed in 10.08s**;
- legacy locked regression: **20/20**;
- trace evidence: **2/2**;
- standalone runtime action-session Golden regression: **8/8**.

Runtime Golden case order and record counts:

1. `arch-017-reviewed-static-action-session` — 4 records — PASS;
2. `arch-021-reviewed-static-clamped-energy` — 3 records — PASS;
3. `arch-023-reviewed-static-clamped-skill-point` — 3 records — PASS;
4. `arch-025-reviewed-static-energy-consume` — 3 records — PASS;
5. `arch-027-reviewed-static-skill-point-consume` — 3 records — PASS;
6. `arch-032-reviewed-static-action-advance` — 3 records — PASS;
7. `arch-035-reviewed-static-action-delay` — 3 records — PASS;
8. `arch-038-reviewed-static-change-speed` — 3 records — PASS.

The eighth production-generated actual trace passed comparison against the accepted ARCH-038 static expectation. Its expected SHA-256 remained `c23b34e0afffdfe4bee53d028e5ff21d946623300b169ba57e5ddfb69478df2a`.

## Validation history / resolved failures

Earlier PR CI runs failed only because older stage-boundary tests still hard-coded global current manifest version `1.6` or runtime case count `7`. Those failures were used to identify and narrow the stale assertions. No ChangeSpeed setup, production runner, Golden comparison, fixture identity, or divergence test failed in those runs.

After the historical-boundary assertions were corrected, run #230 passed the complete workflow including all three regression lanes.

## Locked areas confirmed unchanged

- `hsr_axis_sim/sim/**` unchanged.
- `hsr_axis_sim/runtime_contracts/**` unchanged.
- `hsr_axis_sim/runtime_adapters/**` unchanged.
- Golden validator/comparator/divergence implementation unchanged.
- trace loader/exporter/stitching implementation unchanged.
- `hsr_axis_sim/data/regression_manifest.json` unchanged.
- all files under `hsr_axis_sim/data/runtime_golden_fixtures/**` unchanged; ARCH-038 remains exactly 2604 bytes with the pinned SHA-256 above.
- production `AdvanceAction`, `DelayAction`, and `ChangeSpeed` formulas/events unchanged.
- `ImmediateAction` and `GrantExtraTurn` semantics unchanged.
- trace schema/version unchanged.
- production extra-turn LIFO behavior unchanged.

## Warnings / errors

- No compile, pytest, legacy-regression, trace-evidence, or runtime-action-session-regression failure remains.
- Nonblocking GitHub Actions warning remains: `actions/checkout@v4` and `actions/setup-python@v5` target Node 20 and are forced onto Node 24.
- Upstream action setup continues to emit Node `punycode` and `url.parse()` deprecation notices. These warnings predate ARCH-039 and are unrelated to simulator correctness.

## Unresolved issues

None blocking HSR-RUNTIME-ARCH-039 acceptance.

`ImmediateAction` and `GrantExtraTurn` still do not have equivalent dedicated runtime observation contracts. They remain out of scope for this milestone.

The Master Bible summary remains historically stale relative to the narrow runtime frontier; ARCH-039 intentionally does not broaden scope into governance synchronization.

## Exclusions confirmation

Respected: no production simulator changes, no runtime observation-contract changes, no adapter/schema/comparator/divergence/Golden changes, no static fixture generation or modification, no legacy regression-manifest promotion, no generic effect/action-axis DSL, no `ImmediateAction` support, no `GrantExtraTurn` support, no automatic action selection, no video parsing/scraping, no character database work, no AI optimization, and no unrelated UI/refactor work.

## Suggested next milestone

`HSR-RUNTIME-ARCH-040 — ImmediateAction Runtime Observation Contract`

Inspect and expose only the existing production `ImmediateAction` behavior through a dedicated deterministic runtime observation contract, preserving all accepted simulator semantics and keeping `GrantExtraTurn` separate. Do not create a static Golden or regression promotion until the observation contract itself is accepted.

Recommended execution routing: ChatGPT **GPT-5.6 Sol**; Codex reasoning **High** because immediate-turn scheduling/ordering is deterministic core timeline behavior.
