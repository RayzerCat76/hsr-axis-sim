# Multi-Action Capture Session V1

## Purpose

HSR-RUNTIME-ARCH-013 composes repeated accepted ARCH-012 single-action capture calls into one explicit caller-controlled ordered session.

The session does not select turns or actions. The caller owns the action sequence, optional production `TurnContext` objects, initial capture cursor, common legacy adapter policy, and every segment trace export configuration.

## Input contract

The caller supplies:

- one existing `BattleState`;
- a non-empty tuple of `ExplicitActionCaptureStep` values;
- one `MultiActionCaptureSessionConfig` containing:
  - initial caller-owned `PendingEventCaptureCursor`;
  - one accepted `LegacyEventAdapterConfig` common to the whole session;
  - one `TraceExportConfig` per declared action step, in exact tuple order;
  - one explicit segment artifact `pretty` flag.

The number of export configs must exactly equal the number of action steps before any production action is executed.

Each `ExplicitActionCaptureStep` contains:

- one caller-supplied production `Action`;
- optionally one caller-supplied production `TurnContext`.

The session never calls `Timeline.next_turn` and never derives or generates an action.

## Execution order

For each step in declared tuple order:

```text
current caller-owned cursor
+ common LegacyEventAdapterConfig
+ current cursor.next_runtime_sequence
+ caller-declared per-step TraceExportConfig
+ session pretty flag
-> LegacyEventTraceBridgeConfig
-> SingleActionEventCaptureRequest
-> accepted ARCH-012 execute_action_and_capture_pending_events
-> completed SingleActionEventCaptureResult
-> advance current cursor only to result.next_cursor
```

No sorting, reordering, cursor repair, sequence renumbering, action generation, or direct event capture is performed by the session layer.

## Successful result

`MultiActionCaptureSessionResult` is a frozen shell preserving:

- exact session config;
- exact declared step tuple;
- exact ordered tuple of completed ARCH-012 results;
- final caller-visible cursor.

Validation requires:

- one completed result per declared step;
- each result action/actor identity matches its step;
- first result starts at `initial_cursor`;
- every later result starts at the preceding result's `next_cursor`;
- one common adapter config is preserved;
- each result uses exactly its declared per-step export config;
- one common `pretty` flag is preserved;
- any explicitly supplied `TurnContext` is preserved by object identity;
- final cursor equals the final completed result's `next_cursor`.

The shell is frozen; nested production `Action` and `TurnContext` objects retain their existing simulator mutability semantics.

## Failure contract

ARCH-013 remains explicitly **non-transactional** because each ARCH-012 call may mutate simulator state before failure.

At the first failing step:

- execution stops immediately;
- no later action is executed;
- no successful session result is returned;
- the original exception is chained as `__cause__` of `MultiActionCaptureSessionFailure`;
- no rollback, retry, queue cleanup, or synthetic capture/cursor result is attempted.

`MultiActionCaptureSessionFailure` preserves:

- `failed_action_index`;
- `failed_action_id`;
- exact tuple of completed ARCH-012 results before the failed step;
- `last_successful_cursor`, equal to the last confirmed completed result cursor, or the initial cursor when the first step fails.

### Critical recovery limitation

`last_successful_cursor` is **not a guaranteed resumable or retry-safe cursor**.

A failed production action may already have mutated state or appended one or more events after that cursor. A production action may also complete successfully and then fail during downstream event adaptation/capture, leaving the entire action mutation and emitted-event window uncaptured.

Therefore the failure object records confirmed provenance only. It does not infer recovery, rollback, queue identity, or safe retry semantics.

## TurnContext ownership

The session does not automatically carry one turn context into later actions.

If multiple non-ending actions are intended to share one production `TurnContext`, the caller must explicitly place that same object in each corresponding step. ARCH-013 preserves that object identity and lets existing `Action.execute` semantics update it normally.

## Non-goals

ARCH-013 does not:

- call `Timeline.next_turn`;
- choose or generate actions;
- execute replay files;
- add simulator hooks;
- modify `sim/**`;
- drain or clear pending events;
- rollback or retry failed actions;
- stitch session segments;
- perform Golden Replay validation;
- write artifacts to files;
- change event mappings or runtime schemas;
- change HSR mechanics or production LIFO behavior.

## Next boundary

A later milestone may consume a fully successful ARCH-013 session result and compose its completed ARCH-012/ARCH-009 segments through accepted ARCH-010 stitching and ARCH-011 Golden validation. That composition must remain separate from session execution so failed state-mutating sessions cannot be mistaken for complete deterministic actual traces.
