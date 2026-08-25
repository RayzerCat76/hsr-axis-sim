# HSR-RUNTIME-ARCH-035 — Reviewed Static Delay Action Golden Fixture

## Current confirmed state

- HSR-RUNTIME-ARCH-034 — PASS — proceed.
- Accepted main merge commit before this task: `b2f01a3ffe0db7d2ffcbc69cdd4a8b5984be6a54`.
- Last confirmed validation:
  - `1433 passed`;
  - legacy regression `20/20`;
  - trace evidence `2/2`;
  - standalone runtime action-session Golden regression `6/6`.
- Production Delay observation is now accepted as:
  - legacy event `action_delayed`;
  - runtime event `ACTION_VALUE_DELAYED`;
  - typed payload `payload["action_delay"]`;
  - no clamp field;
  - signed equation `after_av = before_av + base_av * percent`.

## Execution recommendation

- ChatGPT model: GPT-5.6 Sol.
- Codex reasoning: High if Codex is used.

## Objective

Add one independently reviewed, static, non-circular Golden expectation for a deterministic positive production `DelayAction`, then validate the real production action session through the already accepted ARCH-016 end-to-end validation path.

The expected artifact must be manually specified from the accepted schema/runtime contracts. It must not be generated from the simulator, adapter, trace builder, exporter, or Golden pipeline under test.

Do not promote the new fixture into any regression manifest in this milestone.

## Reviewed deterministic scenario

Use exactly:

- fixture ID: `arch-035-reviewed-static-action-delay`;
- trace ID: `arch-035-reviewed-static-expected`;
- stream ID: `arch-035-reviewed-axis`;
- actor/target ID: `delay-actor`;
- Unit name: `Delay Actor`;
- team: `ally`;
- base speed: `100`;
- initial AV: `30`;
- action ID/name: `reviewed-action-delay`;
- `DelayAction(percent=0.25)`;
- `ends_turn=False`;
- final AV: `55.0`.

These are explicit deterministic fixture inputs only; they are not claimed to be hidden release-game values.

## Required static expected trace

Add exactly one compact canonical UTF-8 JSON artifact under:

`hsr_axis_sim/data/runtime_golden_fixtures/arch_035_reviewed_action_delay_expected.json`

The artifact must:

- have no trailing newline;
- use schema name `hsr_runtime_trace`;
- use schema version `1.0`;
- use contiguous sequences `0,1,2`;
- have exactly three records;
- have exact event order:
  - `ACTION_START`;
  - `ACTION_VALUE_DELAYED`;
  - `ACTION_END`;
- use exact legacy event IDs:
  - `legacy:arch-035-reviewed-axis:0`;
  - `legacy:arch-035-reviewed-axis:1`;
  - `legacy:arch-035-reviewed-axis:2`;
- preserve raw `legacy_data`;
- expose typed Delay data under `action_delay`;
- keep `numeric_values={}` in every schema-v1 record;
- have metadata:
  - `construction = "manual-reviewed"`;
  - `fixture_id = "arch-035-reviewed-static-action-delay"`;
  - `purpose = "action-delay-end-to-end-golden"`.

The Delay record must lock exactly:

- `target_id = "delay-actor"`;
- `before_av = 30`;
- `after_av = 55.0`;
- `base_av = 100.0`;
- `requested_percent = 0.25`;
- `requested_delta_av = 25.0`;
- `applied_delta_av = 25.0`.

There must be no `clamped_to_zero` field in either the typed `action_delay` structure or raw Delay legacy data.

After manual construction, compute and pin the artifact's exact byte length and lowercase SHA-256 in tests and the final report.

## Non-circularity requirements

The expected fixture must not be created or rewritten at test runtime.

The ARCH-035 focused test source must not construct expected bytes using project runtime-generation helpers, including:

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

Use the accepted ARCH-016 `run_action_session_validation` entry point with:

- one explicit production `Action` containing `DelayAction(percent=0.25)`;
- one explicit Unit matching the reviewed scenario;
- stream ID `arch-035-reviewed-axis`;
- static expected bytes read from the committed fixture;
- pinned expected SHA-256;
- compact-only Golden loading.

Do not call lower simulator/adapter/export/stitch/Golden helpers to manufacture the expected side.

## Controlled divergence

Against the same static expected fixture, run production with `percent=0.20`.

Expected actual final AV: `50.0`.

The Golden comparison must complete normally with `matches=False` and report the first divergence at:

- record index `1`;
- path `/event/payload/action_delay/after_av`;
- expected `55.0`;
- actual `50.0`.

Also verify the compared typed Delay payloads preserve consistent differences in requested percent, requested delta, and applied delta.

## Acceptance criteria

- Static expected bytes are committed, compact, no trailing newline, and digest-pinned.
- Expected artifact is manually specified and independent of simulator/runtime generation at test runtime.
- Strict loader accepts the artifact only with the pinned digest.
- Exact event order and Delay payload fields match the reviewed contract.
- Production ARCH-016 positive Delay session matches the static expected artifact.
- Production final AV is `55.0`.
- Controlled `percent=0.20` mutation produces the exact first typed divergence described above.
- The new fixture remains absent from both:
  - `hsr_axis_sim/data/regression_manifest.json`;
  - `hsr_axis_sim/data/runtime_action_session_regression_manifest.json`.
- Runtime action-session regression therefore remains exactly `6/6`.
- All earlier reviewed static fixture byte identities remain unchanged.
- No production/runtime contract/adapter implementation changes occur.
- No trace schema change occurs.
- Legacy regression remains `20/20`.
- Trace evidence remains `2/2`.
- Production LIFO remains unchanged.

## Required tests

Add focused tests proving:

1. exact static byte length, SHA-256, compact form, and no trailing newline;
2. strict loader acceptance with pinned digest;
3. exact schema, trace ID, sequences, event order, actor/action/target provenance, raw `legacy_data`, typed `action_delay`, and empty numeric values;
4. ARCH-016 production Delay match and final AV/cursor;
5. controlled percent mutation exact first divergence;
6. no runtime expected-generation path in the test source;
7. new fixture absent from both regression manifests;
8. all six prior static fixture identities unchanged;
9. runtime regression remains `6/6`;
10. legacy regression `20/20`, trace evidence `2/2`, LIFO unchanged.

## Must remain unchanged

- `hsr_axis_sim/sim/**`;
- `hsr_axis_sim/runtime_contracts/**`;
- `hsr_axis_sim/runtime_adapters/**`;
- loaders/exporters/comparators/divergence/Golden implementation;
- both regression manifests;
- all prior reviewed static fixture bytes;
- Advance/Delay production semantics;
- ChangeSpeed/ImmediateAction/GrantExtraTurn behavior;
- trace schema version;
- LIFO behavior.

## Explicit exclusions

- runtime regression promotion or schema v1.6;
- production Delay changes;
- negative/clamped Delay Golden case;
- ChangeSpeed observation;
- ImmediateAction observation;
- GrantExtraTurn observation;
- generic action-axis abstraction;
- video parsing/scraping/AI optimization/damage expansion.

## Commands

```bash
python -m compileall -q hsr_axis_sim
python -m pytest -q
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --format text
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --only trace_evidence --format text
python -m hsr_axis_sim.runtime_action_session_regression.runner --manifest hsr_axis_sim/data/runtime_action_session_regression_manifest.json --format text
```

## Final report

Update `hsr_axis_sim/LUMEN_RESULT.md` with task ID, fixture byte length/SHA-256, manual construction review, implementation summary, files, tests, exact commands/results, warnings/errors, unresolved issues, exclusions confirmation, and suggested next milestone.
