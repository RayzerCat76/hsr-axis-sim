# Successful Session Trace Stitch Handoff V1

## Purpose

HSR-RUNTIME-ARCH-014 adds one read-only typed boundary from a fully successful ARCH-013 multi-action capture session to the accepted ARCH-010 deterministic captured-trace stitcher.

It does not execute actions and does not accept ARCH-013 failure provenance as a substitute for a complete session.

## Input contract

The caller supplies:

- one completed `MultiActionCaptureSessionResult`;
- one accepted `CapturedTraceStitchConfig` controlling final trace export identity, metadata, sequence policy, and pretty/compact serialization.

A `MultiActionCaptureSessionFailure` is not an accepted input type. Failed or partial state-mutating sessions are not complete deterministic actual traces.

## Handoff

The handoff extracts exactly:

```text
tuple(
    action_result.capture_result
    for action_result in session_result.results
)
```

Each extracted object is the already accepted ARCH-009 `PendingEventCursorCaptureResult` stored by the corresponding completed ARCH-012 result.

The tuple is passed exactly once, in existing session order, to:

```text
stitch_captured_trace_segments(segments, config=config)
```

The handoff does not:

- rebuild capture results;
- re-adapt legacy events;
- reconstruct RuntimeEvents;
- sort or realign segments;
- renumber sequences/event IDs;
- serialize intermediate copies;
- access simulator state.

All flattening, continuity validation, final trace export, canonical byte serialization, and SHA-256 identity remain owned by accepted ARCH-010/ARCH-003 semantics.

## Result contract

`SuccessfulSessionTraceStitchResult` is frozen and preserves:

- the complete successful ARCH-013 session result;
- the complete accepted ARCH-010 stitch result.

Construction requires every stitch segment to be the exact same Python object as the corresponding `action_result.capture_result` from the session, in the same order.

This identity requirement prevents a handoff wrapper from claiming session provenance over independently reconstructed or merely equal segment values.

## Errors

Invalid handoff input types are rejected before ARCH-010 is invoked.

Any accepted ARCH-010 stitching error propagates unchanged. ARCH-014 does not catch, wrap, repair, retry, or normalize stitch failures.

## Non-goals

ARCH-014 does not:

- execute production actions or sessions;
- inspect `BattleState`;
- call `Timeline.next_turn`;
- accept partial/failure session provenance;
- add simulator hooks;
- perform Golden Replay validation;
- write files;
- reimplement adaptation, capture, export, or stitch semantics;
- change event mappings/runtime schema;
- change HSR mechanics or production LIFO behavior.

## Next boundary

A later milestone may accept this completed successful session stitch wrapper and hand its exact existing ARCH-010 `CapturedTraceStitchResult` to accepted ARCH-011 Golden validation. That should remain a separate read-only composition layer so execution, stitching, and Golden comparison retain distinct provenance boundaries.
