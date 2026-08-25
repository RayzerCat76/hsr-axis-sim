# HSR-RUNTIME-ARCH-030 — Insufficient Energy Action Failure Contract

## Status

PASS — proceed

## Implementation summary

- Independently locked the existing production failure semantics for `ConsumeEnergy` when the resolved target Unit has less Energy than requested.
- This milestone is tests/docs only; no simulator or runtime orchestration production code was changed.
- Controlled reference scenario:
  - actor `energy-failure-actor`;
  - action `insufficient-energy-action`;
  - target Unit `energy-failure-target`;
  - target Energy `10 / 100`;
  - `ConsumeEnergy(target_ids=["energy-failure-target"], amount=20)`.
- Exact production exception:
  - `ValueError("Unit 'energy-failure-target' has insufficient energy: 10 available, 20 required.")`.
- Direct production partial state is locked:
  - target resolution succeeds;
  - `Action.execute` sets `TurnContext.should_end_turn` from the action flag and emits `action_started` before effect execution;
  - target Energy remains exactly `10`;
  - no `energy_changed` event is emitted;
  - `TurnContext.actions_taken` remains unchanged;
  - no `action_finished` or `turn_ended` event is emitted;
  - end-turn completion is not reached.
- ARCH-012 behavior is locked:
  - the Unit-scoped production `ValueError` propagates directly;
  - pending-event capture is never invoked after failure;
  - target Energy remains unchanged;
  - `action_started` remains pending;
  - no result/cursor advance is fabricated.
- ARCH-013 behavior is locked for both first-step and later-step failure:
  - `MultiActionCaptureSessionFailure` reports exact failed index/action ID;
  - the production Energy `ValueError` is preserved as `__cause__`;
  - only fully completed prior results are retained;
  - `last_successful_cursor` remains the last confirmed boundary;
  - the failed Energy action's `action_started` remains uncaptured beyond that boundary;
  - later actions do not execute.
- ARCH-016 end-to-end behavior is locked:
  - session failure propagates before a complete successful session exists;
  - session stitching is not invoked;
  - Golden validation is not invoked;
  - no failed Energy action is represented as a successful trace artifact or Golden result.
- Successful runtime resource regression remains `5/5`.

## Files added

- `LUMEN_TASK_HSR_RUNTIME_ARCH_030.md`
- `docs/runtime/INSUFFICIENT_ENERGY_FAILURE_CONTRACT_V1.md`
- `hsr_axis_sim/tests/test_runtime_arch_030_insufficient_energy_failure_contract.py`

## Files modified

- `hsr_axis_sim/LUMEN_RESULT.md`

No `sim/**`, `runtime_action_captures/**`, `runtime_action_sessions/**`, runtime adapter, trace schema/contract, loader/exporter/comparator/divergence implementation, Golden validator, regression manifest, reviewed static fixture, AV/timeline, or extra-turn/LIFO implementation was modified.

## Tests added

ARCH-030 focused coverage proves:

- exact Unit-scoped production exception type/message;
- target Unit identity and Energy `10/100` remain unchanged;
- exact failed `action_started` actor/action provenance;
- absence of `energy_changed`, `action_finished`, and `turn_ended`;
- `actions_taken` remains empty;
- `should_end_turn` was assigned before the failure;
- ARCH-012 direct propagation and capture skip;
- ARCH-012 request cursor remains at the original confirmed boundary;
- ARCH-013 first-step failure wrapper/cause/initial-cursor provenance;
- ARCH-013 later-step failure preserves exactly one completed prior result and leaves exactly one failed-action event beyond the confirmed cursor;
- later actions do not run after failure;
- ARCH-016 stops before stitch and Golden validation;
- legacy regression remains `20/20`;
- trace evidence remains `2/2`;
- successful runtime action-session Golden regression remains `5/5`;
- production LIFO remains `third, second, first`.

## Exact validation commands and real results

### Initial validated PR CI

GitHub Actions workflow `HSR Axis Sim Validation`, PR #35, run #155, job `validate` (`97657933977`).

1. `python -m compileall -q hsr_axis_sim`
   - PASS.
2. `python -m pytest -q`
   - PASS: `1315 passed in 6.96s`.
3. `python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --format text`
   - PASS legacy locked regression `20/20`:
     - 12/12 golden replays;
     - 2/2 manual checks;
     - 2/2 search scenarios;
     - 2/2 action-sequence trace checks;
     - 2/2 trace-evidence checks.
4. `python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --only trace_evidence --format text`
   - PASS `2/2` trace-evidence checks.
5. `python -m hsr_axis_sim.runtime_action_session_regression.runner --manifest hsr_axis_sim/data/runtime_action_session_regression_manifest.json --format text`
   - PASS `5/5` successful runtime action-session Golden regression with record counts `4,3,3,3,3`.

The first ARCH-030 PR CI was green; no implementation correction was required.

## Warnings / errors

- No compile, Unit-target failure observation, ARCH-012, ARCH-013, ARCH-016, legacy-regression, trace-evidence, or runtime-regression error was observed.
- Existing GitHub Actions Node 20 deprecation warning remains nonblocking and unrelated to ARCH-030 correctness.

## Acceptance review

- The Energy failure contract is independently documented and tested rather than inferred from the Skill-Point failure path.
- Target resolution succeeds before the insufficient-Energy check; the exact target Unit is named in the production exception.
- Failure occurs after action start but before any Energy mutation or successful action completion.
- The failed action leaves one uncaptured `action_started`; retained session cursors remain confirmed provenance only and are not retry instructions.
- ARCH-012/013/016 existing non-transactional semantics remain unchanged.
- No failed-action Golden artifact, generic resource-failure abstraction, rollback, retry, resume, or manifest schema was introduced.
- Successful ARCH-025/026 Energy consume behavior remains unchanged.
- No hidden HSR/release-game value was inferred; Energy `10/100` and request `20` are explicit contract-only inputs.
- Production LIFO compatibility remains unchanged.

## Unresolved issues

None blocking HSR-RUNTIME-ARCH-030 acceptance.

Both currently supported consumption resources now have independently locked insufficient-resource failure contracts. A generic failure abstraction is still intentionally absent because it is not needed for correctness.

The next major runtime observability gap is action-axis mutation: `AdvanceAction`, `DelayAction`, `ChangeSpeed`, `ImmediateAction`, and `GrantExtraTurn` mutate deterministic simulator state but do not yet emit equivalent typed runtime observation events.

## Suggested next milestone

`HSR-RUNTIME-ARCH-031 — Advance Action Runtime Observation Contract`

ARCH-031 should inspect the existing `AdvanceAction` production mutation and accepted runtime event schema/adapter boundaries, then add the smallest deterministic observation needed to make one explicit action-advance transition traceable. It must lock before/after AV, requested advance input, target Unit provenance, and clamping to zero without changing the underlying advance formula. Keep Delay, ChangeSpeed, ImmediateAction, and extra-turn observation separate until AdvanceAction is accepted.
