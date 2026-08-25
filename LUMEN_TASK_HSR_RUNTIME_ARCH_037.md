# HSR-RUNTIME-ARCH-037 — ChangeSpeed Runtime Observation Contract

## Current confirmed state

- HSR-RUNTIME-ARCH-036 — PASS — proceed.
- Accepted main merge commit before this task: `5f6a4fc64cef76f6e5767e3415c630f6ebe87d30`.
- Last confirmed validation:
  - `1503 passed`;
  - legacy regression `20/20`;
  - trace evidence `2/2`;
  - standalone runtime action-session Golden regression `7/7`.
- Advance and Delay production observations are accepted and separately typed.
- `ChangeSpeed` currently mutates speed and AV deterministically but emits no legacy event.

## Execution recommendation

- ChatGPT model: GPT-5.6 Sol.
- Codex reasoning: High if Codex is used.

## Objective

Add the smallest deterministic typed runtime observation for one successful production `ChangeSpeed` mutation without changing its existing formula, error condition, target resolution, or accepted production input surface.

## Existing production behavior to preserve

For each resolved target, existing finite-positive-speed behavior is:

```text
before_speed = unit.speed
before_av = unit.current_av
after_av = before_av * before_speed / new_speed
after_speed = new_speed
```

`ChangeSpeed` currently raises `ValueError("New speed must be greater than zero.")` when `new_speed <= 0` before target mutation.

Do not add new production validation for NaN, infinity, bool, or other previously unguarded values in this milestone. The typed runtime observation itself remains strict and canonical-JSON-compatible; malformed/non-finite structured observations must be rejected by the adapter rather than silently normalized.

## Required production event

After both `unit.current_av` and `unit.speed` have been assigned their new values, emit exactly one legacy event per target:

`speed_changed`

Event fields:

- `actor_id`;
- `action_id`;
- `target_id`;
- `before_speed`;
- `after_speed`;
- `before_av`;
- `after_av`.

Do not add requested/applied speed deltas, percent, clamp flags, generic axis fields, or hidden game semantics.

## Dispatch ordering

`speed_changed` must be emitted only after both mutations complete.

A normal legacy trigger listening to `speed_changed` must observe:

- target `speed == after_speed`;
- target `current_av == after_av`.

Use standard `state.emit_event`; do not add a side channel.

## Typed runtime contract

Add dedicated:

`RuntimeEventType.SPEED_CHANGED`

Do not use `CONTENT_DEFINED` and do not rename/reinterpret the accepted Advance/Delay event types.

Add frozen `RuntimeSpeedChangeObservation` with exact payload fields:

- `target_id`;
- `before_speed`;
- `after_speed`;
- `before_av`;
- `after_av`.

Validation:

- non-empty target ID;
- all numeric fields finite int/float with bool rejected;
- `before_speed > 0`;
- `after_speed > 0`;
- exact formula `after_av == before_av * before_speed / after_speed`.

Do not impose a lower bound on AV.

## Legacy adapter

Map:

`speed_changed -> RuntimeEventType.SPEED_CHANGED`

Normalize:

- `action_id`;
- `actor_id`;
- `target_id`.

Preserve raw event fields under `payload["legacy_data"]`.

Expose validated structured observation under:

`payload["speed_change"]`.

Malformed structured speed observations must raise `LegacyEventSchemaError`, not degrade to `CONTENT_DEFINED`.

## Acceptance criteria

- Existing ChangeSpeed finite-positive formula remains exact.
- Example: before speed `100`, before AV `80`, new speed `200` -> after speed `200`, after AV `40`.
- Slowing example: before speed `200`, before AV `40`, new speed `100` -> after speed `100`, after AV `80`.
- Negative AV remains formula-preserved rather than clamped.
- `new_speed <= 0` still raises the same production error before a speed observation is emitted.
- Legacy order for one non-ending action is `action_started`, `speed_changed`, `action_finished`.
- Typed capture order is `ACTION_START`, `SPEED_CHANGED`, `ACTION_END`.
- Runtime event target ID equals the changed Unit.
- Trigger dispatch sees both post-mutation speed and AV.
- No schema version bump.
- Advance and Delay contracts/formulas/events remain unchanged.
- ImmediateAction and GrantExtraTurn remain unchanged and unobserved.
- Legacy regression remains `20/20`, trace evidence `2/2`, standalone runtime regression `7/7`, LIFO unchanged.

## Required tests

1. frozen/strict `RuntimeSpeedChangeObservation` and exact payload;
2. exact formula validation including negative AV and malformed/non-finite rejection;
3. direct adapter mapping and malformed payload rejection;
4. production speed-up event and unchanged formula;
5. production slow-down formula;
6. nonpositive speed rejection produces no `speed_changed`;
7. trigger sees post-mutation speed and AV;
8. ARCH-012 exact three-record typed capture;
9. Advance/Delay preservation;
10. scope guard: no ImmediateAction/GrantExtraTurn observation added;
11. all reviewed fixture bytes unchanged;
12. legacy `20/20`, trace `2/2`, runtime `7/7`, LIFO preservation.

## Must remain unchanged

Except for minimal `ChangeSpeed` event emission:

- all other simulator formulas/effects;
- AdvanceAction and DelayAction;
- ImmediateAction;
- GrantExtraTurn;
- runtime action-session regression manifest/schema;
- reviewed Golden fixtures;
- trace schema version;
- Golden/comparator/divergence semantics;
- extra-turn LIFO behavior.

## Explicit exclusions

- static ChangeSpeed Golden fixture;
- regression promotion for ChangeSpeed;
- generic axis-effect/action-value/speed-change abstraction;
- production input cleanup/refactor;
- ImmediateAction observation;
- GrantExtraTurn observation;
- release-game hidden values;
- character DB/video automation.

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
