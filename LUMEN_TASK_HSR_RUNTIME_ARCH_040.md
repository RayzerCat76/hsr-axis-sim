# HSR-RUNTIME-ARCH-040 — ImmediateAction Runtime Observation Contract

## Current confirmed state

- HSR-RUNTIME-ARCH-039 — PASS — proceed.
- Accepted `main` before this task: `cde75d15e71a75d7158a5229d07da47dbeab6753`.
- Last confirmed post-merge validation, GitHub Actions run #232:
  - `1601 passed in 9.84s`;
  - legacy regression `20/20`;
  - trace evidence `2/2`;
  - standalone runtime action-session Golden regression `8/8`.
- Advance, Delay, and ChangeSpeed production observations are accepted and separately typed.
- Existing production `ImmediateAction` resolves its targets and sets each target Unit's `current_av = 0`; it currently emits no event and does not touch the extra-turn stack.
- `GrantExtraTurn` remains separate and unobserved.

## Execution recommendation

- ChatGPT model: GPT-5.6 Sol.
- Codex reasoning: High if Codex is used.

## Objective

Add the smallest deterministic runtime observation for one successful production `ImmediateAction` AV mutation without changing target resolution, action execution order, turn selection, extra-turn behavior, or any hidden HSR semantics.

## Existing production behavior to preserve

For each resolved target, accepted implementation behavior is exactly:

```text
before_av = unit.current_av
unit.current_av = 0
after_av = unit.current_av
```

This task does **not** claim that `ImmediateAction` is an extra turn, interrupt, priority class, action advance percentage, or a release-game universal rule. It only exposes the existing deterministic AV-to-zero mutation.

Do not add new production input validation or alter target resolution.

## Required production event

After `unit.current_av` has been assigned `0`, emit exactly one legacy event per resolved target:

`action_immediate`

Exact event fields:

- `actor_id`;
- `action_id`;
- `target_id`;
- `before_av`;
- `after_av`.

Do not add `base_av`, percentages, requested/applied deltas, clamp flags, priority, turn kind, queue position, extra-turn metadata, or inferred HSR semantics.

## Dispatch ordering

`action_immediate` must be emitted only after the target AV mutation completes.

A normal legacy trigger listening to `action_immediate` must observe the target's `current_av == 0`.

Use accepted `state.emit_event`; do not add a side channel.

For one non-ending action with one target, legacy pending-event order must be:

`action_started -> action_immediate -> action_finished`.

## Typed runtime contract

Add dedicated runtime vocabulary:

`RuntimeEventType.ACTION_VALUE_IMMEDIATE`

Do not reuse `ACTION_VALUE_ADVANCED`, because `ImmediateAction` has no accepted percentage/base-AV request contract and must remain distinguishable from `AdvanceAction`.

Add frozen `RuntimeImmediateActionObservation` with exact payload fields:

- `target_id`;
- `before_av`;
- `after_av`.

Validation:

- `target_id` is a non-empty string;
- `before_av` and `after_av` are finite int/float values with bool rejected;
- `after_av == 0` exactly;
- do not impose a lower bound on `before_av`.

Expose this typed object through `hsr_axis_sim.runtime_contracts`.

## Legacy adapter

Map:

`action_immediate -> RuntimeEventType.ACTION_VALUE_IMMEDIATE`

Normalize:

- `action_id`;
- `actor_id`;
- `target_id`.

Preserve all raw event fields under:

`payload["legacy_data"]`.

Expose the validated structured observation under:

`payload["immediate_action"]`.

Malformed structured ImmediateAction observations must raise `LegacyEventSchemaError`, not degrade to `CONTENT_DEFINED`.

## Acceptance criteria

- Existing `ImmediateAction` target resolution and AV mutation remain exact.
- Example: target AV `80` -> `0`.
- Negative starting AV remains accepted by this observation contract and becomes `0`; no new production floor/range rule is inferred.
- Starting AV `0` still deterministically remains `0` and may still produce the explicit observation; do not silently skip the event as a no-op optimization.
- Event emission occurs after the AV mutation.
- One resolved target produces one `action_immediate` event.
- Legacy order for one non-ending action is `action_started`, `action_immediate`, `action_finished`.
- Typed capture order is `ACTION_START`, `ACTION_VALUE_IMMEDIATE`, `ACTION_END`.
- Runtime event `target_id` equals the affected Unit.
- `payload["immediate_action"]` is exact and separately typed from `action_advance`.
- A self-target ImmediateAction has dedicated coverage and preserves actor/target identity correctly.
- Multi-target resolution, if exercised, emits observations in the existing resolved-target iteration order without sorting or reinterpretation.
- No trace schema version bump.
- Advance, Delay, and ChangeSpeed formulas/events/contracts remain unchanged.
- `GrantExtraTurn` remains unchanged and unobserved.
- Runtime regression manifest remains v1.7 with the accepted eight cases and all Golden fixture bytes unchanged.
- Legacy regression remains `20/20`, trace evidence `2/2`, standalone runtime regression `8/8`, and production extra-turn LIFO remains unchanged.

## Required tests

1. frozen/strict `RuntimeImmediateActionObservation` and exact payload;
2. finite-number validation, bool/non-finite rejection, exact `after_av == 0`, and negative/zero `before_av` support;
3. direct adapter mapping and malformed payload rejection;
4. production positive-AV target mutation and exact event data/order;
5. production zero-AV no-op mutation still emits one explicit observation;
6. production negative-AV input still becomes zero without adding a new range rule;
7. trigger listening to `action_immediate` observes post-mutation AV zero;
8. ARCH-012 exact three-record typed capture;
9. self-target edge-case actor/target provenance;
10. optional multi-target deterministic observation order if needed to lock existing iteration semantics;
11. Advance/Delay/ChangeSpeed preservation;
12. scope guard proving `GrantExtraTurn` remains unobserved and unchanged;
13. all eight reviewed static fixture byte identities unchanged;
14. legacy `20/20`, trace `2/2`, runtime `8/8`, LIFO preservation.

## Must remain unchanged

Except for the minimal `ImmediateAction` event emission:

- all other simulator formulas/effects;
- target resolution implementation;
- `AdvanceAction`;
- `DelayAction`;
- `ChangeSpeed`;
- `GrantExtraTurn`;
- runtime action-session regression grammar/manifest/runner;
- reviewed Golden fixture bytes;
- trace schema version;
- Golden/comparator/divergence semantics;
- extra-turn stack semantics and LIFO behavior;
- action selection/turn-priority semantics.

## Explicit exclusions

- static ImmediateAction Golden fixture;
- regression promotion for ImmediateAction;
- `GrantExtraTurn` observation or refactor;
- generic action-axis/effect abstraction;
- reinterpretation as an extra turn, interrupt, action family, or priority class;
- changes to `Timeline.next_turn` or `Timeline.end_turn`;
- tie-breaking changes for multiple zero-AV units;
- production input cleanup/refactor;
- release-game hidden values;
- character database work;
- video parsing/scraping;
- AI optimization or UI work.

## Commands

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
- warnings/errors;
- unresolved issues;
- confirmation that exclusions were respected;
- suggested next milestone.
