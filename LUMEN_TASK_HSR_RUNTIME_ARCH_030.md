# HSR-RUNTIME-ARCH-030 — Insufficient Energy Action Failure Contract

## Current confirmed state

- HSR-RUNTIME-ARCH-029 — PASS — proceed.
- Accepted main merge commit before this task: `88e3f5d71ab5cdbe7182338fed2ed64d4434deda`.
- Last confirmed validation:
  - `1309 passed`;
  - legacy regression `20/20`;
  - trace evidence `2/2`;
  - standalone runtime action-session Golden regression `5/5`.
- Successful `ConsumeEnergy` is already locked by ARCH-025 and promoted by ARCH-026.
- ARCH-029 independently locked insufficient Skill-Point failure semantics.

## Execution recommendation

- ChatGPT model: GPT-5.6 Sol.
- Codex reasoning: High if Codex is used.

## Objective

Independently lock the existing production failure semantics when `ConsumeEnergy` requires more Energy than the resolved target Unit has available. Validate the exact unit-scoped partial action state through direct production execution, ARCH-012, ARCH-013, and ARCH-016 without changing production behavior.

This is a failure-contract milestone, not a Golden replay milestone.

## Controlled reference scenario

Use explicit contract-only values:

- actor `energy-failure-actor`;
- target Unit `energy-failure-target`;
- team `ally`;
- base speed `100`;
- initial Energy `10`;
- max Energy `100`;
- effect `ConsumeEnergy(target_ids=["energy-failure-target"], amount=20)`.

Exact expected production exception:

`ValueError("Unit 'energy-failure-target' has insufficient energy: 10 available, 20 required.")`.

## Required implementation

Prefer tests and documentation only. Do not modify simulator/runtime orchestration unless a real contradiction with accepted architecture is proven.

### Direct production contract

Lock that:

- target resolution succeeds before the resource check;
- `Action.execute` has already set `turn_context.should_end_turn` and emitted `action_started`;
- the exact Unit-scoped `ValueError` is raised;
- target Energy remains exactly `10`;
- no `energy_changed` event is emitted;
- `actions_taken` is not appended;
- no `action_finished` or `turn_ended` event is emitted;
- no end-turn completion occurs.

### ARCH-012 contract

Lock that:

- the production Energy `ValueError` propagates directly;
- capture is never invoked after the action failure;
- target Energy remains unchanged;
- the failed action's `action_started` remains pending;
- no result/cursor advance is fabricated.

### ARCH-013 contract

Lock both first-step and later-step failure:

- controlled `MultiActionCaptureSessionFailure` wrapper;
- exact failed index/action ID;
- production `ValueError` preserved as `__cause__`;
- only fully completed prior results retained;
- `last_successful_cursor` remains the prior confirmed boundary;
- failed `action_started` remains uncaptured beyond that boundary;
- later actions do not execute.

### ARCH-016 contract

Lock that a failed Energy session stops before session stitching and Golden validation. No failed-action successful trace/Golden result may be synthesized.

## Acceptance criteria

- Tests/docs only; no production code changed.
- Exact unit-scoped exception text locked.
- Target Energy remains unchanged on failure.
- Partial event boundary is exactly `action_started` only for the failed action.
- ARCH-012 direct propagation/capture skip locked.
- ARCH-013 cause/provenance semantics locked for first and later failure.
- ARCH-016 stitch/Golden short-circuit locked.
- Successful runtime regression remains `5/5`.
- Legacy regression remains `20/20`.
- Trace evidence remains `2/2`.
- Production LIFO remains `third, second, first`.

## Required tests

Add focused tests for:

1. direct production Unit-scoped failure;
2. ARCH-012 propagation and capture skip;
3. ARCH-013 first-step failure;
4. ARCH-013 later-step failure after one completed action;
5. ARCH-016 downstream stitch/Golden not called;
6. successful regression/LIFO preservation.

## Must remain unchanged

- `hsr_axis_sim/sim/**`;
- `runtime_action_captures/**`;
- `runtime_action_sessions/**`;
- runtime adapters/trace schema/loaders/exporters/comparators/divergence/Golden validators;
- both regression manifests;
- all reviewed static fixtures;
- AV/timeline/extra-turn implementation.

## Explicit exclusions

- changing insufficient Skill-Point behavior;
- generic resource-failure abstraction;
- rollback/retry/resume semantics;
- failed-action Golden artifact;
- manifest schema evolution;
- Energy formula/cap changes;
- HSR release-game assumptions;
- AV/speed/advance/delay/immediate-action observation;
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
