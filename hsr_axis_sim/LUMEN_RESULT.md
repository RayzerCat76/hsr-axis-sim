# HSR-RUNTIME-ARCH-035 — Reviewed Static Delay Action Golden Fixture

## Status

PASS — proceed

## Implementation summary

- Added one independently reviewed static schema-v1 Golden expectation for the accepted production Delay observation.
- Static fixture:
  - `hsr_axis_sim/data/runtime_golden_fixtures/arch_035_reviewed_action_delay_expected.json`;
  - exactly `2728` bytes;
  - SHA-256 `9efbb65defb5eacc12150d31d0530d9a94b43a42e2303ebca643911f98094c4d`;
  - compact canonical UTF-8 JSON;
  - no trailing newline;
  - trace ID `arch-035-reviewed-static-expected`.
- Reviewed deterministic scenario:
  - fixture id `arch-035-reviewed-static-action-delay`;
  - stream `arch-035-reviewed-axis`;
  - actor/target `delay-actor`;
  - Unit name `Delay Actor`;
  - team `ally`;
  - base speed `100`;
  - initial AV `30`;
  - action `reviewed-action-delay`;
  - `DelayAction(percent=0.25)`;
  - `ends_turn=False`;
  - final AV `55.0`.
- Static record order is exactly `ACTION_START -> ACTION_VALUE_DELAYED -> ACTION_END`.
- Delay observation locks exactly:
  - `target_id="delay-actor"`;
  - `before_av=30`;
  - `after_av=55.0`;
  - `base_av=100.0`;
  - `requested_percent=0.25`;
  - `requested_delta_av=25.0`;
  - `applied_delta_av=25.0`.
- No `clamped_to_zero` field exists in typed `action_delay` or raw Delay `legacy_data`.
- Raw `legacy_data` and typed `action_delay` are both explicitly present.
- Every record keeps `numeric_values={}` under schema v1.
- The expected artifact was manually specified from the accepted schema/runtime contract, not generated from simulator, adapter, trace-builder, exporter, or Golden output.
- Accepted ARCH-016 production execution matches the committed static expected artifact.
- Controlled production mutation `percent=0.25 -> 0.20` yields final AV `50.0` and a normal Golden mismatch at record index `1`, first path `/event/payload/action_delay/after_av`, expected `55.0`, actual `50.0`.
- The new fixture remains absent from both regression manifests; standalone runtime lane remains `6/6`.
- No production/runtime contract/adapter/manifest implementation was changed.

## Files added

- `LUMEN_TASK_HSR_RUNTIME_ARCH_035.md`
- `hsr_axis_sim/data/runtime_golden_fixtures/arch_035_reviewed_action_delay_expected.json`
- `hsr_axis_sim/tests/test_runtime_arch_035_static_action_delay_golden_fixture.py`

## Files modified

- `hsr_axis_sim/LUMEN_RESULT.md`

No `sim/**`, `runtime_contracts/**`, `runtime_adapters/**`, loader/exporter/comparator/divergence/Golden implementation, regression manifest, prior reviewed static fixture, Advance/Delay production semantics, ChangeSpeed/ImmediateAction/GrantExtraTurn behavior, trace schema, or LIFO implementation was modified.

## Tests added

ARCH-035 focused coverage proves:

- exact static byte size, SHA-256, compact form, and no trailing newline;
- strict loader acceptance with the pinned expected digest;
- exact schema-v1 trace identity, three-record count, contiguous sequences `0,1,2`;
- exact event order `ACTION_START -> ACTION_VALUE_DELAYED -> ACTION_END`;
- exact action/actor/target provenance;
- exact raw `legacy_data` and typed `action_delay` values;
- absence of a clamp field;
- every record has empty `numeric_values`;
- accepted ARCH-016 production Delay output matches the static expected artifact;
- final production AV is `55.0` and final cursor is `(3,3)`;
- controlled percent `0.20` mismatch reports record `1`, path `/event/payload/action_delay/after_av`, expected `55.0`, actual `50.0`;
- controlled mismatch also preserves consistent requested-percent/requested-delta/applied-delta differences;
- AST/source guard prevents project runtime-generation helpers, JSON dumping, or file writes from constructing expected bytes in the test;
- new fixture remains absent from both regression manifests;
- all six prior reviewed static fixture identities remain unchanged;
- standalone runtime Golden regression remains `6/6`;
- legacy regression remains `20/20`;
- trace evidence remains `2/2`;
- production LIFO remains `third, second, first`.

## Exact validation commands and real results

### Initial PR CI

GitHub Actions workflow `HSR Axis Sim Validation`, PR #40, run #191, job `validate` (`97676442108`).

1. `python -m compileall -q hsr_axis_sim`
   - PASS.
2. `python -m pytest -q`
   - PASS: `1441 passed in 10.02s`.
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

The first ARCH-035 PR CI was green. No fixture-byte, digest, production-match, or divergence correction was required.

## Warnings / errors

- No compile, static-byte-integrity, strict-loader, ARCH-016 Golden match, comparator/divergence, legacy-regression, trace-evidence, or runtime-regression error was observed.
- Existing GitHub Actions Node 20 deprecation warning remains nonblocking and unrelated to ARCH-035 correctness.

## Acceptance review

- Expected bytes are static, compact, manually specified, independently reviewed, and digest-pinned.
- Expected bytes are not generated at test runtime from simulator, adapter, trace builder, exporter, stitcher, or Golden helpers.
- The fixture locks the accepted ARCH-034 production observation without changing ARCH-034 semantics.
- The reviewed scenario is a positive non-clamped Delay case; signed negative Delay behavior remains separately covered by ARCH-034 contract tests.
- Controlled mismatch proves the typed structured Delay observation is the earliest deterministic field divergence.
- Both regression manifests remain unchanged and runtime lane stays `6/6`.
- Earlier reviewed static fixtures remain byte-identical.
- No adjacent action-axis mechanic was implemented early.
- No hidden HSR values or release-game semantics were inferred; speed `100`, AV `30`, and percent `0.25` are explicit deterministic fixture inputs.
- Production LIFO compatibility remains unchanged.

## Unresolved issues

None blocking HSR-RUNTIME-ARCH-035 acceptance.

The reviewed Delay fixture is intentionally not yet part of the standalone runtime regression manifest. Promotion requires a separate explicit manifest-version milestone.

ChangeSpeed, ImmediateAction, and GrantExtraTurn still lack equivalent runtime observation contracts.

## Suggested next milestone

`HSR-RUNTIME-ARCH-036 — Delay Static Golden Regression Promotion`

ARCH-036 should promote the accepted ARCH-035 fixture into the standalone runtime action-session regression lane through one explicit strict manifest schema evolution. Add only the minimum typed setup needed for deterministic Delay construction, preserve v1.0-v1.5 grammars exactly, keep the reviewed fixture bytes unchanged, and require runtime regression to become exactly `7/7` before moving to another action-axis mechanic.

Recommended execution routing: ChatGPT **GPT-5.6 Sol**; Codex reasoning **High** if Codex is used.
