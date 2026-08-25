# HSR-RUNTIME-ARCH-031 — Advance Action Runtime Observation Contract

## Current confirmed state

- HSR-RUNTIME-ARCH-030 — PASS — proceed.
- Accepted main merge commit before this task: `372ad8161ba74331cae44fc5054d30dc62a710e0`.
- Last confirmed validation:
  - `1315 passed`;
  - legacy regression `20/20`;
  - trace evidence `2/2`;
  - standalone runtime action-session Golden regression `5/5`.
- Resource gain/consume observation and failure paths are locked.
- `AdvanceAction` currently mutates `Unit.current_av` deterministically but emits no event.

## Execution recommendation

- ChatGPT model: GPT-5.6 Sol.
- Codex reasoning: High if Codex is used.

## Objective

Add the smallest deterministic, typed runtime observation for one production `AdvanceAction` mutation without changing the existing AV formula.

Lock enough information in the trace to verify:

- target Unit provenance;
- AV before and after;
- base AV used by the production formula;
- requested advance percent;
- requested signed AV delta;
- actually applied signed AV delta;
- whether the zero floor clamped the requested result.

Keep Delay, speed change, immediate action, and extra-turn observation out of this milestone.

## Required production event

After each target Unit's existing advance mutation succeeds, emit one legacy event:

`action_advanced`

The event must contain exactly the deterministic observation fields needed by the runtime adapter:

- `actor_id`;
- `action_id`;
- `target_id`;
- `before_av`;
- `after_av`;
- `base_av`;
- `requested_percent`;
- `requested_delta_av`;
- `applied_delta_av`;
- `clamped_to_zero`.

Signed delta convention:

- advance decreases AV, so a normal advance has negative `requested_delta_av` and negative `applied_delta_av`;
- do not add a new positivity restriction to `AdvanceAction.percent`; preserve existing production input semantics exactly.

The underlying production formula must remain behaviorally:

`after_av = max(0, before_av - base_av * percent)`.

Derived fields must describe that exact formula; they must not replace it with a different mechanic.

## Dispatch ordering

`action_advanced` must be emitted only after `Unit.current_av` has been assigned its new value.

Because `state.emit_event` participates in standard legacy trigger dispatch:

- the event is appended to `pending_events` before matching triggers run;
- a trigger listening to `action_advanced` may observe/react to the already-updated AV;
- this dispatch participation is intentional and must be tested/documented;
- do not bypass `state.emit_event` with a side channel.

## Typed runtime contract

Add a dedicated `RuntimeEventType.ACTION_VALUE_ADVANCED`.

Do not use `CONTENT_DEFINED` and do not introduce a broad generic action-value-change type yet.

Add a frozen `RuntimeActionAdvanceObservation` with exact schema-v1-compatible payload fields:

- `target_id`;
- `before_av`;
- `after_av`;
- `base_av`;
- `requested_percent`;
- `requested_delta_av`;
- `applied_delta_av`;
- `clamped_to_zero`.

Validation must require:

- non-empty target ID;
- finite non-boolean numeric fields;
- positive `base_av`;
- exact signed requested delta equal to `-(base_av * requested_percent)`;
- exact applied delta equal to `after_av - before_av`;
- exact after AV equal to `max(0, before_av + requested_delta_av)`;
- exact boolean clamp flag equal to whether the unclamped result is below zero.

Do not reject negative/zero `requested_percent` solely in the observation layer; that would change the accepted input surface.

## Legacy adapter

Map:

`action_advanced -> RuntimeEventType.ACTION_VALUE_ADVANCED`

Normalize:

- `action_id`;
- `actor_id`;
- `target_id`.

Preserve the raw legacy event in `payload["legacy_data"]`.

Validate and expose the typed observation under:

`payload["action_advance"]`.

Malformed structured advance observations must raise `LegacyEventSchemaError`, not silently degrade to `CONTENT_DEFINED`.

## Acceptance criteria

- Existing AdvanceAction AV results remain exactly unchanged.
- Non-clamped example: speed 100, before AV 80, percent 0.5 -> after AV 30.
- Clamped example: speed 100, before AV 40, percent 1.0 -> after AV 0.
- Legacy event order for one non-ending action is `action_started`, `action_advanced`, `action_finished`.
- Typed capture order is `ACTION_START`, `ACTION_VALUE_ADVANCED`, `ACTION_END`.
- Runtime event target ID equals the advanced Unit.
- Structured payload exactly represents requested/applied AV deltas and clamp state.
- A listener for `action_advanced` observes the post-mutation AV and participates in normal trigger dispatch.
- No schema version bump; existing schema-v1 traces remain valid.
- No Delay/ChangeSpeed/ImmediateAction/GrantExtraTurn production changes.
- Existing successful runtime regression remains `5/5`.
- Legacy regression remains `20/20` and trace evidence `2/2`.
- Production LIFO remains unchanged.

## Required tests

Add focused tests for:

1. `RuntimeActionAdvanceObservation` strict/frozen validation and canonical payload;
2. direct adapter mapping and malformed payload rejection;
3. production non-clamped self-advance event and unchanged formula;
4. production clamped-to-zero event;
5. standard trigger dispatch occurs after AV mutation;
6. ARCH-012 capture produces exact typed three-record action trace;
7. existing regression/LIFO preservation;
8. scope guard proving Delay/ChangeSpeed/ImmediateAction/GrantExtraTurn implementations are unchanged.

## Must remain unchanged

Except for the minimal `AdvanceAction` event emission:

- all other simulator effect formulas;
- `DelayAction`;
- `ChangeSpeed`;
- `ImmediateAction`;
- `GrantExtraTurn`;
- action ordering and LIFO behavior;
- regression manifests and reviewed static fixtures;
- trace schema version;
- Golden comparator/divergence semantics.

## Explicit exclusions

- static Golden fixture for advance (separate later milestone);
- regression manifest promotion;
- Delay observation;
- speed observation;
- immediate-action observation;
- extra-turn observation;
- changing the advance formula or percent semantics;
- damage/content database/video automation.

## Commands

```bash
python -m compileall -q hsr_axis_sim
python -m pytest -q
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --format text
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --only trace_evidence --format text
python -m hsr_axis_sim.runtime_action_session_regression.runner --manifest hsr_axis_sim/data/runtime_action_session_regression_manifest.json --format text
```

## Final report

Update `hsr_axis_sim/LUMEN_RESULT.md` with task ID, implementation summary, files, tests, exact commands/results, warnings/errors, unresolved issues, exclusions confirmation, and suggested next milestone.
