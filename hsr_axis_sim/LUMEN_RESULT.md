# HSR-RUNTIME-ARCH-029 — Insufficient Skill-Point Action Failure Contract

## Status

PASS — proceed

## Implementation summary

- Locked the existing production failure semantics for `ConsumeSkillPoint` when requested Skill Points exceed the team's available Skill Points.
- This milestone is tests/docs only; no simulator or runtime orchestration production code was changed.
- Controlled reference scenario:
  - actor `sp-failure-actor`;
  - action `insufficient-sp-action`;
  - initial team SP `1`, max SP `5`;
  - `ConsumeSkillPoint(amount=2)`.
- Exact production exception:
  - `ValueError("Insufficient skill points: 1 available, 2 required.")`.
- Direct production partial state is now locked:
  - `Action.execute` sets `TurnContext.should_end_turn` from the action flag before effect execution;
  - exactly one `action_started` event is emitted with exact actor/action provenance;
  - team SP remains `1`;
  - no `skill_points_changed` event is emitted;
  - `TurnContext.actions_taken` remains unchanged;
  - no `action_finished` or `turn_ended` event is emitted;
  - `Timeline.end_turn` is not reached.
- ARCH-012 behavior is locked:
  - the production `ValueError` propagates directly;
  - pending-event capture is never invoked after the action exception;
  - the already emitted `action_started` remains;
  - no result or cursor advance is fabricated.
- ARCH-013 first-step failure behavior is locked:
  - `MultiActionCaptureSessionFailure` at index `0`;
  - exact failed action ID;
  - `completed_results == ()`;
  - `last_successful_cursor` remains the initial cursor;
  - the production `ValueError` is preserved as `__cause__`;
  - later actions are not executed.
- ARCH-013 later-step failure behavior is locked:
  - one completed prior result is retained;
  - `last_successful_cursor` equals that result's `next_cursor`;
  - the insufficient-SP action appends exactly one uncaptured `action_started` after the confirmed boundary;
  - in the controlled scenario `len(state.pending_events) == last_successful_cursor.pending_event_index + 1`;
  - later actions are not executed.
- ARCH-016 end-to-end behavior is locked:
  - session failure propagates before a successful session result exists;
  - session stitching is not invoked;
  - Golden validation is not invoked;
  - no failed action is synthesized into a successful trace artifact or Golden result.
- Successful resource regression remains `5/5`.

## Files added

- `LUMEN_TASK_HSR_RUNTIME_ARCH_029.md`
- `docs/runtime/INSUFFICIENT_SKILL_POINT_FAILURE_CONTRACT_V1.md`
- `hsr_axis_sim/tests/test_runtime_arch_029_insufficient_skill_point_failure_contract.py`

## Files modified

- `hsr_axis_sim/LUMEN_RESULT.md`

No `sim/**`, `runtime_action_captures/**`, `runtime_action_sessions/**`, runtime adapter, trace schema/contract, loader/exporter/comparator/divergence implementation, Golden validator, regression manifest, reviewed static fixture, AV/timeline, or extra-turn/LIFO implementation was modified.

## Tests added

ARCH-029 focused coverage proves:

- exact direct production exception type/message;
- exact direct partial state with SP unchanged;
- exact `action_started` actor/action provenance;
- absence of `skill_points_changed`, `action_finished`, and `turn_ended`;
- `actions_taken` remains empty;
- `should_end_turn` was assigned before the failure;
- ARCH-012 direct propagation of the production `ValueError`;
- ARCH-012 capture helper is never called after the action failure;
- ARCH-012 request cursor remains the original confirmed boundary;
- ARCH-013 first-step failure wrapper, exact cause, empty completed results, and initial-cursor provenance;
- ARCH-013 failure after one successful action preserves exactly one completed result and leaves exactly one failed-action event beyond the confirmed cursor;
- later declared session actions do not run after failure;
- ARCH-016 stops before stitch and Golden validation;
- legacy regression remains `20/20`;
- trace evidence remains `2/2`;
- standalone successful runtime Golden regression remains `5/5`;
- production LIFO remains `third, second, first`.

## Exact validation commands and real results

### Initial validated PR CI

GitHub Actions workflow `HSR Axis Sim Validation`, PR #34, run #152, job `validate` (`97657216366`).

1. `python -m compileall -q hsr_axis_sim`
   - PASS.
2. `python -m pytest -q`
   - PASS: `1309 passed in 7.18s`.
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

The first ARCH-029 PR CI was green; no implementation correction was required.

## Warnings / errors

- No compile, production-failure observation, ARCH-012, ARCH-013, ARCH-016, legacy-regression, trace-evidence, or runtime-regression error was observed.
- Existing GitHub Actions Node 20 deprecation warning remains nonblocking and unrelated to ARCH-029 correctness.

## Acceptance review

- The failure contract documents and tests the existing non-transactional behavior without modifying it.
- The insufficient-SP exception occurs after action start but before any SP mutation or successful action completion.
- The failed action leaves one observable uncaptured `action_started`; therefore a failed-session cursor is confirmed provenance only and must not be treated as the live end of `pending_events` or as automatically retry-safe.
- ARCH-012 and ARCH-013 existing failure semantics remain unchanged and are now locked with a real production resource failure.
- ARCH-016 cannot create a stitch or Golden result from this failed action path.
- No failed-action Golden artifact, failure manifest schema, rollback, retry, or generic failure DSL was introduced.
- Successful ARCH-027/028 Skill-Point consume behavior remains unchanged.
- No hidden HSR/release-game value was inferred; SP `1`, max `5`, and requested `2` are explicit contract-only test inputs.
- Production LIFO compatibility remains unchanged.

## Unresolved issues

None blocking HSR-RUNTIME-ARCH-029 acceptance.

Insufficient Energy has a structurally similar production check, but it remains intentionally separate until its exact unit-targeted failure provenance is independently reviewed and locked.

Failed-session resumption/recovery remains deliberately undefined. The current cursor is provenance only, not a retry instruction.

## Suggested next milestone

`HSR-RUNTIME-ARCH-030 — Insufficient Energy Action Failure Contract`

ARCH-030 should independently lock the production `ConsumeEnergy` insufficient-resource failure path using one explicit Unit target. Confirm the exact unit-scoped exception text, unchanged Energy, `action_started` partial event, absence of `energy_changed`/`action_finished`, ARCH-012 direct propagation, ARCH-013 cause/provenance behavior, and ARCH-016 stitch/Golden short-circuit. Do not merge the SP and Energy failure paths into a generic failure abstraction unless a later task explicitly justifies it.
