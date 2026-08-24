# Successful Session Golden Validation Handoff v1

## Scope

HSR-RUNTIME-ARCH-015 adds one read-only composition boundary from a completed successful ARCH-014 session-stitch result into the accepted ARCH-011 stitched-actual Golden validation handoff.

This layer does not execute simulator actions, create captures, stitch traces, serialize actual traces, load trace files, compare records, compute first divergence, or choose replay/turn/action behavior.

## Input

`validate_successful_session_against_golden` accepts:

- one completed `SuccessfulSessionTraceStitchResult` from ARCH-014;
- caller-supplied expected Golden trace bytes;
- one accepted `GoldenReplayValidationConfig`.

A controlled ARCH-013 partial-session failure is not a valid input because it is not a completed ARCH-014 result.

## Exact handoff rule

The only actual-trace object passed downstream is:

```text
session_stitch_result.stitch_result
```

That exact Python object is passed once to accepted ARCH-011:

```text
validate_stitched_actual_against_golden(
    session_stitch_result.stitch_result,
    expected_payload_bytes,
    config=config,
)
```

ARCH-015 does not:

- call ARCH-010 again;
- rebuild or reserialize the actual artifact;
- extract and reload payload bytes itself;
- call the lower Golden Replay validator directly;
- call loader/comparator/divergence functions directly;
- reorder or repair records/events.

## Result

`SuccessfulSessionGoldenValidationResult` is frozen and preserves:

- the complete ARCH-014 `SuccessfulSessionTraceStitchResult`;
- the complete accepted ARCH-011 `StitchedActualGoldenValidationResult`.

Construction requires:

```text
validation_result.stitch_result
is session_stitch_result.stitch_result
```

Equal-looking reconstructed stitch results are rejected because provenance identity, not structural equality alone, is authoritative at this boundary.

## Mismatch and operational failures

A Golden Replay mismatch remains a completed ARCH-011/HSR-AXIS-001B validation result with accepted comparison and first-divergence provenance. ARCH-015 does not convert mismatch into an exception.

Input or operational failures from ARCH-011 propagate unchanged. ARCH-015 does not retry, repair, or synthesize partial success.

## Determinism and provenance

The successful action-session path is therefore:

```text
caller-declared actions
-> ARCH-013 successful capture session
-> ARCH-014 exact capture-object stitch handoff
-> accepted ARCH-010 deterministic stitched actual artifact
-> ARCH-015 exact stitch-object Golden handoff
-> accepted ARCH-011 exact-byte validation handoff
-> accepted Golden PASS / first divergence
```

Every new boundary preserves the previously accepted object identity rather than reconstructing an equivalent replacement.

## Exclusions

ARCH-015 does not authorize:

- automatic turn/action selection;
- replay execution;
- simulator hooks;
- rollback or retry;
- file I/O;
- trace stitching;
- actual trace reserialization;
- direct Golden loader/comparator/divergence implementation;
- schema or event-map changes;
- new HSR mechanics;
- FIFO/LIFO changes.
