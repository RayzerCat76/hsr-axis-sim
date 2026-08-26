# HSR-RUNTIME-ARCH-041 — Reviewed Static ImmediateAction Golden Fixture

## Current confirmed state

- `HSR-RUNTIME-ARCH-040 — PASS — proceed` is accepted on `main`.
- Accepted `main` baseline for this task: `27dbbd988f5e46066ad7b2ba7cd2425e7ecace7c`.
- Last confirmed post-merge validation:
  - pytest: `1627 passed in 9.77s`;
  - legacy regression: `20/20`;
  - trace evidence: `2/2`;
  - standalone runtime action-session Golden regression: `8/8`.
- Accepted ImmediateAction observation contract:
  - production mutation remains `target.current_av = 0`;
  - legacy event `action_immediate`;
  - runtime event `RuntimeEventType.ACTION_VALUE_IMMEDIATE`;
  - typed payload `payload["immediate_action"]` with `target_id`, `before_av`, `after_av`;
  - typed observation requires finite non-boolean AV values and exact `after_av == 0`;
  - no priority, interrupt, extra-turn, action-family, or hidden scheduling semantics are inferred.

## Execution recommendation

- ChatGPT model: GPT-5.6 Terra.
- Codex reasoning: High if Codex is used.

## Objective

Add one independently reviewed, static, non-circular Golden expectation for a deterministic production `ImmediateAction`, then validate the real production action session through the accepted ARCH-016 end-to-end validation path.

The expected artifact must be manually specified from already accepted schema/runtime contracts. It must not be generated from the simulator, adapter, trace builder, exporter, or Golden pipeline under test.

Do not promote the new fixture into either regression manifest in this milestone.

## Reviewed deterministic scenario

Use exactly:

- fixture ID: `arch-041-reviewed-static-immediate-action`;
- trace ID: `arch-041-reviewed-static-expected`;
- stream ID: `arch-041-reviewed-axis`;
- actor/target ID: `immediate-actor`;
- Unit name: `Immediate Actor`;
- team: `ally`;
- base speed: `100`;
- initial AV: `80`;
- action ID/name: `reviewed-immediate-action`;
- effect: `ImmediateAction()`;
- `ends_turn=False`;
- final AV: `0`.

These are explicit deterministic fixture inputs only; they are not claimed to be hidden release-game values.

## Required static expected trace

Add exactly one compact canonical UTF-8 JSON artifact under:

`hsr_axis_sim/data/runtime_golden_fixtures/arch_041_reviewed_immediate_action_expected.json`

The artifact must:

- have no trailing newline;
- use schema name `hsr_runtime_trace`;
- use schema version `1.0`;
- use contiguous sequences `0,1,2`;
- have exactly three records;
- have exact event order `ACTION_START`, `ACTION_VALUE_IMMEDIATE`, `ACTION_END`;
- use exact event IDs `legacy:arch-041-reviewed-axis:0`, `:1`, `:2`;
- preserve raw `legacy_data`;
- expose typed ImmediateAction data under `immediate_action`;
- keep `numeric_values={}` in every schema-v1 record;
- have metadata:
  - `construction = "manual-reviewed"`;
  - `fixture_id = "arch-041-reviewed-static-immediate-action"`;
  - `purpose = "immediate-action-end-to-end-golden"`.

The ImmediateAction record must lock exactly:

- `target_id = "immediate-actor"`;
- `before_av = 80`;
- `after_av = 0`.

The manually reviewed artifact identity for this exact task contract is:

- byte length: **2620**;
- SHA-256: **`7fd1594362b5bf9a95eec6f6472b2f17afa9dcfe10196d81ec6c970eab86eea1`**.

## Non-circularity requirements

The expected fixture must not be created or rewritten at test runtime.

The ARCH-041 focused test source must not construct expected bytes using project runtime-generation helpers, including:

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
- runtime JSON dumping to synthesize expected bytes.

The test may only read the already committed static bytes and validate them through accepted loader/Golden boundaries.

## Production validation path

Use accepted `run_action_session_validation` with:

- one explicit production `Action` containing `ImmediateAction()`;
- one explicit Unit matching the reviewed scenario;
- stream ID `arch-041-reviewed-axis`;
- static expected bytes read from the committed fixture;
- pinned expected SHA-256;
- compact-only Golden loading.

Do not call lower simulator/adapter/export/stitch/Golden helpers to manufacture the expected side.

## Controlled divergence

Against the same static expected fixture, change only production initial AV from `80` to `60`.

Expected actual final AV remains `0`.

The accepted comparator recursively sorts mapping keys. In this payload `immediate_action` sorts before `legacy_data`, so the first divergence must be the comparator's true existing result:

- record index `1`;
- path `/event/payload/immediate_action/before_av`;
- expected `80`;
- actual `60`.

Do not modify comparator/first-divergence semantics. Separately verify the compared raw `legacy_data` also preserves the `before_av` difference.

## Acceptance criteria

- Static expected bytes are committed, compact, no trailing newline, and pinned to exactly 2620 bytes / SHA-256 `7fd1594362b5bf9a95eec6f6472b2f17afa9dcfe10196d81ec6c970eab86eea1`.
- Expected artifact is manually specified and independent of simulator/runtime generation at test runtime.
- Strict loader accepts the artifact only with the pinned digest.
- Exact schema, provenance, event order, raw `legacy_data`, and typed `immediate_action` payload match the reviewed contract.
- Production ARCH-016 ImmediateAction session matches the static expected artifact.
- Production final AV is exactly `0`.
- Controlled initial-AV `60` mismatch produces the exact accepted first divergence above and consistent raw/typed differences.
- New fixture remains absent from both regression manifests.
- Runtime action-session regression remains exactly `8/8`.
- All eight prior reviewed static fixture byte identities remain unchanged.
- No production/runtime contract/adapter implementation changes occur.
- No trace schema change occurs.
- Legacy regression remains `20/20`.
- Trace evidence remains `2/2`.
- Production LIFO remains unchanged.

## Required tests

Add focused tests proving:

1. exact static byte length, SHA-256, compact form, and no trailing newline;
2. strict loader acceptance with pinned digest;
3. exact schema, trace ID, sequences, event order, actor/action/target provenance, raw `legacy_data`, typed `immediate_action`, and empty numeric values;
4. ARCH-016 production ImmediateAction match plus final AV and cursor;
5. controlled initial-AV `60` exact first divergence and consistent raw/typed payload differences;
6. no runtime expected-generation path in the test source;
7. new fixture absent from both regression manifests;
8. all eight prior static fixture identities unchanged;
9. runtime regression remains `8/8`;
10. legacy regression `20/20`, trace evidence `2/2`, LIFO unchanged.

## Files / areas that must remain unchanged

- `hsr_axis_sim/sim/**`;
- `hsr_axis_sim/runtime_contracts/**`;
- `hsr_axis_sim/runtime_adapters/**`;
- loaders/exporters/comparators/divergence/Golden implementation;
- both regression manifests;
- runtime action-session regression harness;
- all eight prior reviewed static fixture bytes;
- production ImmediateAction and GrantExtraTurn semantics;
- Timeline semantics;
- trace schema version;
- production extra-turn LIFO behavior.

## Explicit exclusions

- runtime regression promotion for ImmediateAction;
- production ImmediateAction changes;
- GrantExtraTurn observation or fixture work;
- generic action-axis abstraction;
- priority/action-family/interrupt/extra-turn inference;
- hidden release-game values;
- video parsing or scraping;
- character database expansion;
- AI optimization;
- unrelated UI or simulator refactors.

## Commands to run

```bash
python -m compileall -q hsr_axis_sim
python -m pytest -q
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --format text
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --only trace_evidence --format text
python -m hsr_axis_sim.runtime_action_session_regression.runner --manifest hsr_axis_sim/data/runtime_action_session_regression_manifest.json --format text
```

## Final report format

Update `hsr_axis_sim/LUMEN_RESULT.md` with:

- task ID;
- implementation summary;
- files added/modified;
- tests added;
- exact commands executed;
- exact pass/fail results;
- fixture byte length and SHA-256;
- first-divergence result;
- warnings/errors;
- unresolved issues;
- confirmation exclusions were respected;
- suggested next milestone;
- milestone decision.
