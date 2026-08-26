# HSR-RUNTIME-ARCH-042 — ImmediateAction Static Golden Regression Promotion

## Status

PASS — proceed

## Task ID

`HSR-RUNTIME-ARCH-042`

## Current confirmed base

- Accepted `main` before this task: `e8492f8dd35a11b0f47fd1315e871cc5500b335c`.
- Baseline validation before this task:
  - pytest: **1635 passed in 10.25s**;
  - legacy regression: **20/20**;
  - trace evidence: **2/2**;
  - standalone runtime action-session Golden regression: **8/8**.

## Objective completed

Promoted the already accepted ARCH-041 reviewed static ImmediateAction Golden into the dedicated standalone runtime action-session regression lane as the ninth locked reviewed case, without changing production ImmediateAction semantics or the accepted Golden fixture bytes.

## Implementation summary

- Evolved `runtime_action_session_regression` manifest grammar from v1.7 to v1.8.
- Added explicit historical constant `RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_7 = "1.7"` and retained the exact supported version chain from v1.0 through v1.8.
- Preserved historical grammar boundaries:
  - `ACTION_ADVANCE` remains v1.5+;
  - `ACTION_DELAY` remains v1.6+;
  - `CHANGE_SPEED` remains v1.7+;
  - new `IMMEDIATE_ACTION` is accepted only in v1.8.
- Added frozen `RuntimeActionSessionRegressionImmediateActionSetup` with exact fields:
  - `target_id`;
  - `target_name`;
  - `team`;
  - `base_speed`;
  - `initial_av`;
  - `action_index`.
- ImmediateAction setup validation is strict:
  - exact fields only;
  - non-empty target/name/team strings;
  - finite non-boolean `base_speed` and `initial_av`;
  - positive `base_speed`;
  - exact nonnegative in-range integer `action_index`;
  - no new lower bound on `initial_av`.
- Extended the closed runner only with the explicit production construction:
  - `ImmediateAction(target_ids=[setup.target_id])` at the declared action index.
- No generic effect/action-axis DSL, dynamic import, class lookup, `eval`, `exec`, or generic kwargs path was added.
- Updated the standalone runtime manifest to v1.8 and appended the accepted ARCH-041 case as the ninth case after the existing eight.
- Preserved the first eight accepted case IDs/order and all nine reviewed Golden fixture byte identities.
- Updated historical stage-boundary tests only where prior “current = v1.7 / 8 cases” assertions had become stale:
  - ARCH-018 now validates the current nine-case lane;
  - ARCH-039 now explicitly preserves and independently reruns its historical eight-case v1.7 prefix as `8/8` rather than treating v1.7 as a permanent global ceiling.

## Ninth locked case

- Case ID: `arch-041-reviewed-static-immediate-action`
- Expected file: `hsr_axis_sim/data/runtime_golden_fixtures/arch_041_reviewed_immediate_action_expected.json`
- Expected size: **2620 bytes**
- Expected SHA-256: **`7fd1594362b5bf9a95eec6f6472b2f17afa9dcfe10196d81ec6c970eab86eea1`**
- Stream ID: `arch-041-reviewed-axis`
- Actor/target ID: `immediate-actor`
- Action: `reviewed-immediate-action`, `ends_turn=False`
- Setup: `IMMEDIATE_ACTION`, base speed `100`, initial AV `80`, action index `0`
- Runtime record count: **3**
- Accepted actual trace SHA-256 in CI run #247: **`c91ede2546175977b4612190af6e4ae68a301295236954a485684944ce929f31`**.

The actual trace digest is provenance for the generated actual trace and is not claimed to equal the pinned expected-file digest. The accepted Golden regression compares the loaded expected and actual record streams under the existing validation semantics.

## Files added

- `LUMEN_TASK_HSR_RUNTIME_ARCH_042.md`
- `hsr_axis_sim/tests/test_runtime_arch_042_immediate_action_regression_promotion.py`

## Files modified

- `hsr_axis_sim/LUMEN_RESULT.md`
- `hsr_axis_sim/data/runtime_action_session_regression_manifest.json`
- `hsr_axis_sim/runtime_action_session_regression/manifest.py`
- `hsr_axis_sim/runtime_action_session_regression/runner.py`
- `hsr_axis_sim/tests/test_runtime_arch_018_standalone_regression.py`
- `hsr_axis_sim/tests/test_runtime_arch_039_change_speed_regression_promotion.py`

## Tests added / updated

Focused ARCH-042 coverage verifies:

- exact supported versions v1.0 through v1.8;
- explicit historical v1.7 constant;
- v1.7 rejects `IMMEDIATE_ACTION`;
- v1.8 accepts the exact frozen ImmediateAction setup;
- strict missing/unknown-field rejection;
- strict identity-string validation;
- finite non-boolean numeric validation;
- positive base-speed validation;
- exact in-range action-index validation;
- zero and negative finite initial AV remain representable;
- `CHANGE_SPEED` remains valid in v1.7/v1.8 and rejected in v1.6;
- current manifest contains exactly nine cases in the accepted order;
- ninth case has exact accepted ARCH-041 path/digest/setup;
- runtime lane passes exactly `9/9` with record counts `[4, 3, 3, 3, 3, 3, 3, 3, 3]`;
- controlled harness-only `initial_av=60` mutation produces a Golden mismatch with first divergence:
  - record index `1`;
  - path `/event/payload/immediate_action/before_av`;
  - expected `80`;
  - actual `60`;
- all nine reviewed Golden fixture byte identities remain exact;
- regression harness remains explicit and closed, with no `GrantExtraTurn` support or generic loader;
- ARCH-039 historical first-eight-case prefix still independently passes `8/8`;
- legacy regression remains `20/20`;
- trace evidence remains `2/2`;
- production extra-turn LIFO remains unchanged.

## Exact commands executed by CI

```bash
python -m compileall -q hsr_axis_sim
python -m pytest -q
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --format text
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --only trace_evidence --format text
python -m hsr_axis_sim.runtime_action_session_regression.runner --manifest hsr_axis_sim/data/runtime_action_session_regression_manifest.json --format text
```

## Real validation results

GitHub Actions `HSR Axis Sim Validation`, PR #47, run **#247** (`32920547726`), job **`98033145142`**, branch head `bf574c273c3059b73ae5b9f183264ee3ec88c0e9`:

- compile: **PASS**;
- pytest: **1673 passed in 11.13s**;
- legacy locked regression: **20/20**;
- trace evidence: **2/2**;
- standalone runtime action-session Golden regression: **9/9**.

Runtime record counts were exactly:

1. `arch-017-reviewed-static-action-session` — 4;
2. `arch-021-reviewed-static-clamped-energy` — 3;
3. `arch-023-reviewed-static-clamped-skill-point` — 3;
4. `arch-025-reviewed-static-energy-consume` — 3;
5. `arch-027-reviewed-static-skill-point-consume` — 3;
6. `arch-032-reviewed-static-action-advance` — 3;
7. `arch-035-reviewed-static-action-delay` — 3;
8. `arch-038-reviewed-static-change-speed` — 3;
9. `arch-041-reviewed-static-immediate-action` — 3.

## Validation history / resolved failures

Initial PR CI run **#246** (`32920340120`) compiled successfully and produced **3 failed, 1670 passed in 10.92s**. The three failures were stale stage-boundary expectations only:

- two ARCH-018 assertions still expected the current runtime lane to contain eight cases;
- one ARCH-039 assertion still treated v1.7 as the permanent global current version.

No ARCH-042 focused setup/parser/runner/manifest/Golden test failed. Those historical tests were updated to preserve their original milestone boundaries without constraining later authorized evolution. Run #247 then passed the complete workflow.

## Controlled first-divergence proof

Changing only the ninth setup's initial AV from `80` to `60` leaves the production ImmediateAction final AV at `0`, but the accepted Golden comparison returns:

- record index: **1**;
- path: **`/event/payload/immediate_action/before_av`**;
- expected: **80**;
- actual: **60**.

No comparator or first-divergence semantics were changed.

## Locked areas confirmed unchanged

- `hsr_axis_sim/sim/**` unchanged.
- `hsr_axis_sim/runtime_contracts/**` unchanged.
- `hsr_axis_sim/runtime_adapters/**` unchanged.
- `hsr_axis_sim/data/regression_manifest.json` unchanged.
- all files under `hsr_axis_sim/data/runtime_golden_fixtures/**` unchanged, including ARCH-041.
- Golden validator/comparator/divergence implementation unchanged.
- trace schema/version unchanged.
- production Advance/Delay/ChangeSpeed/ImmediateAction behavior and events unchanged.
- `GrantExtraTurn` semantics unchanged and still unsupported by this regression grammar.
- Timeline semantics unchanged.
- production extra-turn LIFO unchanged.

## Warnings / errors

- No compile, pytest, legacy-regression, trace-evidence, or runtime-action-session-regression failure remains in run #247.
- Existing nonblocking GitHub Actions warning remains: `actions/checkout@v4` and `actions/setup-python@v5` target Node 20 and are forced onto Node 24.
- Existing upstream Node `punycode` and `url.parse()` deprecation notices remain unrelated to simulator correctness.

## Unresolved issues

None blocking HSR-RUNTIME-ARCH-042 acceptance.

`GrantExtraTurn` remains intentionally outside the runtime observation/regression surface. Actual HSR game scheduling semantics remain separate from the simulator's accepted deterministic LIFO implementation and must not be inferred without a dedicated evidence-backed task.

## Exclusions confirmation

Respected: no Golden fixture generation or modification, no legacy manifest promotion, no simulator changes, no runtime observation contract/adapter changes, no generic effect/action-axis DSL, no ImmediateAction formula/observation changes, no GrantExtraTurn support, no automatic action selection, no priority/action-family/interrupt/extra-turn inference, no comparator/divergence/Golden changes, no trace schema bump, no video parsing/scraping, no character database expansion, no AI optimization, and no unrelated UI/refactor work.

## Suggested next milestone

Do not begin a new milestone until ARCH-042 is accepted on canonical `main` with post-merge CI.

After acceptance, inspect the current repository frontier before assigning the next task. A likely candidate is a **dedicated GrantExtraTurn runtime observation contract**, but it must be scoped separately from actual HSR scheduling semantics and must preserve the accepted production LIFO behavior unless an explicit evidence-backed task authorizes otherwise.

Recommended routing if that becomes the next task: ChatGPT **GPT-5.6 Sol**; Codex reasoning **High**, because extra-turn queue semantics are core deterministic turn-order behavior.
