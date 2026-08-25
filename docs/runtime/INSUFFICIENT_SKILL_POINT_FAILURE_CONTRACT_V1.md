# Insufficient Skill-Point Action Failure Contract v1

## Purpose

This document locks the existing deterministic failure boundary for production `ConsumeSkillPoint` when the requested amount exceeds the team's available Skill Points.

It describes observed repository behavior only. It does not claim any additional Honkai: Star Rail release-game rule and does not introduce rollback, retry, or failed-action Golden semantics.

## Controlled reference scenario

The contract tests use:

- actor: `sp-failure-actor`;
- action: `insufficient-sp-action`;
- initial team Skill Points: `1`;
- max Skill Points: `5`;
- effect: `ConsumeSkillPoint(amount=2)`.

The exact production exception is:

```text
Insufficient skill points: 1 available, 2 required.
```

## Production `Action.execute` boundary

`Action.execute` performs these relevant operations in order:

1. create or validate the `TurnContext`;
2. set `turn_context.should_end_turn = action.ends_turn`;
3. emit `action_started`;
4. apply effects in declared order;
5. only after all effects succeed, append the action ID to `actions_taken`;
6. emit `action_finished`;
7. if required, run `Timeline.end_turn`.

`ConsumeSkillPoint` checks availability before modifying Skill Points. If available SP is below `amount`, it raises immediately.

Therefore the controlled failure leaves this exact partial state:

- team Skill Points remain `1`;
- one `action_started` event remains in `BattleState.pending_events`;
- that event retains the failing actor/action provenance;
- no `skill_points_changed` event exists;
- no `action_finished` event exists;
- `TurnContext.actions_taken` is not appended;
- `TurnContext.should_end_turn` has already been assigned from the action flag;
- `Timeline.end_turn` is not reached, even when `ends_turn=True`.

This is intentionally not a zero-side-effect failure. The action-start boundary is observable before resource validation fails.

## ARCH-012 single-action capture behavior

`execute_action_and_capture_pending_events` calls production `Action.execute` before any pending-event capture.

When insufficient SP raises:

- the production `ValueError` propagates directly;
- no ARCH-012 result object is produced;
- downstream capture is not called;
- no cursor advance is fabricated;
- the already emitted `action_started` remains in `pending_events`;
- team SP remains unchanged.

ARCH-012 is non-transactional. It does not remove the partial event or roll back any mutation that occurred before the exception.

## ARCH-013 multi-action session behavior

`run_multi_action_capture_session` wraps a failing step in `MultiActionCaptureSessionFailure` and chains the production exception as `__cause__`.

### Failure on the first step

The failure records:

- `failed_action_index == 0`;
- the exact failing action ID;
- `completed_results == ()`;
- `last_successful_cursor == initial_cursor`.

The state nevertheless contains the failed action's uncaptured `action_started`. The retained cursor is a confirmed boundary, not the current end of `pending_events`.

### Failure after a completed step

If one effect-free action completed first:

- its completed capture result is preserved exactly;
- `last_successful_cursor` equals that result's `next_cursor`;
- the next insufficient-SP action appends one uncaptured `action_started` and then fails;
- the cursor remains at the prior confirmed boundary;
- in the controlled scenario, `len(state.pending_events)` is therefore exactly one greater than `last_successful_cursor.pending_event_index`;
- later declared actions are not executed.

A cursor retained by a failed session is provenance only. It must not be treated as automatically resumable or retry-safe.

## ARCH-016 end-to-end validation behavior

`run_action_session_validation` first runs ARCH-013. Stitching and Golden validation occur only after a complete successful session result exists.

For insufficient SP:

- ARCH-013 raises before a successful session result exists;
- the `MultiActionCaptureSessionFailure` propagates from the end-to-end boundary;
- session stitching is not called;
- Golden validation is not called;
- no successful trace artifact or Golden result is synthesized for the failed action.

## What this contract does not do

This contract does not define:

- a failed-action Golden file;
- rollback or transaction semantics;
- retry behavior;
- failure resumption from `last_successful_cursor`;
- insufficient Energy behavior;
- generic resource-failure schema;
- any HSR-specific SP cap or release-game resource rule beyond explicit test inputs.

Successful Skill-Point consume remains governed by the accepted ARCH-027 reviewed static fixture and ARCH-028 regression promotion.
