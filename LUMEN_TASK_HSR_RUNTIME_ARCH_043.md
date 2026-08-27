# HSR-RUNTIME-ARCH-043 — GrantExtraTurn Runtime Observation Contract

## Current confirmed state

Canonical accepted `main` before this task:

`23be13799facfe63152d727459f345f03e87fac6`

Last confirmed post-merge validation (GitHub Actions run #257):

- compile: PASS;
- pytest: **1687 passed in 10.16s**;
- legacy regression: **20/20**;
- trace evidence: **2/2**;
- standalone runtime action-session Golden regression: **9/9**.

Already accepted production semantics relevant to this task:

- `GrantExtraTurn.apply()` resolves targets through existing `UnitEffect.target_units()` and appends each resolved `unit.id` to `state.extra_turn_stack` in resolved/declaration order.
- `Timeline.next_turn()` gives queued extra turns precedence over the normal timeline and resolves the stack by `pop()` from the end, therefore the simulator's accepted deterministic ordering is LIFO.
- extra turns do not advance global AV and do not alter the original normal-timeline AV values merely by being selected.
- `RuntimeEventType.EXTRA_TURN_QUEUED` already exists in the stable runtime event vocabulary.
- no production legacy event currently observes `GrantExtraTurn` queue mutation.

These are simulator semantics only. They are not a claim that real HSR uses this exact hidden priority/interrupt model.

## Objective

Make the already-existing production `GrantExtraTurn` stack append observable through the runtime trace pipeline without changing queue mutation, target resolution, LIFO resolution, normal timeline behavior, or any other simulator semantics.

This task is observation-only. It must expose the concrete queue mutation that already occurs; it must not invent or infer game priority, interrupt, scheduling, or extra-action rules.

## Required implementation

### 1. Preserve exact production queue mutation

For every target resolved by `GrantExtraTurn.target_units(state, action)`, preserve the existing append exactly:

```python
state.extra_turn_stack.append(unit.id)
```

Immediately around that existing mutation, capture:

```python
stack_depth_before = len(state.extra_turn_stack)
state.extra_turn_stack.append(unit.id)
stack_depth_after = len(state.extra_turn_stack)
```

Do not reorder targets, deduplicate targets, replace the list, sort the stack, or change `Timeline.next_turn()`.

### 2. Emit one post-mutation legacy event per appended target

After each append, emit exactly one legacy event:

`extra_turn_queued`

with exact data fields:

- `actor_id`
- `action_id`
- `target_id`
- `stack_depth_before`
- `stack_depth_after`

No priority value, queue rank, interrupt marker, turn-kind inference, AV mutation, source timestamp, hidden HSR mechanic value, or extra-action metadata may be added.

The event must be emitted after the append, so event-trigger handlers observe the already-mutated stack.

For a one-target non-ending action, pending-event order must be exactly:

`action_started -> extra_turn_queued -> action_finished`

### 3. Add a strict frozen typed runtime observation

Add a dedicated runtime contract named:

`RuntimeExtraTurnQueuedObservation`

Prefer a semantically dedicated module such as:

`hsr_axis_sim/runtime_contracts/turn_order_observations.py`

rather than treating queue depth as an AV/action-axis observation.

Exact fields:

- `target_id: str`
- `stack_depth_before: int`
- `stack_depth_after: int`

Validation must require:

- `target_id` is a non-empty string;
- both depth fields are exact integers (`type(value) is int`), so booleans are rejected;
- both depths are nonnegative;
- `stack_depth_after == stack_depth_before + 1`.

`to_payload()` must return exactly those three fields and no others.

Export the new contract from `hsr_axis_sim/runtime_contracts/__init__.py`.

### 4. Bind the legacy event to the already-existing runtime vocabulary

Do not change `RuntimeEventType` enum values.

Add a deterministic registry mapping:

`extra_turn_queued -> RuntimeEventType.EXTRA_TURN_QUEUED`

Normalized fields:

- `action_id <- action_id`
- `actor_id <- actor_id`
- `target_id <- target_id`

Preserve the existing sorted mapping-registry key order.

Use a confirmed/bound semantic contract consistent with other production-observed mappings. Do not backfill the historical ARCH-002 mapping document.

### 5. Preserve raw data and expose typed payload

For a valid `extra_turn_queued` legacy event:

- preserve exact raw input in `payload["legacy_data"]`;
- expose the validated typed payload in `payload["extra_turn_queue"]`;
- keep normal adapter provenance fields unchanged.

Malformed structured queue observations must raise `LegacyEventSchemaError`; they must not degrade to `CONTENT_DEFINED` or silently drop invalid fields.

### 6. Prove post-mutation trigger visibility

Add a focused trigger test showing that when an `extra_turn_queued` trigger fires, it sees the target already appended and the stack depth equal to `stack_depth_after`.

Do not change trigger dispatch semantics.

### 7. Prove self-target behavior

Add a dedicated self-target test:

- actor and target IDs may be identical;
- exactly one target ID is appended;
- event provenance keeps `actor_id == target_id` when self-targeted;
- depth transitions are exact.

### 8. Prove multi-target append order and LIFO resolution

Add a dedicated multi-target test using explicit target order, for example `["first", "second"]`:

- queue events are emitted in resolved/declaration order: first, then second;
- depth transitions are `0 -> 1`, then `1 -> 2`;
- stack after the action is `["first", "second"]`;
- subsequent `Timeline.next_turn()` calls resolve `second`, then `first`;
- global AV / normal timeline behavior remains unchanged by the extra-turn selection itself.

This is a test of accepted simulator LIFO behavior only, not a claim about undocumented HSR priority semantics.

### 9. Runtime capture proof

Use the existing ARCH-012 capture pipeline to prove one target produces exactly three typed records:

1. `ACTION_START`
2. `EXTRA_TURN_QUEUED`
3. `ACTION_END`

The queued record must preserve:

- action ID;
- actor ID;
- target ID;
- `payload["legacy_data"]`;
- exact `payload["extra_turn_queue"]`;
- existing adapter provenance;
- no unrelated numeric-values payload.

### 10. Preserve all accepted regressions and reviewed fixtures

All existing reviewed Golden fixture byte identities must remain unchanged.

Required regression results after this task:

- legacy regression: **20/20**;
- trace evidence: **2/2**;
- standalone runtime action-session Golden regression: **9/9**;
- production LIFO compatibility remains explicit and passing.

ARCH-043 must not add a static GrantExtraTurn Golden and must not promote a new regression case.

## Required tests

Add a focused file:

`hsr_axis_sim/tests/test_runtime_arch_043_extra_turn_observation.py`

It must cover at minimum:

1. frozen `RuntimeExtraTurnQueuedObservation` exact payload;
2. rejection of empty/non-string target IDs;
3. rejection of bool/float/string/negative queue-depth fields;
4. rejection unless `after == before + 1`;
5. adapter mapping to `EXTRA_TURN_QUEUED`;
6. exact normalized IDs;
7. exact raw `legacy_data` preservation;
8. exact typed `extra_turn_queue` payload;
9. malformed event rejection as `LegacyEventSchemaError`;
10. one-target production event data and event ordering;
11. trigger sees post-append stack;
12. self-target provenance and depth;
13. multi-target declared append/event order;
14. subsequent LIFO resolution in reverse append order;
15. runtime capture `ACTION_START -> EXTRA_TURN_QUEUED -> ACTION_END`;
16. `GrantExtraTurn` remains distinct from ImmediateAction/Advance/Delay/ChangeSpeed observations;
17. all accepted reviewed fixture identities remain exact;
18. legacy 20/20;
19. trace evidence 2/2;
20. runtime action-session 9/9;
21. existing production extra-turn LIFO behavior remains unchanged.

Update stale historical source guards only where this newly authorized observation makes an old global-current assumption false. Historical milestones must continue protecting their original mechanic boundaries; do not weaken unrelated assertions.

## Files / areas that must remain unchanged

Unless a narrow historical test boundary must be updated because of this authorized observation, do not change:

- `hsr_axis_sim/sim/timeline.py`;
- `hsr_axis_sim/sim/action.py`;
- `hsr_axis_sim/sim/unit.py`;
- `hsr_axis_sim/sim/state.py` except no change is expected;
- `hsr_axis_sim/runtime_contracts/enums.py`;
- runtime resource/action-axis observation semantics;
- runtime action-session regression manifest grammar/runner;
- `hsr_axis_sim/data/runtime_action_session_regression_manifest.json`;
- `hsr_axis_sim/data/regression_manifest.json`;
- every file under `hsr_axis_sim/data/runtime_golden_fixtures/`;
- Golden validator/comparator/first-divergence code;
- trace schema/version;
- ownership/SP/energy semantics;
- any other effect implementation.

The only production simulator change should be observation emission around the existing append inside `GrantExtraTurn.apply()`.

## Explicit exclusions

Do not implement or infer:

- real HSR extra-turn priority values;
- interrupt windows;
- ultimate priority;
- extra-action/follow-up semantics;
- FIFO/FILO alternatives;
- a generalized scheduler or priority queue;
- changes to accepted LIFO ordering;
- changes to Timeline selection/reset behavior;
- queue deduplication or replacement;
- automatic action selection;
- a static GrantExtraTurn Golden fixture;
- runtime regression promotion or manifest v1.9;
- generic effect DSL support;
- trace schema bump;
- video parsing/scraping;
- character database expansion;
- damage formulas;
- AI optimization;
- unrelated UI/refactor work.

## Commands to run

```bash
python -m compileall -q hsr_axis_sim
python -m pytest -q
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --format text
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --only trace_evidence --format text
python -m hsr_axis_sim.runtime_action_session_regression.runner --manifest hsr_axis_sim/data/runtime_action_session_regression_manifest.json --format text
```

Report real results only.

## Acceptance criteria

ARCH-043 is accepted only if all of the following are true:

- existing `GrantExtraTurn` append semantics are unchanged;
- exactly one post-append `extra_turn_queued` event is emitted per resolved target;
- event fields are exactly the five specified legacy fields;
- strict frozen typed queue observation exists and rejects malformed depth transitions;
- existing `EXTRA_TURN_QUEUED` enum is used without enum changes;
- adapter preserves both raw and typed payloads;
- malformed structured queue events raise `LegacyEventSchemaError`;
- trigger sees post-mutation stack;
- self-target behavior is explicitly tested;
- multi-target append order is explicitly tested;
- subsequent resolution remains deterministic LIFO;
- one-target runtime capture is exactly three records in required order;
- no static Golden/regression promotion occurs;
- no Timeline or queue-selection semantics change occurs;
- all reviewed fixture bytes remain unchanged;
- full pytest passes;
- legacy 20/20 passes;
- trace evidence 2/2 passes;
- runtime action-session 9/9 passes;
- exclusions are respected;
- `LUMEN_RESULT.md` is updated with exact commands/results, warnings, unresolved issues, exclusions, and next milestone suggestion.

## Final report format

Update `hsr_axis_sim/LUMEN_RESULT.md` and include:

1. task ID;
2. decision/status;
3. starting accepted main SHA;
4. implementation summary;
5. exact observation semantics and explicit non-claims about real HSR priority;
6. files added/modified;
7. tests added/updated;
8. exact commands executed;
9. exact real pass/fail counts and timings;
10. any intermediate CI failures and evidence-backed fixes;
11. warnings/errors;
12. unresolved issues;
13. confirmation that exclusions and locked areas were respected;
14. suggested next milestone only after acceptance.

## Execution routing

- ChatGPT model: **GPT-5.6 Sol**
- Codex reasoning: **High**

Reason: the implementation is narrow, but it observes the core deterministic extra-turn queue whose LIFO semantics must not be accidentally changed.
