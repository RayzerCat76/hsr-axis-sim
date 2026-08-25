# HSR-RUNTIME-ARCH-029 — Insufficient Skill-Point Action Failure Contract

## Current confirmed state

- HSR-RUNTIME-ARCH-028 — PASS — proceed.
- Accepted main merge commit before this task: `3de670684a1c7e833fb8818cbfd956d0f655d019`.
- Last confirmed validation:
  - `1303 passed`;
  - legacy regression `20/20`;
  - trace evidence `2/2`;
  - standalone runtime action-session Golden regression `5/5`.
- Successful `ConsumeSkillPoint` is already locked by ARCH-027 and promoted by ARCH-028.
- ARCH-012 single-action capture and ARCH-013 multi-action sessions are explicitly non-transactional.

## Execution recommendation

- ChatGPT model: GPT-5.6 Sol.
- Codex reasoning: High if Codex is used.

## Objective

Lock the existing production failure semantics when `ConsumeSkillPoint` requires more team Skill Points than are available. Document and test the exact partial action state left by the exception through direct production execution, ARCH-012 single-action capture orchestration, and ARCH-013 multi-action session orchestration.

This is a failure-contract milestone, not a Golden replay milestone.

## Confirmed production behavior to validate

For an action using `ConsumeSkillPoint(amount=2)` with team SP `1`:

1. `Action.execute` creates or validates the turn context.
2. It sets `turn_context.should_end_turn` from `action.ends_turn`.
3. It emits `action_started`.
4. `ConsumeSkillPoint` sees insufficient SP and raises:
   `ValueError("Insufficient skill points: 1 available, 2 required.")`.
5. The Skill-Point state is not mutated.
6. No `skill_points_changed` event is emitted.
7. `turn_context.actions_taken` is not appended.
8. No `action_finished` event is emitted.
9. `Timeline.end_turn` is not reached even if `ends_turn=True`.

The already emitted `action_started` remains in `BattleState.pending_events`.

## Required implementation

Prefer tests and documentation only. Do not change production behavior unless a test exposes a real contradiction with the accepted architecture and the change is separately justified.

### Direct production contract

Test exact insufficient-SP behavior with a caller-supplied `TurnContext`:

- exact exception type and message;
- SP unchanged;
- pending events exactly one `action_started` with exact actor/action provenance;
- no resource-change or action-finished event;
- `actions_taken` unchanged;
- `should_end_turn` reflects the action flag set before the failure;
- no end-turn event or successful completion state is synthesized.

### ARCH-012 contract

Through `execute_action_and_capture_pending_events`:

- the production `ValueError` propagates directly rather than being wrapped;
- downstream capture is not invoked after action failure;
- SP remains unchanged;
- the already emitted `action_started` remains in `pending_events`;
- no result/cursor advance is fabricated.

### ARCH-013 contract

For a failing first step:

- raise `MultiActionCaptureSessionFailure`;
- `failed_action_index == 0`;
- failed action id exact;
- `completed_results == ()`;
- `last_successful_cursor` equals the initial cursor;
- `__cause__` is the production insufficient-SP `ValueError` with exact message;
- state contains the uncaptured `action_started`;
- SP unchanged;
- later actions do not run.

For a failure after one successful step:

- preserve exactly one completed prior result;
- `last_successful_cursor` equals that result's `next_cursor`;
- failed action adds exactly one uncaptured `action_started` after the confirmed cursor boundary;
- failed action does not add `skill_points_changed` or `action_finished`;
- later actions do not run;
- the retained cursor is provenance only and is behind `len(state.pending_events)` by exactly one event in this controlled scenario.

## Acceptance criteria

- No simulator or runtime orchestration production code changed.
- Direct production insufficient-SP semantics are locked exactly.
- ARCH-012 direct exception propagation and capture-skipping are locked.
- ARCH-013 wrapper/cause/provenance semantics are locked for first-step and later-step failure.
- No failed action is represented as a successful capture result, stitched artifact, or Golden replay.
- Successful ARCH-027/028 behavior remains unchanged.
- Standalone runtime regression remains `5/5`.
- Legacy regression remains `20/20`.
- Trace evidence remains `2/2`.
- Production LIFO remains `third, second, first`.

## Required tests

Add focused tests for:

1. direct production failure partial state;
2. ARCH-012 failure propagation and capture skip;
3. ARCH-013 first-step failure provenance;
4. ARCH-013 failure after one completed step;
5. no downstream successful capture/stitch/Golden representation from the failed step;
6. regression and LIFO preservation.

## Must remain unchanged

- `hsr_axis_sim/sim/**`;
- `hsr_axis_sim/runtime_action_captures/**`;
- `hsr_axis_sim/runtime_action_sessions/**`;
- runtime adapters/trace schema/loaders/exporters/comparators/divergence/Golden validators;
- both regression manifests;
- all reviewed static fixture bytes;
- AV/timeline/extra-turn implementation.

## Explicit exclusions

- insufficient Energy failure behavior;
- changing resource validation rules;
- rollback/retry/transaction semantics;
- a failed-action Golden artifact;
- manifest schema evolution;
- generic failure DSL;
- AV/speed/advance/delay/immediate-action observation;
- character/release-game data;
- video automation;
- FIFO/LIFO changes.

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
