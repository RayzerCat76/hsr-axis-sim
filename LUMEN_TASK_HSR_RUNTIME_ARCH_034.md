# HSR-RUNTIME-ARCH-034 — Delay Action Runtime Observation Contract

## Current confirmed state

- HSR-RUNTIME-ARCH-033 — PASS — proceed.
- Accepted main merge commit before this task: `5915d1772215891fcbcf3789497b5e3a1faf90f9`.
- Last confirmed validation:
  - `1409 passed`;
  - legacy regression `20/20`;
  - trace evidence `2/2`;
  - standalone runtime action-session Golden regression `6/6`.
- Advance observation and its reviewed static Golden regression case are locked.
- `DelayAction` currently mutates `Unit.current_av` deterministically but emits no event.

## Execution recommendation

- ChatGPT model: GPT-5.6 Sol.
- Codex reasoning: High if Codex is used.

## Objective

Add the smallest deterministic, typed runtime observation for one production `DelayAction` mutation without changing the existing AV formula or narrowing its accepted input surface.

Lock enough information in the trace to verify:

- target Unit provenance;
- AV before and after;
- base AV used by the production formula;
- requested delay percent;
- requested signed AV delta;
- actually applied signed AV delta.

Keep ChangeSpeed, ImmediateAction, GrantExtraTurn, static Delay Golden fixtures, and regression promotion out of this milestone.

## Required production event

After each target Unit's existing delay mutation succeeds, emit one legacy event:

`action_delayed`

The event must contain exactly:

- `actor_id`;
- `action_id`;
- `target_id`;
- `before_av`;
- `after_av`;
- `base_av`;
- `requested_percent`;
- `requested_delta_av`;
- `applied_delta_av`.

Signed delta convention:

- normal positive delay increases AV, so `requested_delta_av` and `applied_delta_av` are positive;
- do not add a positivity restriction to `DelayAction.percent`;
- do not add a zero-floor or clamp to DelayAction;
- negative percentages and any resulting finite AV remain representable because current `Unit.current_av` and `DelayAction` do not impose an AV floor.

The production mutation must remain behaviorally identical to:

`after_av = before_av + base_av * percent`.

Derived fields must describe that exact mutation; they must not replace it with a different mechanic.

## Dispatch ordering

`action_delayed` must be emitted only after `Unit.current_av` has been assigned its new value.

Because `state.emit_event` participates in standard legacy trigger dispatch:

- the event is appended to `pending_events` before matching triggers run;
- a trigger listening to `action_delayed` may observe/react to the already-updated AV;
- this dispatch participation is intentional and must be tested/documented;
- do not bypass `state.emit_event` with a side channel.

## Typed runtime contract

Add a dedicated `RuntimeEventType.ACTION_VALUE_DELAYED`.

Do not reuse `ACTION_VALUE_ADVANCED`, do not use `CONTENT_DEFINED`, and do not introduce a generic action-value-change abstraction in this milestone.

Add a frozen `RuntimeActionDelayObservation` with exact schema-v1-compatible payload fields:

- `target_id`;
- `before_av`;
- `after_av`;
- `base_av`;
- `requested_percent`;
- `requested_delta_av`;
- `applied_delta_av`.

Validation must require:

- non-empty target ID;
- finite non-boolean numeric fields;
- positive `base_av`;
- exact requested delta equal to `base_av * requested_percent`;
- exact after AV equal to `before_av + requested_delta_av`;
- exact applied delta equal to `after_av - before_av`.

Do not require `before_av >= 0`, `after_av >= 0`, or `requested_percent >= 0`; those would be new semantics not enforced by current production.

## Legacy adapter

Map:

`action_delayed -> RuntimeEventType.ACTION_VALUE_DELAYED`

Normalize:

- `action_id`;
- `actor_id`;
- `target_id`.

Preserve the raw legacy event in `payload["legacy_data"]`.

Validate and expose the typed observation under:

`payload["action_delay"]`.

Malformed structured Delay observations must raise `LegacyEventSchemaError`, not silently degrade to `CONTENT_DEFINED`.

## Acceptance criteria

- Existing DelayAction AV results remain exactly unchanged.
- Example: speed 100, before AV 30, percent 0.25 -> after AV 55.
- Signed reverse example remains representable: speed 100, before AV 30, percent -0.5 -> after AV -20.
- Legacy event order for one non-ending action is `action_started`, `action_delayed`, `action_finished`.
- Typed capture order is `ACTION_START`, `ACTION_VALUE_DELAYED`, `ACTION_END`.
- Runtime event target ID equals the delayed Unit.
- Structured payload exactly represents requested/applied AV deltas without any clamp field.
- A listener for `action_delayed` observes the post-mutation AV and participates in normal trigger dispatch.
- No trace schema version bump; existing schema-v1 traces remain valid.
- AdvanceAction behavior/event/payload remains unchanged.
- No ChangeSpeed/ImmediateAction/GrantExtraTurn production changes.
- Existing reviewed static fixtures remain byte-identical.
- Existing standalone runtime Golden regression remains exactly `6/6`.
- Legacy regression remains `20/20` and trace evidence `2/2`.
- Production LIFO remains unchanged.

## Required tests

Add focused tests for:

1. `RuntimeActionDelayObservation` frozen/strict validation and exact payload;
2. signed finite Delay observations, including a negative-percent case that yields negative AV;
3. direct adapter mapping and malformed payload rejection;
4. production positive Delay event and unchanged formula;
5. standard trigger dispatch after AV mutation;
6. ARCH-012 capture produces exact typed three-record Delay trace;
7. Advance observation remains unchanged;
8. reviewed static fixture digest(s), runtime `6/6`, legacy `20/20`, trace `2/2`, and LIFO preservation;
9. scope guard proving ChangeSpeed/ImmediateAction/GrantExtraTurn do not gain observation emission.

## Must remain unchanged

Except for the minimal `DelayAction` event emission:

- all simulator effect formulas;
- `AdvanceAction`;
- `ChangeSpeed`;
- `ImmediateAction`;
- `GrantExtraTurn`;
- action ordering and LIFO behavior;
- both regression manifests;
- reviewed static fixture bytes;
- trace schema version;
- Golden comparator/divergence semantics;
- standalone runtime regression grammar/version (`1.5`).

## Explicit exclusions

- static Golden fixture for Delay;
- runtime regression manifest promotion or schema v1.6;
- ChangeSpeed observation;
- ImmediateAction observation;
- GrantExtraTurn observation;
- generic action-axis observation/event abstraction;
- changing DelayAction formula, percent semantics, or AV clamping;
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
