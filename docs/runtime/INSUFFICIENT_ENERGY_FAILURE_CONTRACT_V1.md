# Insufficient Energy Action Failure Contract v1

## Purpose

This document locks the existing deterministic failure boundary for production `ConsumeEnergy` when the resolved target Unit has less Energy than the requested amount.

It is intentionally independent from the Skill-Point failure contract because Energy is Unit-scoped and target resolution is part of the production path.

## Controlled reference scenario

The contract uses:

- actor `energy-failure-actor`;
- target Unit `energy-failure-target`;
- team `ally`;
- base speed `100`;
- Energy `10 / 100`;
- `ConsumeEnergy(target_ids=["energy-failure-target"], amount=20)`.

The exact production exception is:

```text
Unit 'energy-failure-target' has insufficient energy: 10 available, 20 required.
```

## Production boundary

`Action.execute` sets the action's turn-ending intent and emits `action_started` before applying effects. `ConsumeEnergy` then resolves its Unit target and checks available Energy before mutation.

When the resolved target has only `10` Energy and `20` is requested:

- target resolution has succeeded;
- `action_started` is already pending;
- the exact Unit-scoped `ValueError` is raised;
- target Energy remains `10`;
- no `energy_changed` event is emitted;
- `TurnContext.actions_taken` is not appended;
- no `action_finished` event is emitted;
- no turn-end completion is reached.

The failure is therefore non-transactional but occurs before any Energy mutation.

## ARCH-012

`execute_action_and_capture_pending_events` invokes production `Action.execute` before pending-event capture. On insufficient Energy:

- the production `ValueError` propagates directly;
- downstream capture is not called;
- no capture result is produced;
- the request cursor is not advanced or repaired;
- target Energy remains unchanged;
- the already emitted `action_started` remains in `pending_events`.

## ARCH-013

`run_multi_action_capture_session` wraps the failed step in `MultiActionCaptureSessionFailure` and chains the production Energy exception as `__cause__`.

For a first-step failure:

- `failed_action_index == 0`;
- `completed_results == ()`;
- `last_successful_cursor` remains the initial cursor;
- the failed action's `action_started` exists beyond that confirmed boundary;
- later actions do not run.

After one completed action:

- exactly one completed result is preserved;
- `last_successful_cursor` equals that result's `next_cursor`;
- the failed Energy action appends one uncaptured `action_started`;
- no `energy_changed` or `action_finished` is appended for the failed action;
- later actions do not run.

The retained cursor is provenance only, not a safe retry/resume instruction.

## ARCH-016

`run_action_session_validation` cannot reach stitching or Golden validation until ARCH-013 returns a complete successful session result. Therefore insufficient Energy:

- propagates as `MultiActionCaptureSessionFailure` from the session boundary;
- prevents session stitching;
- prevents Golden validation;
- never creates a successful artifact for the failed action.

## Explicit exclusions

This contract does not define or change:

- insufficient Skill-Point behavior;
- rollback, transaction, retry, or resume semantics;
- a generic resource-failure abstraction;
- a failed-action Golden artifact;
- Energy caps/formulas;
- target-selection rules beyond the explicit target ID used here;
- HSR release-game values;
- regression manifest grammar;
- production LIFO behavior.

Successful Energy consumption remains governed by ARCH-025 and ARCH-026.
