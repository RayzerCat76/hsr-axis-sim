# HSR-RUNTIME-ARCH-038 — Reviewed Static ChangeSpeed Golden Fixture

## Current confirmed state

- `HSR-RUNTIME-ARCH-037 — PASS — proceed` is accepted on `main`.
- Accepted `main` baseline for this task: `01985d10d38c74c87d7afbe1861d7acb90fbffea`.
- Last confirmed validation from `hsr_axis_sim/LUMEN_RESULT.md`:
  - `1530 passed`;
  - legacy regression `20/20`;
  - trace evidence `2/2`;
  - runtime action-session Golden regression `7/7`.
- Production `ChangeSpeed` observation is accepted as:
  - legacy event `speed_changed`;
  - runtime event `RuntimeEventType.SPEED_CHANGED`;
  - typed payload `payload["speed_change"]`;
  - formula `after_av = before_av * before_speed / after_speed`;
  - no AV floor/clamp;
  - existing non-positive requested-speed production error preserved.

## Execution recommendation

- ChatGPT model: GPT-5.6 Sol.
- Codex reasoning: High if Codex is used.

## Objective

Add one independently reviewed, static, non-circular Golden expectation for a deterministic positive production `ChangeSpeed`, then validate the real production action session through the accepted ARCH-016 end-to-end validation path.

The expected artifact must be manually specified from accepted schema/runtime contracts. It must not be generated from the simulator, adapter, trace builder, exporter, or Golden pipeline under test.

Do not promote the new fixture into any regression manifest in this milestone.

## Reviewed deterministic scenario

Use exactly:

- fixture ID: `arch-038-reviewed-static-change-speed`;
- trace ID: `arch-038-reviewed-static-expected`;
- stream ID: `arch-038-reviewed-axis`;
- actor/target ID: `speed-actor`;
- Unit name: `Speed Actor`;
- team: `ally`;
- initial speed: `100`;
- initial AV: `80`;
- action ID/name: `reviewed-change-speed`;
- `ChangeSpeed(new_speed=200)`;
- `ends_turn=False`;
- final speed: `200`;
- final AV: `40.0`.

These are explicit deterministic fixture inputs only; they are not claimed to be hidden release-game values.

## Required static expected trace

Add exactly one compact canonical UTF-8 JSON artifact under:

`hsr_axis_sim/data/runtime_golden_fixtures/arch_038_reviewed_change_speed_expected.json`

The artifact must:

- have no trailing newline;
- use schema name `hsr_runtime_trace`;
- use schema version `1.0`;
- use contiguous sequences `0,1,2`;
- have exactly three records;
- have exact event order `ACTION_START`, `SPEED_CHANGED`, `ACTION_END`;
- use exact legacy event IDs `legacy:arch-038-reviewed-axis:0`, `:1`, `:2`;
- preserve raw `legacy_data`;
- expose typed ChangeSpeed data under `speed_change`;
- keep `numeric_values={}` in every schema-v1 record;
- have metadata:
  - `construction = "manual-reviewed"`;
  - `fixture_id = "arch-038-reviewed-static-change-speed"`;
  - `purpose = "change-speed-end-to-end-golden"`.

The speed-change record must lock exactly:

- `target_id = "speed-actor"`;
- `before_speed = 100`;
- `after_speed = 200`;
- `before_av = 80`;
- `after_av = 40.0`.

After manual construction, compute and pin the artifact's exact byte length and lowercase SHA-256 in tests and the final report.

## Non-circularity requirements

The expected fixture must not be created or rewritten at test runtime.

The ARCH-038 focused test source must not construct expected bytes using project runtime-generation helpers, including:

- `build_runtime_trace_document`;
- `build_runtime_trace_artifact`;
- `canonical_json_bytes`;
- `canonical_json_dumps`;
- `adapt_legacy_event`;
- `adapt_legacy_event_stream`;
- `run_multi_action_capture_session`;
- `stitch_successful_action_session`;
- `validate_successful_session_against_golden`;
- `write_bytes` / `write_text`;
- runtime JSON dumping to synthesize the expected artifact.

The test may only read the already committed static bytes and validate them through accepted loader/Golden boundaries.

## Production validation path

Use accepted `run_action_session_validation` with:

- one explicit production `Action` containing `ChangeSpeed(new_speed=200)`;
- one explicit Unit matching the reviewed scenario;
- stream ID `arch-038-reviewed-axis`;
- static expected bytes read from the committed fixture;
- pinned expected SHA-256;
- compact-only Golden loading.

Do not call lower simulator/adapter/export/stitch/Golden helpers to manufacture the expected side.

## Controlled divergence

Against the same static expected fixture, run production with `new_speed=160`.

Expected actual final state:

- speed `160`;
- AV `50.0`.

The accepted comparator recursively sorts mapping keys. Because `legacy_data` sorts before `speed_change`, the first divergence must remain the comparator's true existing result:

- record index `1`;
- path `/event/payload/legacy_data/after_av`;
- expected `40.0`;
- actual `50.0`.

Do not modify comparator/first-divergence semantics to force the typed payload to appear first. Separately verify the compared typed `speed_change` payloads preserve the consistent `after_av` and `after_speed` differences.

## Acceptance criteria

- Static expected bytes are committed, compact, no trailing newline, and digest-pinned.
- Expected artifact is manually specified and independent of simulator/runtime generation at test runtime.
- Strict loader accepts the artifact only with the pinned digest.
- Exact event order, provenance, raw legacy data, and typed `speed_change` payload match the reviewed contract.
- Production ARCH-016 ChangeSpeed session matches the static expected artifact.
- Production final speed/AV are exactly `200` / `40.0`.
- Controlled `new_speed=160` mutation produces the exact accepted first divergence above and typed speed-change differences.
- The new fixture remains absent from both regression manifests.
- Runtime action-session regression remains exactly `7/7`.
- All seven prior reviewed static fixture byte identities remain unchanged.
- No production/runtime contract/adapter implementation changes occur.
- No trace schema change occurs.
- Legacy regression remains `20/20`.
- Trace evidence remains `2/2`.
- Production LIFO remains unchanged.

## Required tests

Add focused tests proving:

1. exact static byte length, SHA-256, compact form, and no trailing newline;
2. strict loader acceptance with pinned digest;
3. exact schema, trace ID, sequences, event order, actor/action/target provenance, raw `legacy_data`, typed `speed_change`, and empty numeric values;
4. ARCH-016 production ChangeSpeed match plus final speed/AV/cursor;
5. controlled `new_speed=160` exact first divergence and typed payload differences;
6. no runtime expected-generation path in the test source;
7. new fixture absent from both regression manifests;
8. all seven prior static fixture identities unchanged;
9. runtime regression remains `7/7`;
10. legacy regression `20/20`, trace evidence `2/2`, LIFO unchanged.

## Must remain unchanged

- `hsr_axis_sim/sim/**`;
- `hsr_axis_sim/runtime_contracts/**`;
- `hsr_axis_sim/runtime_adapters/**`;
- loaders/exporters/comparators/divergence/Golden implementation;
- both regression manifests;
- all prior reviewed static fixture bytes;
- Advance/Delay/ChangeSpeed production semantics;
- ImmediateAction/GrantExtraTurn behavior;
- trace schema version;
- production LIFO behavior.

## Explicit exclusions

- runtime regression promotion;
- production ChangeSpeed changes;
- negative/non-positive-speed Golden case;
- ImmediateAction observation;
- GrantExtraTurn observation;
- generic action-axis abstraction;
- new production input validation;
- video parsing;
- scraping;
- character database expansion;
- AI optimization;
- unrelated UI or simulator refactors.

## Commands

```bash
python -m compileall -q hsr_axis_sim
python -m pytest -q
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --format text
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --only trace_evidence --format text
python -m hsr_axis_sim.runtime_action_session_regression.runner --manifest hsr_axis_sim/data/runtime_action_session_regression_manifest.json --format text
```

## Final report

Update `hsr_axis_sim/LUMEN_RESULT.md` with task ID, fixture byte length/SHA-256, manual construction review, implementation summary, files, tests, exact commands/results, warnings/errors, unresolved issues, exclusions confirmation, suggested next milestone, and the milestone decision.
