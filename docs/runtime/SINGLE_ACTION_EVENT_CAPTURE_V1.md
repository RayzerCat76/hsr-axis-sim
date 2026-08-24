# Single-Action Event Capture V1

## Purpose

HSR-RUNTIME-ARCH-012 adds one explicit, non-transactional orchestration boundary around the existing production `Action.execute` API and accepted ARCH-009 pending-event cursor capture.

It exists to capture the exact legacy events appended by one caller-selected action without changing production simulator code or event semantics.

## Input contract

The caller supplies:

- one existing `BattleState`;
- one existing production `Action`;
- one `SingleActionEventCaptureRequest` containing:
  - caller-owned `PendingEventCaptureCursor`;
  - accepted `LegacyEventTraceBridgeConfig` whose `start_sequence` equals the cursor's `next_runtime_sequence`;
- optionally one existing `TurnContext`.

Before action execution, `cursor.pending_event_index` must equal the current `len(state.pending_events)` exactly. A cursor behind the list end is rejected rather than silently including pre-existing events. A cursor beyond the list end is also rejected by the same equality rule.

## Execution order

```text
validate explicit inputs
-> record pre-action pending-event count
-> require cursor index == pre-action list end
-> Action.execute(state, turn_context) exactly once
-> record post-action pending-event count
-> construct ARCH-009 capture request [pre:end)
-> capture_battle_state_pending_events_from_cursor
-> immutable orchestration result
```

The capture end is never guessed before action execution; it is the concrete list length after the successful production action call returns.

## Successful result

`SingleActionEventCaptureResult` preserves:

- exact caller request;
- action ID and actor ID;
- pre-action and post-action pending-event counts;
- the `TurnContext` returned by production `Action.execute`;
- the complete accepted ARCH-009 `PendingEventCursorCaptureResult`.

The result requires:

- pre-action count equals the caller cursor index;
- capture start equals that same cursor;
- capture end equals the post-action list count;
- captured event count equals `post - pre`;
- bridge configuration is unchanged;
- returned turn-context actor matches the action actor.

The dataclass shell is frozen. `TurnContext` remains the existing production mutable object and is not redefined or deep-frozen by this sidecar.

## Partial-failure semantics

This boundary is intentionally **not transactional**.

### Action execution failure

If `Action.execute` raises:

- the original exception propagates unchanged;
- no ARCH-009 capture call is attempted;
- any simulator state mutation or already-emitted events remain exactly as production execution left them;
- no result object is returned;
- the caller-owned cursor is not mutated or advanced.

### Post-action capture failure

If `Action.execute` succeeds but downstream ARCH-009/ARCH-008 adaptation or capture fails:

- that downstream exception propagates unchanged;
- the successful action's simulator mutation and emitted events remain in `BattleState`;
- no orchestration result is returned;
- no rollback, retry, repair, queue cleanup, or synthetic cursor advancement is attempted.

This distinction is mandatory because production action execution mutates state and is not currently transactional.

## Non-goals

ARCH-012 does not:

- call `Timeline.next_turn`;
- select or generate an action;
- execute a replay;
- modify `sim/**`;
- drain or clear `pending_events`;
- add simulator hooks;
- perform retries or rollback;
- stitch segments;
- perform Golden Replay validation;
- write trace files;
- change event mappings, runtime schema, HSR mechanics, or production LIFO behavior.

## Next boundary

A later milestone may compose repeated completed single-action captures into a higher-level caller-controlled execution session, but it must preserve ARCH-012's explicit non-transactional failure semantics and must not silently auto-select gameplay actions.
